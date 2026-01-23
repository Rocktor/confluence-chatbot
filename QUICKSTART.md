# Confluence Chatbot 快速启动指南

## 前置要求

- Docker 和 Docker Compose
- 域名 cf.rocktor.shop 已配置DNS
- Azure OpenAI API密钥
- 钉钉应用AppKey和AppSecret

## 5分钟快速部署

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下配置：

```bash
# 数据库（必填）
POSTGRES_PASSWORD=your_secure_password_here

# Redis（必填）
REDIS_PASSWORD=your_redis_password_here

# Azure OpenAI（必填）
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 钉钉（必填）
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret

# JWT（必填，至少32字符）
JWT_SECRET=your_random_secret_key_min_32_chars
```

### 2. 配置SSL证书

将SSL证书放到 `nginx/ssl/` 目录：

```bash
# 如果使用Let's Encrypt
sudo certbot certonly --webroot -w /var/www/certbot -d cf.rocktor.shop

# 复制证书
sudo cp /etc/letsencrypt/live/cf.rocktor.shop/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/cf.rocktor.shop/privkey.pem nginx/ssl/
```

### 3. 运行部署脚本

```bash
./deploy.sh
```

### 4. 验证部署

访问 https://cf.rocktor.shop，应该看到登录页面。

## 常用命令

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务

```bash
docker-compose down
```

### 重新构建

```bash
docker-compose up -d --build
```

## 数据库管理

### 连接数据库

```bash
docker-compose exec postgres psql -U cfbot -d confluence_chatbot
```

### 备份数据库

```bash
docker-compose exec postgres pg_dump -U cfbot confluence_chatbot > backup.sql
```

### 恢复数据库

```bash
docker-compose exec -T postgres psql -U cfbot confluence_chatbot < backup.sql
```

## 故障排查

### 1. 服务无法启动

检查日志：
```bash
docker-compose logs backend
```

### 2. 数据库连接失败

检查PostgreSQL状态：
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### 3. 前端无法访问

检查Nginx配置：
```bash
docker-compose logs nginx
```

### 4. WebSocket连接失败

确认Nginx配置了WebSocket支持，检查 `nginx/conf.d/default.conf`。

## 性能监控

### 查看资源使用

```bash
docker stats
```

### 查看数据库连接

```bash
docker-compose exec postgres psql -U cfbot -d confluence_chatbot -c "SELECT count(*) FROM pg_stat_activity;"
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 安全建议

1. 定期更新依赖包
2. 使用强密码
3. 定期备份数据库
4. 监控日志异常
5. 配置防火墙规则

## 获取帮助

如遇问题，请查看：
- README.md - 完整文档
- docker-compose logs - 服务日志
- GitHub Issues - 提交问题
