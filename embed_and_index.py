# Usage: python embed_and_index.py --docs docs.jsonl --index out.index --meta meta.json
# REPLACED: safe import with diagnostic on failure
import argparse, json
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

def load_docs(path):
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs

# New: small helper to create text like serve_vector
def doc_to_text(item: dict) -> str:
    parts = []
    title = item.get("title") or ""
    parts.append(f"Title: {title}")
    detail = item.get("detail", {})
    if isinstance(detail, dict):
        ing = detail.get("ingredients", [])
        if ing:
            parts.append("Ingredients:")
            for i in ing:
                if isinstance(i, dict):
                    parts.append(" - " + " | ".join([v for v in i.values() if v]))
                else:
                    parts.append(f" - {i}")
        steps = detail.get("steps", [])
        if steps:
            parts.append("Steps:")
            for s in steps:
                step_text = s.get("step") if isinstance(s, dict) else str(s)
                parts.append(f" - {step_text}")
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

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--docs", required=True)
    p.add_argument("--index", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = p.parse_args()

    docs = load_docs(args.docs)
    texts = []
    meta = []
    for d in docs:
        txt = doc_to_text(d)
        chunks = simple_chunk_text(txt, 1024, 80)
        for c in chunks:
            texts.append(c)
            meta.append({"id": d.get("id"), "title": d.get("title"), "text": c})

    # try fast embed first
    try:
        from fastembed import FastEmbedEmbeddings
        emb_model = FastEmbedEmbeddings()
        embeddings = emb_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    except Exception:
        model = SentenceTransformer(args.model)
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype=np.float32))
    faiss.write_index(index, args.index)
    with open(args.meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Saved index {args.index} and metadata {args.meta}")

if __name__ == "__main__":
    main()
