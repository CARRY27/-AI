.PHONY: help start stop restart logs clean test lint format

help: ## 显示帮助信息
	@echo "DocAgent - 可用命令："
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

start: ## 启动所有服务
	@echo "🚀 启动 DocAgent..."
	docker-compose up -d
	@echo "✅ 服务已启动"
	@echo "   前端: http://localhost:5173"
	@echo "   后端: http://localhost:8000"
	@echo "   文档: http://localhost:8000/docs"

stop: ## 停止所有服务
	@echo "🛑 停止 DocAgent..."
	docker-compose down
	@echo "✅ 服务已停止"

restart: ## 重启所有服务
	@echo "🔄 重启 DocAgent..."
	docker-compose restart
	@echo "✅ 服务已重启"

logs: ## 查看日志
	docker-compose logs -f

logs-backend: ## 查看后端日志
	docker-compose logs -f backend

logs-worker: ## 查看 Worker 日志
	docker-compose logs -f celery-worker

logs-frontend: ## 查看前端日志
	docker-compose logs -f frontend

ps: ## 查看服务状态
	docker-compose ps

build: ## 重新构建镜像
	@echo "🔨 构建镜像..."
	docker-compose build
	@echo "✅ 构建完成"

rebuild: ## 完全重建并启动
	@echo "🔨 完全重建..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ 重建完成"

clean: ## 清理所有容器和卷（警告：会删除数据）
	@echo "⚠️  这将删除所有容器、卷和数据！"
	@read -p "确认继续？(y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	@echo "✅ 清理完成"

test: ## 运行测试
	@echo "🧪 运行测试..."
	docker-compose exec backend pytest
	@echo "✅ 测试完成"

lint: ## 代码检查
	@echo "🔍 检查后端代码..."
	docker-compose exec backend flake8 app/
	@echo "🔍 检查前端代码..."
	docker-compose exec frontend npm run lint
	@echo "✅ 检查完成"

format: ## 格式化代码
	@echo "✨ 格式化后端代码..."
	docker-compose exec backend black app/
	@echo "✨ 格式化前端代码..."
	docker-compose exec frontend npm run format
	@echo "✅ 格式化完成"

shell-backend: ## 进入后端容器 Shell
	docker-compose exec backend bash

shell-db: ## 进入数据库容器
	docker-compose exec postgres psql -U docagent -d docagent

backup: ## 备份数据库
	@echo "💾 备份数据库..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U docagent docagent > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ 备份完成"

restore: ## 恢复数据库（需要指定文件：make restore FILE=backup.sql）
	@if [ -z "$(FILE)" ]; then echo "❌ 请指定备份文件：make restore FILE=backup.sql"; exit 1; fi
	@echo "📥 恢复数据库..."
	cat $(FILE) | docker-compose exec -T postgres psql -U docagent -d docagent
	@echo "✅ 恢复完成"

init: ## 初始化项目（首次运行）
	@echo "🎯 初始化 DocAgent..."
	@if [ ! -f .env ]; then \
		echo "📝 创建 .env 文件..."; \
		cp .env.example .env; \
		echo "⚠️  请编辑 .env 文件，配置 OPENAI_API_KEY 等信息"; \
		exit 1; \
	fi
	@echo "📁 创建数据目录..."
	@mkdir -p backend/data/faiss_index
	@echo "🚀 启动服务..."
	$(MAKE) start
	@echo "✅ 初始化完成"
	@echo ""
	@echo "🎉 DocAgent 已启动！"
	@echo "   访问: http://localhost:5173"

update: ## 更新代码并重启
	@echo "📥 拉取最新代码..."
	git pull
	@echo "🔨 重新构建..."
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "✅ 更新完成"

monitor: ## 查看资源使用情况
	@echo "📊 资源使用情况："
	@echo ""
	docker stats --no-stream

health: ## 健康检查
	@echo "🏥 健康检查..."
	@curl -sf http://localhost:8000/health > /dev/null && echo "✅ 后端健康" || echo "❌ 后端异常"
	@curl -sf http://localhost:5173 > /dev/null && echo "✅ 前端健康" || echo "❌ 前端异常"

