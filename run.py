#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tự động chạy pipeline: prepare -> embed -> serve
Usage: python run.py [--source recipes.json] [--skip-prepare] [--skip-embed] [--port 8000]
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Chạy command và hiển thị kết quả"""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    print(f"🔧 Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"\n❌ Lỗi khi chạy: {description}")
        sys.exit(1)
    print(f"\n✅ Hoàn thành: {description}")
    return result

def main():
    parser = argparse.ArgumentParser(description="Chạy pipeline recipe chatbot")
    parser.add_argument("--source", default="recipes.json", help="File JSON nguồn hoặc API URL (mặc định: recipes.json)")
    parser.add_argument("--skip-prepare", action="store_true", help="Bỏ qua bước prepare (nếu docs.jsonl đã có)")
    parser.add_argument("--skip-embed", action="store_true", help="Bỏ qua bước embed (nếu index đã có)")
    parser.add_argument("--port", type=int, default=8000, help="Port cho API server (mặc định: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host cho API server (mặc định: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Bật auto-reload cho server")
    
    args = parser.parse_args()
    
    # Xác định Python interpreter
    venv_python = Path(".venv/Scripts/python.exe")
    if not venv_python.exists():
        venv_python = Path(".venv/bin/python")
    if not venv_python.exists():
        python_cmd = [sys.executable]
        print("⚠️  Không tìm thấy .venv, sử dụng Python hệ thống")
    else:
        python_cmd = [str(venv_python)]
        print(f"✅ Sử dụng Python từ venv: {venv_python}")
    
    # Bước 1: Prepare recipes
    if not args.skip_prepare:
        source_arg = args.source
        if not source_arg.startswith("api://") and not os.path.exists(source_arg):
            print(f"⚠️  File {source_arg} không tồn tại, bỏ qua bước prepare")
            args.skip_prepare = True
    
    if not args.skip_prepare:
        cmd = python_cmd + [
            "prepare_recipes.py",
            "--source", args.source,
            "--out", "docs.jsonl"
        ]
        run_command(cmd, "Bước 1: Chuẩn hóa recipes thành docs.jsonl")
    else:
        print("\n⏭️  Bỏ qua bước prepare (--skip-prepare)")
    
    # Bước 2: Embed và tạo index
    if not args.skip_embed:
        if not os.path.exists("docs.jsonl"):
            print("❌ File docs.jsonl không tồn tại. Chạy prepare trước!")
            sys.exit(1)
        
        cmd = python_cmd + [
            "embed_and_index.py",
            "--docs", "docs.jsonl",
            "--index", "out.index",
            "--meta", "meta.json"
        ]
        run_command(cmd, "Bước 2: Tạo embeddings và index")
    else:
        print("\n⏭️  Bỏ qua bước embed (--skip-embed)")
    
    # Bước 3: Chạy API server
    print(f"\n{'='*60}")
    print("🚀 Bước 3: Khởi động API server")
    print(f"{'='*60}")
    
    uvicorn_cmd = python_cmd + ["-m", "uvicorn", "serve_vector:app"]
    uvicorn_cmd.extend(["--host", args.host, "--port", str(args.port)])
    if args.reload:
        uvicorn_cmd.append("--reload")
    
    print(f"🔧 Command: {' '.join(uvicorn_cmd)}")
    print(f"\n📡 API sẽ chạy tại: http://{args.host}:{args.port}")
    print(f"📚 API docs: http://{args.host}:{args.port}/docs")
    print(f"\n⚠️  Nhấn Ctrl+C để dừng server\n")
    
    # Chạy server (blocking)
    try:
        subprocess.run(uvicorn_cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng server")

if __name__ == "__main__":
    main()

