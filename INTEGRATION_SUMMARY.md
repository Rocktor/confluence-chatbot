# Confluence Chatbot 集成总结

## 已完成的集成

### ✅ 1. GPT-5.1 集成（参考 JuniorDao）

#### 关键更新
- **API版本**: `2024-12-01-preview`
- **模型部署**: `gpt-5.1`
- **最大Token**: 65536 (64K)
- **参数更新**: `max_completion_tokens` 替代 `max_tokens`

#### 更新的文件
1. `backend/app/config.py`
   - 添加 `AZURE_OPENAI_API_VERSION` 配置
   - 更新默认部署名为 `gpt-5.1`

2. `backend/app/services/azure_openai_service.py`
   - 使用 `settings.AZURE_OPENAI_API_VERSION`
   - 设置 `max_completion_tokens = 65536`
   - 添加 `@retry` 装饰器（tenacity）
   - 所有API调用使用 `max_completion_tokens`

3. `backend/requirements.txt`
   - 添加 `tenacity==8.2.3`
   - 添加 `structlog==24.1.0`

4. `.env.example`
   - 添加 `AZURE_OPENAI_API_VERSION=2024-12-01-preview`
   - 更新 `AZURE_CHAT_DEPLOYMENT=gpt-5.1`

### ✅ 2. 钉钉新版API集成（参考 dingtalk-bot-new）

#### 三步认证流程
1. **获取用户Token**: `POST /v1.0/oauth2/userAccessToken`
   - 使用 authCode 换取 accessToken
   
2. **获取用户信息**: `GET /v1.0/contact/users/me`
   - 使用 accessToken 获取 unionId
   
3. **查询企业用户**: `POST /topapi/user/getbyunionid`
   - 使用 unionId 获取企业 userid

#### 更新的文件
1. `backend/app/services/dingtalk_service.py`
   - 添加 `new_api_base = "https://api.dingtalk.com"`
   - 实现三步认证流程
   - 添加 structlog 日志记录
   - 设置30秒超时

2. `backend/app/services/auth_service.py`
   - 更新 `process_qrcode_callback` 方法
   - 会话有效期设置为180天
   - 添加企业员工验证逻辑

## 配置要求

### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=<your_key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_CHAT_DEPLOYMENT=gpt-5.1
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

### 钉钉
```bash
DINGTALK_APP_KEY=<your_app_key>
DINGTALK_APP_SECRET=<your_app_secret>
```

## 部署步骤

1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

2. **验证配置**
   ```bash
   ./verify-update.sh
   ```

3. **构建并启动**
   ```bash
   docker-compose up -d --build
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f backend
   ```

## 验证测试

### GPT-5.1 测试
```bash
# 检查日志中的模型信息
docker-compose logs backend | grep "gpt-5.1"

# 测试聊天功能
# 访问 https://cf.rocktor.shop/chat
# 发送消息并验证响应
```

### 钉钉登录测试
```bash
# 检查日志中的认证流程
docker-compose logs backend | grep "dingtalk"

# 测试登录流程
# 1. 访问 https://cf.rocktor.shop/login
# 2. 扫描二维码
# 3. 验证登录成功
```

## 关键改进

### 性能优化
- ✅ 自动重试机制（最多3次）
- ✅ 指数退避策略
- ✅ 30秒HTTP超时
- ✅ 64K输出Token支持

### 安全增强
- ✅ 企业员工验证
- ✅ 180天会话有效期
- ✅ 结构化日志记录
- ✅ 详细错误处理

### 代码质量
- ✅ 使用最新API版本
- ✅ 遵循最佳实践
- ✅ 完整的错误处理
- ✅ 详细的日志记录

## 参考项目

- **JuniorDao**: `/home/ubuntu/ClaudeCode/JuniorDao`
  - `backend/app/core/llm.py` - GPT-5.1实现
  - `backend/app/config.py` - 配置管理

- **dingtalk-bot-new**: `/home/ubuntu/ClaudeCode/dingtalk-bot-new`
  - `src/services/qrcodeAuth.js` - 钉钉认证实现

## 注意事项

1. **API版本**: 必须使用 `2024-12-01-preview`
2. **参数名称**: 使用 `max_completion_tokens` 而非 `max_tokens`
3. **钉钉API**: 使用新版OAuth2.0 API
4. **会话管理**: 180天有效期，需定期清理
5. **日志记录**: 使用structlog进行结构化日志

## 故障排查

### GPT-5.1问题
- 检查API版本是否正确
- 确认部署名称为 `gpt-5.1`
- 验证endpoint和API key

### 钉钉登录问题
- 检查AppKey和AppSecret
- 确认回调地址已配置
- 查看structlog日志
- 验证用户是否为企业员工

## 更新完成

所有代码已更新并准备部署！

**更新日期**: 2026-01-20
**版本**: v1.1.0
