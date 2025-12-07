# GitHub Actions Workflow

Dự án sử dụng GitHub Actions để tự động build và push Docker image lên Docker Hub.

## 📋 Workflow Overview

### Docker Deploy (`docker-deploy.yml`)
Workflow đơn giản chạy khi push code vào `main`/`master` branch:
- ✅ Build Docker image sử dụng `docker-compose.prod.yml`
- ✅ Tag image với multiple tags (latest, commit SHA, branch name)
- ✅ Push image lên Docker Hub

## 🚀 Quick Start

### 1. Cấu hình GitHub Secrets

**Settings → Secrets and variables → Actions → New repository secret**

Thêm các secrets sau:
- `DOCKER_USERNAME`: Tên đăng nhập Docker Hub của bạn
- `DOCKER_PASSWORD`: Access Token hoặc password Docker Hub

### 2. Push code lên GitHub

```bash
git add .
git commit -m "Add Docker workflow"
git push origin main
```

### 3. Xem workflow chạy

- Vào tab **Actions** trên GitHub repository
- Xem logs và kết quả

## 📦 Docker Images

Sau khi workflow chạy thành công, Docker images sẽ được push lên:

```
your-username/recipe-chatbot-api:latest
your-username/recipe-chatbot-api:{commit-sha}
your-username/recipe-chatbot-api:{branch-name}
```

### Pull và chạy:

```bash
# Pull latest
docker pull your-username/recipe-chatbot-api:latest

# Chạy container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name recipe-api \
  your-username/recipe-chatbot-api:latest
```

## 🔧 Customization

### Thay đổi trigger branches:

Sửa trong `docker-deploy.yml`:
```yaml
on:
  push:
    branches: [ "main", "master", "develop" ]  # Thêm branches bạn muốn
```

### Thay đổi Docker Hub repository name:

Sửa trong workflow file:
```yaml
docker tag $IMAGE_ID ${{ secrets.DOCKER_USERNAME }}/your-repo-name:latest
```

## 🐛 Troubleshooting

### Workflow không chạy:
- Kiểm tra file có đúng path: `.github/workflows/docker-deploy.yml`
- Kiểm tra syntax YAML
- Xem Actions tab để xem lỗi

### Docker build fail:
- Kiểm tra Dockerfile syntax
- Xem logs trong Actions để biết lỗi cụ thể
- Đảm bảo `docker-compose.prod.yml` có đúng format

### Docker Hub push fail:
- Kiểm tra secrets đã được thêm đúng chưa
- Kiểm tra Docker Hub credentials có đúng không
- Đảm bảo repository đã được tạo trên Docker Hub (hoặc sẽ tự động tạo)

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
