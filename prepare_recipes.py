# Script: tải/chuẩn hoá recipes thành JSONL cho embedding / fine-tune
# Usage: python prepare_recipes.py --source recipes.json --out docs.jsonl

import json
import argparse
from datetime import datetime

def normalize_recipe(r):
    # unify fields: id, title, text (concat description + sections), metadata
    title = r.get("title") or r.get("name") or ""
    description = r.get("description") or r.get("notes") or ""
    detail = r.get("detail") or r.get("detail_block") or {}
    parts = [description]
    # instructions / steps
    instructions = detail.get("instructions") or detail.get("steps") or []
    for s in instructions:
        text = s.get("step") if isinstance(s, dict) else str(s)
        parts.append(text)
    # ingredients
    ing = detail.get("ingredients") or []
    for item in ing:
        if isinstance(item, dict):
            parts.append(item.get("main",""))
            parts.append(item.get("sauce",""))
        else:
            parts.append(str(item))
    text = "\n\n".join([p for p in parts if p])
    metadata = {
        "id": r.get("id"),
        "slug": r.get("slug"),
        "category": (r.get("category") or {}).get("name"),
        "created_at": r.get("created_at") or r.get("createdAt")
    }
    return {
        "id": r.get("id"),
        "title": title,
        "text": text,
        "metadata": metadata
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="input JSON file (array of recipes) or 'api://http://localhost:8080/recipes/full-details'")
    p.add_argument("--out", required=True, help="output JSONL file")
    args = p.parse_args()

    if args.source.startswith("api://"):
        import requests
        url = args.source[len("api://"):] 
        resp = requests.get(url)
        data = resp.json()
        items = data.get("data") or data
    else:
        with open(args.source, "r", encoding="utf-8") as f:
            items = json.load(f)

    # Handle both list and dict formats
    if isinstance(items, dict):
        recipe_list = items.get("data", [])
    else:
        recipe_list = items

    docs = [normalize_recipe(r) for r in recipe_list if r.get("title") or r.get("name")]
    with open(args.out, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Wrote {len(docs)} docs to {args.out}")

if __name__ == "__main__":
    main()
