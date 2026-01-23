# Confluence Chatbot 更新说明

## 更新内容

### 1. 精确编辑能力 (2026-01-20)

新增 `edit_confluence_page` 工具，实现类似 Claude Code 的精确编辑能力：

#### 核心改进
- **保留原始 HTML**: `read_confluence_page` 现在同时返回 Markdown（阅读）和原始 HTML（编辑）
- **精确替换**: 在原始 HTML 中查找并替换指定内容，保留其他所有格式和图片
- **智能转换**: `new_content` 支持 Markdown 格式，系统自动转换为 HTML

#### 工具优先级
1. `edit_confluence_page` - 修改某一段、某个标题、某个表格（推荐）
2. `insert_content_to_confluence_page` - 在开头/结尾插入内容
3. `update_confluence_page` - 完全替换页面（谨慎使用）

#### 代码更新
- `backend/app/services/tool_executor.py`:
  - `_read_page` 返回 `html` 字段（最大 12000 字符）
  - 新增 `_edit_page` 方法实现精确编辑
- `backend/app/services/tools.py`:
  - 新增 `edit_confluence_page` 工具定义
  - 更新 SYSTEM_PROMPT 指导 AI 使用精确编辑
- `backend/app/websocket/chat_handler.py`:
  - 添加工具显示名称 "精确编辑"

#### 使用示例
```
用户: 把第一段改成 XXX
AI: 调用 edit_confluence_page，从 html 字段找到第一段的 HTML，精确替换
结果: 只修改第一段，其他内容（图片、表格）完整保留
```

### 2. Azure OpenAI GPT-5.1 集成

参考 JuniorDao 项目的实现，已更新为使用 GPT-5.1 模型：

#### 配置更新
- **API版本**: `2024-12-01-preview` (GPT-5.1 专用版本)
- **部署名称**: `gpt-5.1`
- **最大输出Token**: 65536 (64K)
- **参数名称**: 使用 `max_completion_tokens` 替代 `max_tokens`

#### 代码更新
- `backend/app/config.py`: 添加 `AZURE_OPENAI_API_VERSION` 配置
- `backend/app/services/azure_openai_service.py`:
  - 更新API版本
  - 使用 `max_completion_tokens` 参数
  - 添加重试机制 (tenacity)
  - 设置 max_completion_tokens = 65536

### 2. 钉钉登录新版API

参考 dingtalk-bot-new 项目的实现，已更新为使用钉钉新版API：

#### 三步认证流程
1. **获取用户个人Token**: 使用 authCode 换取 accessToken
   - API: `https://api.dingtalk.com/v1.0/oauth2/userAccessToken`

2. **获取用户个人信息**: 使用 accessToken 获取 unionId
   - API: `https://api.dingtalk.com/v1.0/contact/users/me`

3. **获取企业userid**: 使用 unionId 查询企业内用户
   - API: `https://oapi.dingtalk.com/topapi/user/getbyunionid`

#### 关键改进
- 使用新版OAuth2.0 API
- 支持企业员工验证（通过userid判断）
- 会话有效期延长至180天
- 添加详细日志记录 (structlog)

#### 代码更新
- `backend/app/services/dingtalk_service.py`:
  - 实现三步认证流程
  - 添加 structlog 日志
  - 增加超时设置 (30秒)
- `backend/app/services/auth_service.py`:
  - 更新回调处理逻辑
  - 会话有效期设置为180天
  - 添加企业员工验证

### 3. 依赖更新

添加新的依赖包：
- `tenacity==8.2.3` - 重试机制
- `structlog==24.1.0` - 结构化日志

## 配置说明

### 环境变量

需要在 `.env` 文件中配置以下变量：

```bash
# Azure OpenAI (GPT-5.1)
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_CHAT_DEPLOYMENT=gpt-5.1
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# 钉钉
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
```

### Azure OpenAI 部署要求

1. 在Azure OpenAI资源中创建以下部署：
   - **聊天模型**: 部署名称为 `gpt-5.1`，使用 GPT-5.1 模型
   - **嵌入模型**: 部署名称为 `text-embedding-3-large`

2. 确保API版本设置为 `2024-12-01-preview`

### 钉钉应用配置

1. 在钉钉开放平台创建应用
2. 配置回调地址白名单：`https://cf.rocktor.shop`
3. 获取 AppKey 和 AppSecret
4. 确保应用有以下权限：
   - 获取用户个人信息
   - 通过unionId获取用户信息

## 部署步骤

1. **更新环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填写正确的配置
   ```

2. **重新构建并启动**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. **验证部署**
   ```bash
   # 检查服务状态
   docker-compose ps

   # 查看日志
   docker-compose logs -f backend
   ```

## 测试验证

### 1. GPT-5.1 测试
- 发送聊天消息
- 验证响应质量
- 检查日志中的模型名称

### 2. 钉钉登录测试
- 生成二维码
- 使用钉钉扫码
- 验证登录成功
- 检查会话有效期（180天）

## 注意事项

1. **API版本**: GPT-5.1 必须使用 `2024-12-01-preview` 版本
2. **参数名称**: 使用 `max_completion_tokens` 而不是 `max_tokens`
3. **钉钉API**: 新版API使用不同的endpoint和认证方式
4. **会话管理**: 会话有效期为180天，需要定期清理过期会话
5. **日志记录**: 使用 structlog 进行结构化日志记录

## 性能优化

1. **重试机制**: 使用 tenacity 实现自动重试
2. **超时设置**: HTTP请求设置30秒超时
3. **Token限制**: GPT-5.1 支持最大64K输出
4. **日志优化**: 使用结构化日志便于分析

## 故障排查

### GPT-5.1 调用失败
- 检查API版本是否为 `2024-12-01-preview`
- 确认部署名称为 `gpt-5.1`
- 验证API密钥和endpoint正确

### 钉钉登录失败
- 检查AppKey和AppSecret
- 确认回调地址已配置
- 查看日志中的详细错误信息
- 验证用户是否为企业员工

## 参考项目

- **JuniorDao**: `/home/ubuntu/ClaudeCode/JuniorDao`
  - GPT-5.1 调用实现
  - 重试机制
  - 结构化日志

- **dingtalk-bot-new**: `/home/ubuntu/ClaudeCode/dingtalk-bot-new`
  - 钉钉新版API实现
  - 三步认证流程
  - 会话管理

## 更新日期

2026-01-20
