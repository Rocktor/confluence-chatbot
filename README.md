# Confluence Chatbot 系统

一个集成了多模态AI聊天、Confluence文档管理和钉钉登录的Web应用系统。

## 功能特性

- **钉钉扫码登录**: 安全便捷的企业级认证
- **AI聊天**: 基于Azure OpenAI的智能对话，支持文本和图片
- **Confluence集成**: 完整的CRUD操作，支持文档同步和向量化
- **RAG检索**: 基于pgvector的语义搜索和文档问答
- **实时通信**: WebSocket支持的流式响应

## 技术栈

### 后端
- Python 3.11
- FastAPI
- PostgreSQL + pgvector
- Redis
- Azure OpenAI
- SQLAlchemy

### 前端
- React 18
- TypeScript
- Vite
- Zustand
- React Router

### 部署
- Docker Compose
- Nginx
- Let's Encrypt SSL

## 快速开始

### 1. 环境准备

确保已安装：
- Docker
- Docker Compose
- Git

### 2. 克隆项目

```bash
git clone <repository-url>
cd confluence
```

### 3. 配置环境变量

复制环境变量示例文件并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必需配置：

```bash
# 数据库密码
POSTGRES_PASSWORD=your_secure_password

# Redis密码
REDIS_PASSWORD=your_redis_password

# Azure OpenAI配置
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 钉钉配置
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret

# JWT密钥（至少32字符）
JWT_SECRET=your_random_secret_key_min_32_chars
```

### 4. 启动服务

```bash
docker-compose up -d
```

### 5. 访问应用

- 应用地址: https://cf.rocktor.shop
- API文档: https://cf.rocktor.shop/api/docs

## 项目结构

```
confluence/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API路由
│   │   ├── services/       # 业务逻辑
│   │   ├── middleware/     # 中间件
│   │   ├── websocket/      # WebSocket处理
│   │   └── dependencies/   # 依赖注入
│   ├── scripts/            # 数据库脚本
│   └── Dockerfile
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── store/         # 状态管理
│   │   └── utils/         # 工具函数
│   └── Dockerfile
├── nginx/                  # Nginx配置
│   ├── nginx.conf
│   └── conf.d/
├── docker-compose.yml      # Docker编排
└── .env.example           # 环境变量示例
```

## API文档

### 认证API

- `POST /api/auth/qrcode/generate` - 生成登录二维码
- `GET /api/auth/qrcode/status/{sessionId}` - 查询登录状态
- `POST /api/auth/refresh` - 刷新Token
- `GET /api/auth/me` - 获取当前用户

### 聊天API

- `WS /api/chat/ws` - WebSocket连接
- `POST /api/chat/conversations` - 创建会话
- `GET /api/chat/conversations` - 列出会话

### Confluence API

- `POST /api/confluence/configs` - 配置Confluence连接
- `POST /api/confluence/pages` - 创建页面
- `GET /api/confluence/pages/{id}` - 读取页面
- `PUT /api/confluence/pages/{id}` - 更新页面
- `DELETE /api/confluence/pages/{id}` - 删除页面
- `POST /api/confluence/sync` - 同步页面到向量库

## 部署说明

### SSL证书配置

1. 使用Let's Encrypt获取证书：

```bash
certbot certonly --webroot -w /var/www/certbot -d cf.rocktor.shop
```

2. 将证书复制到nginx/ssl目录：

```bash
cp /etc/letsencrypt/live/cf.rocktor.shop/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/cf.rocktor.shop/privkey.pem nginx/ssl/
```

### 钉钉配置

1. 在钉钉开放平台创建应用
2. 配置回调地址白名单：`https://cf.rocktor.shop`
3. 获取AppKey和AppSecret

### 数据库初始化

数据库会在首次启动时自动初始化，包括：
- 创建所有表
- 安装pgvector扩展
- 创建索引

### 监控和日志

查看服务日志：

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

## 开发指南

### 后端开发

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 常见问题

### 1. 数据库连接失败

检查PostgreSQL服务是否正常运行：
```bash
docker-compose ps postgres
```

### 2. Redis连接失败

检查Redis密码配置是否正确。

### 3. WebSocket连接失败

确保Nginx配置了WebSocket支持，检查防火墙设置。

### 4. 钉钉登录失败

- 检查AppKey和AppSecret是否正确
- 确认回调地址已在钉钉开放平台配置

## 性能优化

- 数据库查询使用索引
- 向量检索使用HNSW索引
- Redis缓存会话数据
- Nginx启用gzip压缩
- 静态资源CDN加速

## 安全建议

- 定期更新依赖包
- 使用强密码
- 启用HTTPS
- 配置防火墙
- 定期备份数据库
- API Token加密存储

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系开发团队。
