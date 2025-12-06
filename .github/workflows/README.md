# GitHub Actions Workflows

Dự án này sử dụng GitHub Actions để tự động hóa CI/CD pipeline.

## 📋 Workflows Overview

### 1. CI/CD Pipeline (`ci.yml`)
Workflow chính chạy trên mỗi push và pull request:
- ✅ Lint code với flake8
- ✅ Check code formatting với black
- ✅ Test imports
- ✅ Build Docker image
- ✅ Push lên GitHub Container Registry
- ✅ Security scan với Trivy
- ✅ Deploy lên Render (nếu cấu hình)

### 2. Docker Build (`docker-build.yml`)
Chuyên build và push Docker images:
- Build multi-platform (amd64, arm64)
- Tự động tag theo version, branch, commit
- Push lên `ghcr.io`

### 3. Render Deploy (`render-deploy.yml`)
Deploy tự động lên Render:
- Trigger khi push vào main/master
- Hỗ trợ manual trigger với environment selection
- Health check sau khi deploy

### 4. Tests (`test.yml`)
Chạy test suite:
- Test trên nhiều Python versions (3.11, 3.12)
- Test trên Ubuntu và Windows
- Kiểm tra imports và API

## 🚀 Quick Start

### 1. Push code lên GitHub
```bash
git add .
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### 2. Xem workflows chạy
- Vào tab **Actions** trên GitHub repository
- Xem logs và kết quả

### 3. Cấu hình Secrets (Optional)

Nếu muốn deploy tự động lên Render:

1. Lấy Render API Key:
   - Đăng nhập [Render Dashboard](https://dashboard.render.com)
   - Account Settings → API Keys → Create API Key

2. Lấy Service ID:
   - Vào service trên Render
   - Service ID trong URL: `dashboard.render.com/web/{SERVICE_ID}`

3. Thêm vào GitHub Secrets:
   - Repository → Settings → Secrets and variables → Actions
   - Thêm các secrets:
     - `RENDER_API_KEY`
     - `RENDER_SERVICE_ID`
     - `RENDER_SERVICE_URL`

## 📦 Docker Images

Sau khi workflow chạy, Docker images sẽ được push lên:
```
ghcr.io/your-username/recipe-chatbot-api:latest
ghcr.io/your-username/recipe-chatbot-api:main-{sha}
```

### Pull và chạy image:
```bash
docker pull ghcr.io/your-username/recipe-chatbot-api:latest
docker run -p 8000:8000 ghcr.io/your-username/recipe-chatbot-api:latest
```

## 🔧 Customization

### Thay đổi trigger branches:
Sửa trong các workflow files:
```yaml
on:
  push:
    branches: [ main, master, develop ]  # Thêm branches bạn muốn
```

### Thêm tests:
Tạo file test trong thư mục `tests/` và workflow sẽ tự động chạy.

### Thay đổi Docker registry:
Sửa `REGISTRY` và `IMAGE_NAME` trong `docker-build.yml`

## 🐛 Troubleshooting

### Workflow không chạy:
- Kiểm tra file có đúng path: `.github/workflows/*.yml`
- Kiểm tra syntax YAML
- Xem Actions tab để xem lỗi

### Docker build fail:
- Kiểm tra Dockerfile syntax
- Xem logs trong Actions để biết lỗi cụ thể

### Render deploy fail:
- Kiểm tra secrets đã được thêm đúng chưa
- Kiểm tra Service ID có đúng không
- Xem Render dashboard để xem deployment status

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Render API Documentation](https://render.com/docs/api)

