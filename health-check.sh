#!/bin/bash

# 健康检查脚本

echo "==================================="
echo "Confluence Chatbot 健康检查"
echo "==================================="
echo ""

# 检查Docker服务
echo "1. 检查Docker服务状态..."
if docker-compose ps | grep -q "Up"; then
    echo "   ✓ Docker服务运行正常"
else
    echo "   ✗ Docker服务异常"
    exit 1
fi
echo ""

# 检查PostgreSQL
echo "2. 检查PostgreSQL..."
if docker-compose exec -T postgres pg_isready -U cfbot > /dev/null 2>&1; then
    echo "   ✓ PostgreSQL运行正常"
else
    echo "   ✗ PostgreSQL连接失败"
fi
echo ""

# 检查Redis
echo "3. 检查Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "   ✓ Redis运行正常"
else
    echo "   ✗ Redis连接失败"
fi
echo ""

# 检查后端API
echo "4. 检查后端API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ 后端API运行正常"
else
    echo "   ✗ 后端API无响应"
fi
echo ""

# 检查Nginx
echo "5. 检查Nginx..."
if docker-compose ps nginx | grep -q "Up"; then
    echo "   ✓ Nginx运行正常"
else
    echo "   ✗ Nginx异常"
fi
echo ""

# 显示资源使用
echo "6. 资源使用情况..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

echo "==================================="
echo "健康检查完成"
echo "==================================="
