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

## 版本号管理

### 版本号位置（3 处，必须同步更新！）

| 文件 | 位置 | 用途 |
|------|------|------|
| `backend/app/main.py` | 第 29 行 `version="x.x.x"` | FastAPI 文档版本 |
| `backend/app/main.py` | 第 61 行 `"version": "x.x.x"` | API 根路径返回 |
| `frontend/package.json` | 第 3 行 `"version": "x.x.x"` | npm 包版本 |
| `frontend/src/components/LeftPanel/LeftPanel.tsx` | 约 251 行 `v{x.x.x}` | 页面左下角显示 |

### 版本号规则（语义化版本）

```
v{主版本}.{次版本}.{修订号}
  │         │        └── 修订号：bug 修复、小改动
  │         └────────── 次版本：新功能、较大改进
  └──────────────────── 主版本：重大变更、不兼容更新
```

**示例**：
- `2.2.1 → 2.2.2`：修复 bug
- `2.2.2 → 2.3.0`：新增功能或重要修复
- `2.3.0 → 3.0.0`：架构重构、不兼容变更

### 更新版本号命令

```bash
# 查找当前版本
grep -E "version.*[0-9]+\.[0-9]+\.[0-9]+" backend/app/main.py frontend/package.json frontend/src/components/LeftPanel/LeftPanel.tsx

# 更新后重建部署
docker compose build backend frontend --no-cache
docker compose up -d --force-recreate backend frontend
```

### 何时更新版本

- ✅ 功能开发完成并测试通过后
- ✅ bug 修复部署前
- ❌ 不要在开发过程中频繁更新

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

---

## 开发踩坑指南（血泪总结）

### 1. 时间显示问题（UTC 时区）

**问题**：后端 PostgreSQL 用 `func.now()` 存储 UTC 时间，但返回的 datetime 没有 `Z` 后缀，前端 `new Date()` 会当作本地时间解析，导致时间偏差 8 小时。

**解决方案**：前端解析时间时手动加 `Z` 后缀

```typescript
// ❌ 错误 - 时间会偏差
new Date(message.createdAt).toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai' })

// ✅ 正确 - 先加 Z 后缀再解析
const utcTime = message.createdAt.endsWith('Z') ? message.createdAt : message.createdAt + 'Z';
new Date(utcTime).toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai' })
```

**涉及文件**：`frontend/src/components/ChatArea/MessageList.tsx`

---

### 2. 列表排序不稳定

**问题**：只用 `updated_at DESC` 排序时，如果多条记录时间戳相同（同一秒内），排序顺序不确定。

**解决方案**：添加次要排序键 `id DESC`

```python
# ❌ 错误 - 排序不稳定
.order_by(Conversation.updated_at.desc())

# ✅ 正确 - 添加次要排序键
.order_by(Conversation.updated_at.desc(), Conversation.id.desc())
```

**涉及文件**：
- `backend/app/services/chat_service.py` - `get_user_conversations`
- `backend/app/routes/chat.py` - `search_conversations`

---

### 3. 图片上传到 Confluence 必须两步

**问题**：AI 调用 `upload_attachment_to_confluence` 上传图片后就结束，图片没有显示在页面上。

**根因**：Confluence 附件上传只是把文件存到页面附件列表，不会自动插入到内容中。

**解决方案**：在 SYSTEM_PROMPT 里强调两步流程

```markdown
## ⚠️ 图片上传的正确流程

**第1步**：upload_attachment_to_confluence → 返回 filename
**第2步**：必须调用 update_table_cell 或 edit_confluence_page 插入图片！

只执行第1步不会在页面显示图片！
```

**涉及文件**：`backend/app/services/tools.py` - `SYSTEM_PROMPT`

---

### 4. AI 工具重复调用检测

**问题**：上传多张图片时，AI 需要多次调用 `upload_attachment_to_confluence`，但被错误检测为"重复操作"而停止。

**根因**：原逻辑只检查工具名称是否相同，没有检查参数。

**解决方案**：检测"工具名+参数"的组合签名，只有完全相同才算重复

```python
# ❌ 错误 - 只检查工具名
if tool_name == last_tool_name:
    same_tool_count += 1

# ✅ 正确 - 检查工具名+参数签名
call_signature = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
if call_signature == last_tool_name:
    same_tool_count += 1
```

**涉及文件**：`backend/app/services/chat_service.py` - `chat_stream_with_tools`

---

### 5. 前端流式响应状态管理

**问题**：收到 `stream_start` 时立即设置 `isStreaming=true`，导致 TypingIndicator 消失，但此时还没有内容，出现空白期。

**解决方案**：在收到第一个 `stream_chunk` 时才设置 `isStreaming=true`

```typescript
// Chat.tsx WebSocket 消息处理
case 'stream_start':
  // 不要在这里设置 isStreaming，等实际内容到达
  break;

case 'stream_chunk':
  setIsStreaming(true);  // 收到内容后才隐藏 TypingIndicator
  // ... 处理内容
  break;
```

**状态流转**：
```
用户发送 → isLoading=true (显示 TypingIndicator)
         → isUploading=true (显示"正在上传附件")
上传完成 → isUploading=false (显示"AI 正在思考")
收到内容 → isStreaming=true (隐藏 TypingIndicator，显示流式内容)
结束     → isStreaming=false, isLoading=false
```

**涉及文件**：
- `frontend/src/pages/Chat.tsx` - WebSocket 消息处理
- `frontend/src/components/ChatArea/MessageList.tsx` - TypingIndicator

---

### 6. 多图片显示

**问题**：用户上传多张图片，但只显示第一张，其他显示为"📎 附件2"链接。

**根因**：`MessageList` 只渲染 `message.imageUrl`（单张），没有处理 `message.fileUrls`（多张）。

**解决方案**：
1. 分离图片和非图片文件
2. 图片显示为缩略图网格
3. 非图片文件显示为附件链接

```typescript
// 图片缩略图网格
{message.fileUrls
  .filter(url => /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(url))
  .map((url, idx) => (
    <a href={url} className={styles.imageThumbnail}>
      <img src={url} alt={`图片 ${idx + 1}`} />
    </a>
  ))}

// 非图片附件
{message.fileUrls
  .filter(url => !/\.(jpg|jpeg|png|gif|webp)$/i.test(url))
  .map((url, idx) => (
    <a href={url} className={styles.attachment}>📎 {filename}</a>
  ))}
```

**涉及文件**：
- `frontend/src/components/ChatArea/MessageList.tsx`
- `frontend/src/components/ChatArea/ChatArea.module.css` - `.imageGrid`, `.imageThumbnail`

---

### 7. CSS 更新后不生效

**问题**：修改了 CSS 但页面样式没变化。

**原因**：浏览器缓存了旧的 CSS 文件。

**解决方案**：
1. 告知用户强制刷新：`Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)
2. 或者修改 Vite 配置添加 hash

---

### 8. 表格内容 Markdown 不生效

**问题**：AI 生成的表格内容里 `**粗体**` 显示为原始文本，没有变成粗体。

**根因**：`_process_cell_content` 只处理了 `[image:filename]` 语法，没有转换 Markdown。

**解决方案**：在 `confluence_service.py` 添加 `_markdown_to_html` 方法

```python
def _markdown_to_html(self, text: str) -> str:
    # **bold** → <strong>bold</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *italic* → <em>italic</em>
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # ![alt](filename) → <ac:image>
    # [text](url) → <a href>
    # etc.
    return text
```

**涉及文件**：`backend/app/services/confluence_service.py`

---

### 9. 图片上传后用户消息消失

**问题**：用户发送带图片的消息，按回车后用户消息消失，先显示 AI "正在上传"，上传完才显示用户消息。

**根因**：代码先等待上传完成，再添加用户消息到列表。

**解决方案**：
1. 立即用 `URL.createObjectURL()` 创建本地预览
2. 立即显示用户消息
3. 后台上传
4. 上传完成后调用 `updateLastUserMessage()` 更新为服务器 URL
5. 清理本地 blob URL

```typescript
// 1. 创建本地预览
const localPreviewUrls = files.map(f => URL.createObjectURL(f));

// 2. 立即显示
addMessage({ role: 'user', content, fileUrls: localPreviewUrls });

// 3. 后台上传
const serverUrls = await uploadFiles(files);

// 4. 更新为服务器 URL
updateLastUserMessage(serverUrls[0], serverUrls);

// 5. 清理
localPreviewUrls.forEach(url => URL.revokeObjectURL(url));
```

**涉及文件**：`frontend/src/pages/Chat.tsx` - `handleSendMessage`

---

### 10. Markdown 表格中图片语法不生效

**问题**：AI 用 `update_confluence_page` 创建表格时，表格里的 `[image:filename]` 语法显示为原始文本，图片不显示。

**根因**：`markdown_to_html()` 方法处理 Markdown 表格时，直接用 `html.escape()` 转义单元格内容，没有调用 `_process_cell_content()` 来处理图片语法。

**解决方案**：修改 `markdown_to_html()` 中的表格处理逻辑

```python
# ❌ 错误 - 直接转义，[image:xxx] 变成文本
row = '<tr>' + ''.join(f'<td>{html.escape(c)}</td>' for c in cells) + '</tr>'

# ✅ 正确 - 调用 _process_cell_content 处理图片和 Markdown
row = '<tr>' + ''.join(f'<td>{self._process_cell_content(c)}</td>' for c in cells) + '</tr>'
```

**涉及文件**：`backend/app/services/confluence_service.py` - `markdown_to_html()`

---

### 11. Confluence 附件图片格式

**问题**：上传到 Confluence 的图片无法显示。

**根因**：Confluence 有两种图片引用格式：
- `<ri:url ri:value="xxx.jpg"/>` - 外部 URL，**无法显示本地附件**
- `<ri:attachment ri:filename="xxx.jpg"/>` - 页面附件，**正确格式**

**正确做法**：
```html
<!-- ✅ 正确 - 附件格式 -->
<ac:image><ri:attachment ri:filename="image.jpg"/></ac:image>

<!-- ❌ 错误 - URL 格式无法显示附件 -->
<ac:image><ri:url ri:value="image.jpg"/></ac:image>
```

**代码中的处理**：`[image:filename]` 语法会被转换为正确的 `<ri:attachment>` 格式

**涉及文件**：`backend/app/services/confluence_service.py` - `_process_cell_content()`

---

### 12. edit_confluence_page 图片语法不转换

**问题**：AI 用 `edit_confluence_page` 替换 HTML 内容时，`[image:xxx]` 或 `![](xxx)` 语法没有被转换为 Confluence 图片格式。

**根因**：`tool_executor.py` 中的 `_edit_page` 方法判断内容以 `<` 开头就认为是 HTML，直接跳过所有转换。

**解决方案**：

```python
# ❌ 错误 - 以 < 开头就完全跳过转换
if new_content.strip() and not new_content.strip().startswith('<'):
    new_content = self.confluence.markdown_to_html(new_content)
# [image:xxx] 在 HTML 中就无法转换

# ✅ 正确 - HTML 内容也要处理图片语法
if new_content.strip() and not new_content.strip().startswith('<'):
    new_content = self.confluence.markdown_to_html(new_content)
else:
    new_content = self.confluence._process_cell_content(new_content)
```

**涉及文件**：`backend/app/services/tool_executor.py` - `_edit_page()`

---

### 13. Markdown 图片正则顺序问题

**问题**：`![alt](image.png)` 被错误转换为 `!<a href="image.png">alt</a>`

**根因**：`_markdown_to_html` 中链接正则 `[text](url)` 先于图片正则 `![alt](url)` 执行，导致图片语法中的 `[alt](url)` 部分被当作链接处理。

**解决方案**：图片正则必须在链接正则之前执行

```python
def _markdown_to_html(self, text: str) -> str:
    # ✅ 图片必须先于链接处理！
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, text)

    # 然后才处理链接
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
```

**涉及文件**：`backend/app/services/confluence_service.py` - `_markdown_to_html()`

---

### 14. Docker 前端构建缓存问题

**问题**：修改前端代码后，Docker 构建的镜像里没有新代码，或者 Vite 生成的 JS 文件哈希没变。

**根因**：
1. Docker BuildKit 有激进的缓存策略
2. Vite 可能有 node_modules/.vite 缓存
3. 本地 dist 目录可能被复制到构建上下文中

**解决方案**：在 Dockerfile 中添加清除缓存步骤

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# ✅ 清除缓存，确保使用最新代码构建
RUN rm -rf dist node_modules/.vite node_modules/.cache

RUN npm run build
```

**验证命令**：
```bash
# 检查容器里是否有新代码
docker compose exec frontend sh -c 'cat /usr/share/nginx/html/assets/index-*.js | grep -o "你的新代码关键字"'

# 完全重建前端
docker compose build frontend --no-cache && docker compose up -d --force-recreate frontend
```

**涉及文件**：`frontend/Dockerfile`

---

### 15. 前端更新后用户看不到变化

**问题**：Docker 构建部署成功，但用户浏览器里还是旧版本。

**原因**：浏览器缓存了旧的 JS/CSS 文件。

**解决方案**：
1. 告知用户强制刷新：`Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac)
2. 或者清除浏览器缓存后刷新

---

## ⚠️ 前端修改必须手动测试

**这是血泪教训，必须遵守！**

### 问题背景

修改前端代码后，只做了：
1. ✅ 写代码
2. ✅ 构建部署
3. ❌ **没有在浏览器里实际操作测试**
4. 直接告诉用户"已修复"

结果：用户反馈功能不生效，实际上是 UX 设计缺陷（测试成功后用户以为配置已保存，但实际需要再点保存按钮）。

### 强制要求

**修改前端交互逻辑后，必须：**

1. **以新用户视角** 在浏览器里走完整流程
2. 不要假设用户知道操作步骤
3. 特别注意：
   - 表单提交流程（是否需要额外点击？）
   - 成功/失败反馈是否清晰？
   - 用户是否知道下一步该做什么？

### 测试检查清单

修改前端后，至少验证：

- [ ] 在浏览器中打开页面（强制刷新 Ctrl+Shift+R）
- [ ] 模拟新用户操作：不看代码，只看界面提示
- [ ] 验证成功路径：操作 → 反馈 → 结果符合预期
- [ ] 验证失败路径：错误提示是否清晰？
- [ ] 检查控制台是否有报错

### 为什么不能只看代码

- 开发者知道内部逻辑，会"自动"做正确的操作
- 新用户只看界面提示，容易误解
- UX 问题无法通过代码审查发现，只能通过实际操作发现

---

## 调试技巧

### 后端日志
```bash
# 实时查看后端日志
docker compose logs -f backend

# 查看最近 100 行
docker compose logs backend --tail=100
```

### 前端调试
```javascript
// 在浏览器控制台查看 store 状态
// React DevTools 或直接打印
console.log(useChatStore.getState())
```

### 数据库调试
```bash
# 进入 psql
docker compose exec postgres psql -U cfbot -d confluence_chatbot

# 常用查询
SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 5;
SELECT * FROM messages WHERE conversation_id = X ORDER BY created_at;
```

