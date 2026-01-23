# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要警告

**此项目仅用于 cf.rocktor.shop，绝对不要修改或影响 juniordao.com（线上生产系统）！**

## 禁止操作

1. 不要修改 juniordao.com 相关的任何配置
2. 不要修改 `/etc/nginx/sites-available` 中与 juniordao.com 相关的配置
3. 不要操作其他项目目录

## 常用命令

```bash
# 构建和部署（⚠️ 重要：build 后必须用 --force-recreate 重建容器！）
./deploy.sh                                    # 完整部署
docker compose build frontend --no-cache       # 重新构建前端镜像
docker compose build backend --no-cache        # 重新构建后端镜像
docker compose up -d --force-recreate frontend # 前端更新后用这个
docker compose up -d --force-recreate backend  # 后端更新后用这个
docker compose up -d                           # 启动所有服务

# ⚠️ 注意：docker compose restart 不会使用新镜像！
# 修改代码后必须：1. build --no-cache  2. up -d --force-recreate

# 日志
docker compose logs backend --tail=50
docker compose logs frontend --tail=50
docker compose logs -f                         # 实时日志

# 数据库
docker compose exec postgres psql -U cfbot -d confluence_chatbot

# 本地开发
cd backend && uvicorn app.main:app --reload    # 后端开发服务器
cd frontend && npm run dev                     # 前端开发服务器
cd frontend && npm run build                   # 前端构建
```

## 架构概览

```
frontend/          React + TypeScript + Vite
  src/pages/       页面组件 (Login, Chat, Admin)
  src/components/  UI 组件 (ChatArea, LeftPanel, Dialogs)
  src/store/       Zustand 状态管理 (authStore, chatStore)
  src/utils/api.ts API 客户端（含自动字段转换）

backend/           FastAPI + Python
  app/routes/      API 路由 (auth, chat, confluence, admin)
  app/services/    业务逻辑 (azure_openai, rag, confluence_api, dingtalk)
  app/models/      ORM 模型和 Pydantic schemas
  app/config.py    配置管理

nginx/             反向代理 + SSL 终止
```

## 核心服务

- **postgres**: PostgreSQL 16 + pgvector（向量检索）
- **redis**: 会话缓存
- **backend**: FastAPI 应用 (端口 8100)
- **frontend**: Nginx 静态服务 (端口 3200)
- **nginx**: HTTPS 入口 (端口 443)

## API 字段命名规范

**🔴 极其重要：这是最常见的 BUG 来源，每次修改前端代码都必须检查！**

### 核心规则

前端 `api.ts` 自动将后端 snake_case 转换为 camelCase：

```typescript
// 后端返回: { access_token, created_at, is_active, base_url, api_token }
// 前端接收: { accessToken, createdAt, isActive, baseUrl, apiToken }

// ✅ 正确 - 前端代码必须使用 camelCase
const { accessToken, createdAt, baseUrl, apiToken } = response.data;

// ❌ 错误 - 使用 snake_case 会得到 undefined
const { access_token, created_at, base_url, api_token } = response.data;
```

**规则总结：**
1. **后端 → 前端**：API 响应自动转换，前端必须用 camelCase 接收
2. **前端 → 后端**：发送请求时必须用 snake_case（后端期望的格式）
3. **前端内部**：所有 TypeScript 接口和变量必须用 camelCase

```typescript
// 发送请求示例
await api.post('/api/confluence/configs', {
  base_url: config.baseUrl,    // 发送用 snake_case
  api_token: config.apiToken,  // 发送用 snake_case
});
```

### 常见错误实例（血泪教训）

#### ❌ 错误 1：Admin 登录日志（已修复）
```typescript
// 后端返回：{ user_name, login_type, ip_address, created_at }
// ❌ 错误写法（显示全是空白）
<td>{log.user_name}</td>
<td>{log.login_type}</td>
<td>{log.ip_address}</td>

// ✅ 正确写法
<td>{log.userName}</td>
<td>{log.loginType}</td>
<td>{log.ipAddress}</td>
```

#### ❌ 错误 2：用户列表
```typescript
// 后端：{ is_active, last_login_at, total_tokens }
// ❌ 错误
user.is_active, user.last_login_at, user.total_tokens

// ✅ 正确
user.isActive, user.lastLoginAt, user.totalTokens
```

#### ❌ 错误 3：Confluence 配置
```typescript
// 后端：{ base_url, api_token, space_key, updated_at }
// ❌ 错误
config.base_url, config.api_token, config.space_key

// ✅ 正确
config.baseUrl, config.apiToken, config.spaceKey
```

### 开发检查清单

**修改前端代码时，必须检查：**

- [ ] 所有 API 响应字段使用 camelCase（不是 snake_case）
- [ ] 所有发送到后端的数据使用 snake_case
- [ ] TypeScript 接口定义使用 camelCase
- [ ] 控制台无 `undefined` 错误（说明字段名错误）
- [ ] 表格/列表有数据显示（不是全空白）

### 调试技巧

```typescript
// 1. 打印 API 响应查看实际字段名
console.log('API Response:', response.data);

// 2. 检查是否 undefined
console.log('Field check:', {
  userName: log.userName,        // ✅ 应该有值
  user_name: log.user_name,      // ❌ 应该是 undefined
});
```

## 关键配置

- **钉钉登录**: redirect_uri 必须为 `https://cf.rocktor.shop/login`
- **向量维度**: 1536 维（text-embedding-3-large）
- **WebSocket**: `wss://cf.rocktor.shop/api/chat/ws`

## 数据库核心表

- `users` - 用户（钉钉信息）
- `conversations` / `messages` - 聊天记录
- `confluence_configs` / `confluence_pages` - Confluence 配置和缓存
- `document_chunks` - 文档分块（含向量）
- `token_usages` - Token 使用统计

## AI Agent 工具

| 工具 | 用途 | 优先级 |
|-----|------|-------|
| `read_confluence_page` | 读取页面（返回 Markdown + HTML） | - |
| `edit_confluence_page` | 精确编辑（HTML 查找替换） | ⭐ 推荐 |
| `insert_content_to_confluence_page` | 开头/结尾插入 | 次选 |
| `update_confluence_page` | 全量替换 | 谨慎 |
| `create_confluence_page` | 创建新页面 | - |
| `search_confluence` | 搜索页面 | - |

**精确编辑流程**：读取页面 → 从 `html` 字段找到目标片段 → 调用 `edit_confluence_page` 替换
