#!/bin/bash

# DocAgent 快速启动脚本

set -e

echo "========================================"
echo "  DocAgent - 企业级文档问答系统"
echo "========================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "📋 未找到 .env 文件，正在创建..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，至少需要配置 OPENAI_API_KEY"
    echo "   然后重新运行此脚本"
    exit 1
fi

# 检查关键配置
if grep -q "sk-your-openai-api-key-here" .env; then
    echo "⚠️  请先在 .env 文件中配置 OPENAI_API_KEY"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p backend/data/faiss_index

# 启动服务
echo ""
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
echo "========================================"
echo "✅ 启动完成！"
echo "========================================"
echo ""
echo "访问地址："
echo "  前端:        http://localhost:5173"
echo "  后端 API:    http://localhost:8000"
echo "  API 文档:    http://localhost:8000/docs"
echo "  MinIO 控制台: http://localhost:9001"
echo ""
echo "默认 MinIO 凭据："
echo "  用户名: minioadmin"
echo "  密码:   minioadmin"
echo ""
echo "查看日志："
echo "  docker-compose logs -f"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""

