#!/bin/bash

# Confluence Chatbot 部署脚本

set -e

echo "==================================="
echo "Confluence Chatbot 部署脚本"
echo "==================================="

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "错误: .env 文件不存在"
    echo "请复制 .env.example 并填写配置："
    echo "  cp .env.example .env"
    exit 1
fi

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

echo "✓ 环境检查通过"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p nginx/ssl
mkdir -p postgres_data
mkdir -p redis_data

# 构建并启动服务
echo "构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo ""
echo "==================================="
echo "部署完成！"
echo "==================================="
echo ""
echo "访问地址："
echo "  - 应用: https://cf.rocktor.shop"
echo "  - API文档: https://cf.rocktor.shop/api/docs"
echo ""
echo "查看日志："
echo "  docker-compose logs -f"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""
