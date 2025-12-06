# Usage: uvicorn serve_vector:app --reload --host 0.0.0.0 --port 8000
import os, json, requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = os.environ.get("VECTOR_INDEX_PATH", "out.index")
META_PATH = os.environ.get("VECTOR_META_PATH", "meta.json")
MODEL_NAME = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")

app = FastAPI()
print("Starting service...")

# lazy globals
index = None
meta = []
embed_model = None
llm_client = None

class QueryIn(BaseModel):
    q: str
    k: int = 5

class TrainIn(BaseModel):
    source_url: str
    index_path: Optional[str] = INDEX_PATH
    meta_path: Optional[str] = META_PATH
    model: Optional[str] = MODEL_NAME
    chunk_size: int = 1024
    chunk_overlap: int = 80

class ChatIn(BaseModel):
    input: str
    k: int = 3

# --- helpers ------------------------------------------------
def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def doc_to_text(item: dict) -> str:
    # Compose a single text blob from the provided recipe item
    parts = []
    title = item.get("title") or item.get("name") or ""
    parts.append(f"Title: {title}")
    detail = item.get("detail", {})
    if isinstance(detail, dict):
        # ingredients
        ing = detail.get("ingredients", [])
        if ing:
            parts.append("Ingredients:")
            for i in ing:
                # accept dicts or strings
                if isinstance(i, dict):
                    parts.append(" - " + " | ".join([v for v in i.values() if v]))
                else:
                    parts.append(f" - {i}")
        # steps
        steps = detail.get("steps", [])
        if steps:
            parts.append("Steps:")
            for s in steps:
                step_text = s.get("step") if isinstance(s, dict) else str(s)
                parts.append(f" - {step_text}")
        # other fields
        notes = detail.get("notes")
        if notes:
            parts.append("Notes: " + notes)
    # fallback text field
    if item.get("text"):
        parts.append(item.get("text"))
    return "\n".join(parts)

def simple_chunk_text(text, chunk_size=1024, overlap=80):
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        chunks.append(text[start:start+chunk_size])
        start += step
    return chunks

def get_embedder(model_name):
    global embed_model
    if embed_model:
        return embed_model
    # try FastEmbedEmbeddings first (if user installed something named that)
    try:
        from fastembed import FastEmbedEmbeddings
        embed_model = FastEmbedEmbeddings()
        print("Using FastEmbedEmbeddings")
        return embed_model
    except Exception:
        # fallback to sentence-transformers
        embed_model = SentenceTransformer(model_name)
        print("Using SentenceTransformer:", model_name)
        return embed_model

def encode_texts(texts, model_name):
    emb = get_embedder(model_name)
    if hasattr(emb, "encode") and callable(getattr(emb, "encode")):
        return emb.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    else:
        # placeholder if interface differs
        arr = [emb.embed(t) for t in texts]
        arr = np.array(arr, dtype=np.float32)
        # normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms==0] = 1.0
        return arr / norms

def save_index_and_meta(index_obj, meta_list, index_path, meta_path):
    faiss.write_index(index_obj, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

def load_index_and_meta(index_path=INDEX_PATH, meta_path=META_PATH):
    global index, meta
    if index is None:
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("Index or meta file not found. Train first.")
        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    return index, meta

def get_ollama_client():
    global llm_client
    if llm_client:
        return llm_client
    try:
        from ollama import Ollama
        llm_client = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
        return llm_client
    except Exception as e:
        raise RuntimeError("Ollama client unavailable. Install 'ollama' python package and ensure Ollama daemon is accessible.") from e

# --- endpoints ------------------------------------------------
@app.post("/train")
def train(body: TrainIn):
    """
    Fetch data from source_url, build chunks, embeddings and faiss index, save index+meta.
    """
    try:
        payload = fetch_json(body.source_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    items = payload.get("data") or []
    docs = []
    meta_list = []
    texts = []
    for item in items:
        text = doc_to_text(item)
        chunks = simple_chunk_text(text, chunk_size=body.chunk_size, overlap=body.chunk_overlap)
        for c in chunks:
            texts.append(c)
            meta_list.append({"id": item.get("id"), "title": item.get("title"), "text": c, "source": body.source_url})
    if not texts:
        raise HTTPException(status_code=400, detail="No documents found in source")
    embs = encode_texts(texts, body.model)
    # ensure float32
    embs = np.array(embs, dtype=np.float32)
    # normalize for cosine via inner product
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms==0] = 1.0
    embs = embs / norms
    dim = embs.shape[1]
    idx = faiss.IndexFlatIP(dim)
    idx.add(embs)
    save_index_and_meta(idx, meta_list, body.index_path, body.meta_path)
    # update in-memory
    global index, meta
    index = idx
    meta = meta_list
    return {"status": "ok", "indexed": len(texts), "index_path": body.index_path, "meta_path": body.meta_path}

@app.post("/search")
def search(body: QueryIn):
    q = body.q
    k = body.k
    try:
        idx, metas = load_index_and_meta()
        emb = encode_texts([q], MODEL_NAME)
        D, I = idx.search(emb, k)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search error: " + str(e))
    results = []
    for dist, ind in zip(D[0], I[0]):
        if ind < 0 or ind >= len(metas):
            continue
        m = metas[ind]
        results.append({"score": float(dist), "meta": m})
    return {"results": results}