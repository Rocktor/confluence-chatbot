# Confluence Chatbot 项目检查清单

## 部署前检查

### 环境配置
- [ ] 复制 `.env.example` 到 `.env`
- [ ] 填写 `POSTGRES_PASSWORD`
- [ ] 填写 `REDIS_PASSWORD`
- [ ] 填写 `AZURE_OPENAI_API_KEY`
- [ ] 填写 `AZURE_OPENAI_ENDPOINT`
- [ ] 填写 `DINGTALK_APP_KEY`
- [ ] 填写 `DINGTALK_APP_SECRET`
- [ ] 填写 `JWT_SECRET` (至少32字符)

### SSL证书
- [ ] 获取SSL证书（Let's Encrypt）
- [ ] 复制 `fullchain.pem` 到 `nginx/ssl/`
- [ ] 复制 `privkey.pem` 到 `nginx/ssl/`

### DNS配置
- [ ] 配置域名 `cf.rocktor.shop` 指向服务器IP
- [ ] 验证DNS解析正常

### 钉钉配置
- [ ] 在钉钉开放平台创建应用
- [ ] 配置回调地址白名单
- [ ] 获取AppKey和AppSecret

## 部署步骤

- [ ] 运行 `./deploy.sh`
- [ ] 等待所有服务启动
- [ ] 检查服务状态 `docker-compose ps`
- [ ] 运行健康检查 `./health-check.sh`

## 功能测试

### 认证功能
- [ ] 访问 https://cf.rocktor.shop
- [ ] 生成登录二维码
- [ ] 使用钉钉扫码登录
- [ ] 验证登录成功

### 聊天功能
- [ ] 发送文本消息
- [ ] 验证AI回复
- [ ] 测试流式响应
- [ ] 测试多轮对话

### Confluence功能
- [ ] 配置Confluence连接
- [ ] 创建测试页面
- [ ] 同步现有页面
- [ ] 测试文档问答

## 监控检查

- [ ] 查看后端日志 `docker-compose logs backend`
- [ ] 查看前端日志 `docker-compose logs frontend`
- [ ] 查看数据库日志 `docker-compose logs postgres`
- [ ] 查看Nginx日志 `docker-compose logs nginx`

## 性能验证

- [ ] 测试登录响应时间 (< 3秒)
- [ ] 测试聊天首字延迟 (< 1秒)
- [ ] 测试向量检索速度 (< 500ms)
- [ ] 测试并发连接

## 安全检查

- [ ] HTTPS强制跳转正常
- [ ] JWT Token验证正常
- [ ] API Token加密存储
- [ ] CORS配置正确
- [ ] 防火墙规则配置

## 备份计划

- [ ] 配置数据库自动备份
- [ ] 测试数据库恢复
- [ ] 备份环境变量文件
- [ ] 备份SSL证书

## 文档检查

- [ ] README.md 完整
- [ ] QUICKSTART.md 可用
- [ ] API文档可访问
- [ ] 部署文档清晰

## 后续优化

- [ ] 配置日志聚合
- [ ] 添加监控告警
- [ ] 实现自动扩展
- [ ] 优化数据库查询
- [ ] 添加CDN加速

## 问题记录

记录部署过程中遇到的问题和解决方案：

1. 问题：
   解决：

2. 问题：
   解决：

## 完成标记

- [ ] 所有检查项通过
- [ ] 系统稳定运行24小时
- [ ] 用户验收测试通过
- [ ] 文档交接完成

---

检查人：__________
日期：__________
签名：__________
