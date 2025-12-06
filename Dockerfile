# Multi-stage build để tối ưu kích thước image
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt dependencies
WORKDIR /app
COPY requirements.txt .

# Cài đặt dependencies
# Lưu ý: Trong Docker (Linux), sử dụng faiss-cpu thay vì faiss
RUN pip install --no-cache-dir --user faiss-cpu && \
    pip install --no-cache-dir --user fastapi pydantic numpy sentence-transformers ollama requests uvicorn langchain langchain-community langchain-groq langchain-core gpt4all langgraph chromadb tavily-python gradio langchain-huggingface deep-translator

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages từ builder
COPY --from=builder /root/.local /root/.local

# Đảm bảo scripts trong .local/bin có trong PATH
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY *.py ./
COPY requirements.txt ./

# Tạo thư mục cho data files
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Environment variables với giá trị mặc định
ENV VECTOR_INDEX_PATH=/app/data/out.index
ENV VECTOR_META_PATH=/app/data/meta.json
ENV EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV PORT=8000
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs', timeout=5)" || exit 1

# Run startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "serve_vector:app", "--host", "0.0.0.0", "--port", "8000"]

