# DocAgent 🚀

<div align="center">

**基于 RAG 技术的企业级文档问答系统**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3.8-4FC08D.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**让 AI 读懂您的所有企业文档，像资深员工一样回答问题**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [贡献指南](#-贡献指南)

</div>

---

## 📖 项目简介

**DocAgent** 是一个基于 RAG (检索增强生成) 技术的企业级文档问答系统。它能够理解企业内部的各种文档（PDF、Word、Excel、PPT等），并像资深员工一样回答相关问题，所有回答都有明确的文档来源依据。

### ✨ 核心价值

- 🎯 **精准回答，有出处** - 所有回答都有明确的文档来源和页码引用
- 🧠 **智能检索** - 基于向量检索技术，快速找到最相关的文档片段
- 🔄 **自动更新** - 支持文档版本控制和增量更新，知识库持续更新
- 🔐 **安全可控** - 支持私有化部署，企业数据不出内网
- 📊 **可审计** - 完整的对话记录、审核日志和敏感内容检测

---

## ✨ 功能特性

### 🎯 核心能力

- ✅ **多格式文档支持** - PDF、Word、Excel、PPT、TXT、Markdown、HTML
- ✅ **RAG 问答** - 智能检索生成，带来源引用
- ✅ **多模型支持** - 通义千问、OpenAI GPT-4、Ollama（本地模型）
- ✅ **智能模型调度** - 自动降级和限流
- ✅ **文档版本控制** - 增量更新，自动刷新
- ✅ **角色权限控制** - 多租户支持，组织隔离
- ✅ **内容安全** - 敏感词检测和内容审核
- ✅ **用户反馈系统** - 评分和反馈收集
- ✅ **管理仪表盘** - 全面的统计和监控
- ✅ **Prompt 模板管理** - 可自定义不同场景的提示词
- ✅ **流式响应** - 实时流式输出
- ✅ **导出功能** - 支持 Markdown/PDF 导出对话

### 🏗️ 架构亮点

- **异步处理** - Celery 后台任务
- **缓存层** - Redis 缓存，降低 API 成本 30%+
- **向量数据库** - FAISS 快速相似度搜索
- **对象存储** - MinIO 文档存储
- **任务队列** - Celery + Celery Beat 定时任务

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI 0.121.1
- **数据库**: PostgreSQL (SQLAlchemy 2.0)
- **缓存**: Redis
- **任务队列**: Celery + Celery Beat
- **向量数据库**: FAISS
- **对象存储**: MinIO
- **AI 模型**: 
  - 通义千问 (DashScope) - 已配置并优先使用
  - OpenAI GPT-4
  - Ollama (本地模型)

### 前端
- **框架**: Vue 3
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **图表**: ECharts
- **构建工具**: Vite

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 16+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (可选)

### 安装

#### 方式一：Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/CARRY27/-AI.git
cd docagent

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 设置您的 API 密钥

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:5173
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

#### 方式二：手动安装

**后端：**

```bash
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动后端
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

**Celery Worker：**

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

**Celery Beat：**

```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

### 配置

创建 `backend/.env` 文件：

```env
# LLM 配置
TONGYI_API_KEY=sk-your-api-key
TONGYI_MODEL=qwen-turbo
LLM_PROVIDER=tongyi

# 数据库
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=docagent
POSTGRES_USER=docagent
POSTGRES_PASSWORD=docagent_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=docagent-files
```

---

## 📚 文档

- [完整文档](项目总结文档.md)
- [API 文档](http://localhost:8000/docs) - 交互式 API 文档
- [实现细节](backend/README_IMPLEMENTATION.md)

---

## 🎯 使用场景

- **企业知识库** - 内部文档问答系统
- **客户服务** - 基于政策文档的自动客服
- **培训入职** - 新员工快速问答
- **法务合规** - 文档查询和案例查找
- **技术支持** - 技术文档问答

---

## 📊 项目结构

```
docagent/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   ├── services/   # 业务逻辑
│   │   ├── tasks/       # 异步任务
│   │   └── main.py      # 应用入口
│   └── requirements.txt
├── frontend/            # 前端服务
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── services/    # API 服务
│   │   └── ...
│   └── package.json
├── docker-compose.yml    # Docker 编排
└── README.md
```

---

## 🔌 API 示例

### 创建对话

```bash
curl -X POST "http://localhost:8000/api/conversations/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "产品政策问题"}'
```

### 发送消息

```bash
curl -X POST "http://localhost:8000/api/conversations/1/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "退货政策是什么？"}'
```

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/files/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

查看 [API 文档](http://localhost:8000/docs) 获取完整 API 参考。

---

## 🧪 测试

```bash
cd backend
pytest tests/
```

---

## 🤝 贡献指南

我们欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 如何贡献

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

---

## 📈 路线图

### 短期（1-2个月）
- [ ] 文档级权限控制
- [ ] 前端交互增强（点击查看来源）
- [ ] OCR 支持（扫描件识别）
- [ ] 审核仪表盘 UI 优化

### 中期（3-6个月）
- [ ] 数据源集成（钉钉、企微、飞书、ERP、CRM）
- [ ] 角色化语气调整
- [ ] 快捷操作（自动生成回复、创建工单）
- [ ] 知识图谱增强

### 长期（6-12个月）
- [ ] 多模态支持（图片/视频理解）
- [ ] Kubernetes 部署配置
- [ ] 数据加密和 PII 脱敏
- [ ] LLM Agent 扩展

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [FAISS](https://github.com/facebookresearch/faiss) - 向量相似度搜索
- [DashScope](https://dashscope.aliyun.com/) - 通义千问 API

---

## 📞 联系方式与支持

- 🐛 [报告 Bug](https://github.com/CARRY27/-AI/issues)
- 💡 [功能建议](https://github.com/CARRY27/-AI/issues)
- 📧 邮箱: carry27@example.com

---

## ⭐ Star 历史

如果您觉得这个项目有帮助，请考虑给它一个 Star！⭐

---

<div align="center">

**由 DocAgent 团队用 ❤️ 制作**

[⬆ 返回顶部](#-docagent)

</div>

