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

## 🐳 Docker Deployment

### Chạy với Docker

#### Build và chạy image:

```bash
# Build image
docker build -t recipe-chatbot-api .

# Chạy container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e VECTOR_INDEX_PATH=/app/data/out.index \
  -e VECTOR_META_PATH=/app/data/meta.json \
  --name recipe-api \
  recipe-chatbot-api
```

#### Hoặc sử dụng Docker Compose:

```bash
# Tạo thư mục data nếu chưa có
mkdir -p data

# Chạy với docker-compose
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng
docker-compose down
```

**Lưu ý:**
- Thư mục `data/` sẽ được mount để lưu trữ index files
- Nếu chưa có index, bạn có thể tạo qua endpoint `/train` sau khi container chạy
- Hoặc copy `out.index` và `meta.json` vào thư mục `data/` trước khi chạy

### Build và test Docker image:

```bash
# Build
docker build -t recipe-chatbot-api .

# Test locally
docker run -p 8000:8000 recipe-chatbot-api

# Kiểm tra health
curl http://localhost:8000/docs
```

## ☁️ Deploy lên Render

### Cách 1: Sử dụng render.yaml (Khuyến nghị)

1. **Push code lên GitHub/GitLab**
   ```bash
   git add .
   git commit -m "Add Docker and Render config"
   git push origin main
   ```

2. **Tạo service trên Render:**
   - Đăng nhập [Render Dashboard](https://dashboard.render.com)
   - Chọn "New" → "Blueprint"
   - Connect repository
   - Render sẽ tự động detect `render.yaml` và deploy

3. **Cấu hình Environment Variables** (nếu cần):
   - `VECTOR_INDEX_PATH`: `/opt/render/project/src/data/out.index`
   - `VECTOR_META_PATH`: `/opt/render/project/src/data/meta.json`
   - `EMBED_MODEL`: `sentence-transformers/all-MiniLM-L6-v2`

4. **Tạo index sau khi deploy:**
   - Sau khi service chạy, gọi endpoint `/train` để tạo index:
   ```bash
   curl -X POST "https://your-app.onrender.com/train" \
     -H "Content-Type: application/json" \
     -d '{
       "source_url": "http://your-api.com/recipes/full-details",
       "chunk_size": 1024
     }'
   ```

### Cách 2: Deploy thủ công trên Render

1. **Tạo Web Service:**
   - Chọn "New" → "Web Service"
   - Connect repository
   - Cấu hình:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn serve_vector:app --host 0.0.0.0 --port $PORT`
     - **Environment**: `Python 3`

2. **Thêm Persistent Disk** (để lưu index):
   - Settings → Disks → Add Disk
   - Mount path: `/opt/render/project/src/data`
   - Size: 1GB (hoặc lớn hơn tùy nhu cầu)

3. **Environment Variables:**
   ```
   VECTOR_INDEX_PATH=/opt/render/project/src/data/out.index
   VECTOR_META_PATH=/opt/render/project/src/data/meta.json
   EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

4. **Deploy và tạo index:**
   - Sau khi deploy thành công, sử dụng endpoint `/train` để tạo index

### Lưu ý khi deploy lên Render:

- **Build time**: Lần đầu build có thể mất 5-10 phút do cài đặt dependencies
- **Cold start**: Service có thể mất 30-60 giây để start lần đầu
- **Memory**: Đảm bảo plan đủ RAM (tối thiểu 512MB, khuyến nghị 1GB+)
- **Disk**: Sử dụng Persistent Disk để lưu index files
- **Auto-deploy**: Render tự động deploy khi có commit mới (nếu bật)

## 🔄 GitHub Actions CI/CD

Dự án đã được cấu hình với GitHub Actions để tự động build và push Docker image lên Docker Hub.

### Workflow:

**Docker Deploy** (`.github/workflows/docker-deploy.yml`)
- Tự động build Docker image khi push code vào `main`/`master` branch
- Build image sử dụng `docker-compose.prod.yml` với profile `prod`
- Tag image với: `latest`, commit SHA, và branch name
- Push image lên Docker Hub

### Cấu hình GitHub Secrets:

Để workflow hoạt động, cần thêm các secrets sau trong GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

1. **Docker Hub Credentials** (bắt buộc):
   ```
   DOCKER_USERNAME=your_dockerhub_username
   DOCKER_PASSWORD=your_dockerhub_password
   ```

### Cách lấy Docker Hub credentials:

1. Đăng nhập [Docker Hub](https://hub.docker.com)
2. Vào **Account Settings** → **Security**
3. Tạo Access Token mới (khuyến nghị) hoặc dùng password
4. Thêm vào GitHub Secrets:
   - `DOCKER_USERNAME`: Tên đăng nhập Docker Hub
   - `DOCKER_PASSWORD`: Access Token hoặc password

### Trigger workflow:

- **Tự động**: Khi push code vào `main`/`master` branch
- **Manual**: Vào **Actions** tab → Chọn "Docker Image CI" → **Run workflow**

### Xem kết quả:

- Vào tab **Actions** trên GitHub repository
- Xem logs và kết quả của workflow run
- Docker images sẽ được push lên: `your-username/recipe-chatbot-api`

### Pull và chạy image từ Docker Hub:

```bash
# Pull latest image
docker pull your-username/recipe-chatbot-api:latest

# Chạy container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name recipe-api \
  your-username/recipe-chatbot-api:latest
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
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
├── docker-entrypoint.sh    # Docker startup script
├── render.yaml             # Render.com deployment config
├── .dockerignore           # Docker ignore patterns
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       └── docker-deploy.yml # Docker build & push to Docker Hub
├── docker-compose.prod.yml  # Docker Compose config for production build
├── recipes.json            # Dữ liệu recipes (input)
├── docs.jsonl              # Dữ liệu đã chuẩn hóa (output)
├── data/                   # Thư mục lưu index (Docker/Render)
│   ├── out.index           # FAISS index (output)
│   └── meta.json           # Metadata (output)
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

