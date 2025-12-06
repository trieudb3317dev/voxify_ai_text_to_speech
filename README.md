# Recipe Chatbot Agent

Hệ thống chatbot tìm kiếm công thức nấu ăn sử dụng vector search với FAISS và sentence transformers.

## 📋 Mô tả

Dự án này bao gồm:
- **prepare_recipes.py**: Chuẩn hóa dữ liệu recipes từ JSON hoặc API thành định dạng JSONL
- **embed_and_index.py**: Tạo embeddings và xây dựng FAISS index cho vector search
- **serve_vector.py**: FastAPI server cung cấp API để tìm kiếm và train

## 🚀 Cài đặt

### 1. Tạo virtual environment

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Hoặc nếu gặp lỗi execution policy:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
. .venv\Scripts\Activate.ps1
```

```bash
# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

**Lưu ý**: Trên Windows, `faiss-cpu` sẽ được cài tự động. Nếu gặp lỗi, cài thủ công:
```bash
pip install faiss-cpu
```

## 📖 Cách sử dụng

### Cách 1: Chạy tự động với script (Khuyến nghị)

#### Windows PowerShell:
```powershell
# Chạy đầy đủ pipeline (prepare -> embed -> serve)
.\run.ps1

# Hoặc với các tùy chọn:
.\run.ps1 -Source recipes.json -Port 8000 -Reload

# Bỏ qua các bước đã chạy:
.\run.ps1 -SkipPrepare -SkipEmbed  # Chỉ chạy server
.\run.ps1 -SkipEmbed  # Chạy prepare và server
```

#### Python (Cross-platform):
```bash
# Chạy đầy đủ pipeline
python run.py

# Hoặc với các tùy chọn:
python run.py --source recipes.json --port 8000 --reload

# Bỏ qua các bước đã chạy:
python run.py --skip-prepare --skip-embed  # Chỉ chạy server
python run.py --skip-embed  # Chạy prepare và server
```

### Cách 2: Chạy từng bước thủ công

#### Bước 1: Chuẩn hóa dữ liệu

```bash
# Từ file JSON
python prepare_recipes.py --source recipes.json --out docs.jsonl

# Từ API
python prepare_recipes.py --source api://http://localhost:8080/recipes/full-details --out docs.jsonl
```

#### Bước 2: Tạo embeddings và index

```bash
python embed_and_index.py --docs docs.jsonl --index out.index --meta meta.json

# Hoặc với model khác
python embed_and_index.py --docs docs.jsonl --index out.index --meta meta.json --model sentence-transformers/all-mpnet-base-v2
```

#### Bước 3: Chạy API server

```bash
# Chạy server
uvicorn serve_vector:app --host 0.0.0.0 --port 8000

# Với auto-reload (development)
uvicorn serve_vector:app --reload --host 0.0.0.0 --port 8000
```

## 🔌 API Endpoints

Sau khi server chạy, truy cập:
- **API Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

### 1. POST `/search` - Tìm kiếm recipes

Tìm kiếm recipes dựa trên query text.

**Request:**
```json
{
  "q": "cách nấu phở bò",
  "k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "score": 0.85,
      "meta": {
        "id": "recipe-123",
        "title": "Phở Bò",
        "text": "Title: Phở Bò\nIngredients: ...\nSteps: ..."
      }
    }
  ]
}
```

**Ví dụ với curl:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "cách nấu phở bò", "k": 5}'
```

### 2. POST `/train` - Train/index dữ liệu mới

Train lại index từ API URL hoặc cập nhật index.

**Request:**
```json
{
  "source_url": "http://localhost:8080/recipes/full-details",
  "index_path": "out.index",
  "meta_path": "meta.json",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunk_size": 1024,
  "chunk_overlap": 80
}
```

**Response:**
```json
{
  "status": "ok",
  "indexed": 150,
  "index_path": "out.index",
  "meta_path": "meta.json"
}
```

**Ví dụ với curl:**
```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "http://localhost:8080/recipes/full-details",
    "chunk_size": 1024
  }'
```

## ⚙️ Cấu hình

### Environment Variables

Có thể cấu hình qua biến môi trường:

```bash
# Windows PowerShell
$env:VECTOR_INDEX_PATH="out.index"
$env:VECTOR_META_PATH="meta.json"
$env:EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"
$env:OLLAMA_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama3.2:latest"

# Linux/Mac
export VECTOR_INDEX_PATH="out.index"
export VECTOR_META_PATH="meta.json"
export EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

### File cấu hình

- `INDEX_PATH`: Đường dẫn đến file FAISS index (mặc định: `out.index`)
- `META_PATH`: Đường dẫn đến file metadata (mặc định: `meta.json`)
- `EMBED_MODEL`: Model embedding (mặc định: `sentence-transformers/all-MiniLM-L6-v2`)
- `OLLAMA_URL`: URL của Ollama server (mặc định: `http://host.docker.internal:11434`)
- `OLLAMA_MODEL`: Model Ollama (mặc định: `llama3.2:latest`)

## 📁 Cấu trúc dự án

```
recipe_chatbot_agent/
├── prepare_recipes.py      # Chuẩn hóa dữ liệu recipes
├── embed_and_index.py      # Tạo embeddings và index
├── serve_vector.py         # FastAPI server
├── run.py                  # Script Python tự động
├── run.ps1                 # Script PowerShell tự động
├── translate_readme.py     # Script dịch README.md
├── requirements.txt        # Dependencies
├── recipes.json            # Dữ liệu recipes (input)
├── docs.jsonl              # Dữ liệu đã chuẩn hóa (output)
├── out.index               # FAISS index (output)
├── meta.json               # Metadata (output)
└── README.md               # File này
```

## 🔧 Troubleshooting

### Lỗi: ModuleNotFoundError: No module named 'faiss'

**Giải pháp:**
```bash
# Đảm bảo đang dùng Python từ venv
.venv\Scripts\python.exe -m pip install faiss-cpu

# Hoặc nếu trên Linux/Mac
.venv/bin/pip install faiss-cpu
```

### Lỗi: Execution Policy trong PowerShell

**Giải pháp:**
```powershell
# Bypass cho session hiện tại
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Hoặc dùng activate.bat thay vì Activate.ps1
.venv\Scripts\activate.bat
```

### Lỗi: FileNotFoundError khi search

**Giải pháp:**
- Đảm bảo đã chạy `embed_and_index.py` để tạo `out.index` và `meta.json`
- Hoặc dùng endpoint `/train` để tạo index từ API

### Lỗi: torch/torchvision compatibility

**Giải pháp:**
```bash
pip install --upgrade --force-reinstall torchvision==0.24.1
```

## 🌐 Dịch README

Script `translate_readme.py` giúp dịch README.md sang ngôn ngữ khác, tự động giữ nguyên format markdown, code blocks, và links.

### Cài đặt thư viện dịch

```bash
pip install deep-translator
```

### Sử dụng

```bash
# Dịch README.md sang tiếng Anh (mặc định)
python translate_readme.py

# Dịch sang tiếng Việt
python translate_readme.py --target vi --output README_VI.md

# Dịch từ file khác
python translate_readme.py --source README_VI.md --target en --output README_EN.md

# Chỉ định ngôn ngữ nguồn (nếu auto-detect không chính xác)
python translate_readme.py --from-lang vi --target en
```

**Tùy chọn:**
- `--source`: File README nguồn (mặc định: `README.md`)
- `--target`: Ngôn ngữ đích: `en`, `vi` (mặc định: `en`)
- `--output`: File output (mặc định: `README_{target}.md`)
- `--from-lang`: Ngôn ngữ nguồn: `auto`, `vi`, `en` (mặc định: `auto`)

**Lưu ý:**
- Script tự động phát hiện và giữ nguyên code blocks, inline code, links, và URLs
- Chỉ dịch phần text, không dịch code hoặc URLs
- Sử dụng Google Translate API (miễn phí)

## 📝 Ghi chú

- Model embedding mặc định: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Chunk size mặc định: 1024 ký tự với overlap 80 ký tự
- Index sử dụng FAISS IndexFlatIP (Inner Product cho cosine similarity)
- Embeddings được normalize để sử dụng cosine similarity

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo issue hoặc pull request.

## 📄 License

MIT License

