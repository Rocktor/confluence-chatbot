#!/bin/bash

# 验证配置更新脚本

echo "==================================="
echo "Confluence Chatbot 配置验证"
echo "==================================="
echo ""

# 检查.env文件
echo "1. 检查环境变量配置..."
if [ ! -f .env ]; then
    echo "   ✗ .env 文件不存在"
    echo "   请复制 .env.example 并配置："
    echo "   cp .env.example .env"
    exit 1
fi

# 检查关键配置
echo "   检查 Azure OpenAI 配置..."
if grep -q "AZURE_OPENAI_API_VERSION=2024-12-01-preview" .env; then
    echo "   ✓ API版本配置正确 (2024-12-01-preview)"
else
    echo "   ✗ API版本未配置或不正确"
    echo "   应该设置为: AZURE_OPENAI_API_VERSION=2024-12-01-preview"
fi

if grep -q "AZURE_CHAT_DEPLOYMENT=gpt-5.1" .env; then
    echo "   ✓ 聊天模型配置正确 (gpt-5.1)"
else
    echo "   ✗ 聊天模型未配置或不正确"
    echo "   应该设置为: AZURE_CHAT_DEPLOYMENT=gpt-5.1"
fi

echo ""
echo "2. 检查代码更新..."

# 检查azure_openai_service.py
if grep -q "max_completion_tokens" backend/app/services/azure_openai_service.py; then
    echo "   ✓ Azure OpenAI服务已更新 (使用max_completion_tokens)"
else
    echo "   ✗ Azure OpenAI服务未更新"
fi

# 检查dingtalk_service.py
if grep -q "api.dingtalk.com/v1.0/oauth2/userAccessToken" backend/app/services/dingtalk_service.py; then
    echo "   ✓ 钉钉服务已更新 (使用新版API)"
else
    echo "   ✗ 钉钉服务未更新"
fi

# 检查requirements.txt
if grep -q "tenacity" backend/requirements.txt; then
    echo "   ✓ 依赖包已更新 (包含tenacity)"
else
    echo "   ✗ 依赖包未更新"
fi

if grep -q "structlog" backend/requirements.txt; then
    echo "   ✓ 依赖包已更新 (包含structlog)"
else
    echo "   ✗ 依赖包未更新"
fi

echo ""
echo "3. 检查配置文件..."

# 检查config.py
if grep -q "AZURE_OPENAI_API_VERSION" backend/app/config.py; then
    echo "   ✓ 配置文件已更新"
else
    echo "   ✗ 配置文件未更新"
fi

echo ""
echo "==================================="
echo "验证完成"
echo "==================================="
echo ""
echo "如果所有检查都通过，可以运行："
echo "  docker-compose up -d --build"
echo ""
