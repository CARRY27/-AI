# DocAgent 🚀

<div align="center">

**Enterprise Document Q&A System powered by RAG Technology**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3.8-4FC08D.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[![GitHub stars](https://img.shields.io/github/stars/CARRY27/-AI?style=social)](https://github.com/CARRY27/-AI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/CARRY27/-AI?style=social)](https://github.com/CARRY27/-AI/network/members)
[![GitHub issues](https://img.shields.io/github/issues/CARRY27/-AI)](https://github.com/CARRY27/-AI/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/CARRY27/-AI)](https://github.com/CARRY27/-AI/commits)

[English](#-docagent) | [中文](#-docagent-中文)

**Let AI read all your enterprise documents and answer questions like a senior employee**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

**DocAgent** is an enterprise-grade document Q&A system based on RAG (Retrieval Augmented Generation) technology. It can understand various enterprise documents (PDF, Word, Excel, PPT, etc.) and answer questions like a senior employee, with all answers backed by clear document sources and page references.

### ✨ Core Values

- 🎯 **Accurate Answers with Sources** - Every answer includes document sources and page references
- 🧠 **Intelligent Retrieval** - Fast vector-based retrieval to find the most relevant document fragments
- 🔄 **Auto-Update** - Document version control and incremental updates keep knowledge base current
- 🔐 **Secure & Private** - Supports private deployment, enterprise data stays within your network
- 📊 **Auditable** - Complete conversation logs, review logs, and sensitive content detection

---

## ✨ Features

### 🎯 Core Capabilities

- ✅ **Multi-format Document Support** - PDF, Word, Excel, PPT, TXT, Markdown, HTML
- ✅ **RAG-based Q&A** - Intelligent retrieval and generation with source citations
- ✅ **Multi-model Support** - Tongyi Qwen, OpenAI GPT-4, Ollama (local models)
- ✅ **Smart Model Orchestrator** - Automatic fallback and rate limiting
- ✅ **Document Version Control** - Incremental updates, automatic refresh
- ✅ **Role-based Access Control** - Multi-tenant support with organization isolation
- ✅ **Content Security** - Sensitive word detection and content review
- ✅ **User Feedback System** - Rating and feedback collection
- ✅ **Admin Dashboard** - Comprehensive statistics and monitoring
- ✅ **Prompt Template Management** - Customizable prompts for different scenarios
- ✅ **Streaming Responses** - Real-time streaming output
- ✅ **Export Functionality** - Export conversations in Markdown/PDF

### 🏗️ Architecture Highlights

- **Asynchronous Processing** - Celery for background tasks
- **Caching Layer** - Redis caching reduces API costs by 30%+
- **Vector Database** - FAISS for fast similarity search
- **Object Storage** - MinIO for document storage
- **Task Queue** - Celery + Celery Beat for scheduled tasks

---

## 🏗️ Tech Stack

### Backend
- **Framework**: FastAPI 0.121.1
- **Database**: PostgreSQL (SQLAlchemy 2.0)
- **Cache**: Redis
- **Task Queue**: Celery + Celery Beat
- **Vector DB**: FAISS
- **Object Storage**: MinIO
- **AI Models**: 
  - Tongyi Qwen (DashScope) - Configured and prioritized
  - OpenAI GPT-4
  - Ollama (local models)

### Frontend
- **Framework**: Vue 3
- **UI Components**: Element Plus
- **State Management**: Pinia
- **Router**: Vue Router
- **Charts**: ECharts
- **Build Tool**: Vite

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/CARRY27/-AI.git
cd docagent

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and set your API keys

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option 2: Manual Installation

**Backend:**

```bash
cd backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file

# Start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Celery Worker:**

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

**Celery Beat:**

```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

### Configuration

Create `backend/.env` file:

```env
# LLM Configuration
TONGYI_API_KEY=sk-your-api-key
TONGYI_MODEL=qwen-turbo
LLM_PROVIDER=tongyi

# Database
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

## 📚 Documentation

- [Full Documentation](项目总结文档.md) (Chinese)
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Implementation Details](backend/README_IMPLEMENTATION.md)

---

## 🎯 Use Cases

- **Enterprise Knowledge Base** - Internal document Q&A system
- **Customer Service** - Automated customer support with policy documents
- **Training & Onboarding** - Quick answers for new employees
- **Legal & Compliance** - Document query and case lookup
- **Technical Support** - Technical documentation Q&A

---

## 📊 Project Structure

```
docagent/
├── backend/              # Backend service
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models/      # Data models
│   │   ├── services/   # Business logic
│   │   ├── tasks/       # Async tasks
│   │   └── main.py      # Application entry
│   └── requirements.txt
├── frontend/            # Frontend service
│   ├── src/
│   │   ├── views/       # Page components
│   │   ├── services/    # API services
│   │   └── ...
│   └── package.json
├── docker-compose.yml    # Docker orchestration
└── README.md
```

---

## 🔌 API Examples

### Create a Conversation

```bash
curl -X POST "http://localhost:8000/api/conversations/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Product Policy Question"}'
```

### Send a Message

```bash
curl -X POST "http://localhost:8000/api/conversations/1/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the return policy?"}'
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/files/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

See [API Documentation](http://localhost:8000/docs) for complete API reference.

---

## 🧪 Testing

```bash
cd backend
pytest tests/
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📈 Roadmap

### Short-term (1-2 months)
- [ ] Document-level permission control
- [ ] Enhanced frontend interactions (click to view source)
- [ ] OCR support for scanned documents
- [ ] Review dashboard UI improvements

### Medium-term (3-6 months)
- [ ] Data source integration (DingTalk, WeChat Work, Feishu, ERP, CRM)
- [ ] Role-based tone adjustment
- [ ] Quick actions (auto-generate replies, create tickets)
- [ ] Knowledge graph enhancement

### Long-term (6-12 months)
- [ ] Multimodal support (image/video understanding)
- [ ] Kubernetes deployment configuration
- [ ] Data encryption and PII masking
- [ ] LLM Agent extensions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [DashScope](https://dashscope.aliyun.com/) - Tongyi Qwen API

---

## 📞 Contact & Support

- 🐛 [Report Bug](https://github.com/CARRY27/-AI/issues)
- 💡 [Request Feature](https://github.com/CARRY27/-AI/issues)
- 📧 Email: carry27@example.com

---

## ⭐ Star History

If you find this project helpful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ by the DocAgent Team**

[⬆ Back to Top](#-docagent)

</div>

---

## 📖 DocAgent (中文)

### 项目简介

**DocAgent** 是一个基于 RAG (检索增强生成) 技术的企业级文档问答系统。它能够理解企业内部的各种文档（PDF、Word、Excel、PPT等），并像资深员工一样回答相关问题，所有回答都有明确的文档来源依据。

### 核心特性

- 🎯 **精准回答，有出处** - 所有回答都有明确的文档来源和页码引用
- 🧠 **智能检索** - 基于向量检索技术，快速找到最相关的文档片段
- 🔄 **自动更新** - 支持文档版本控制和增量更新，知识库持续更新
- 🔐 **安全可控** - 支持私有化部署，企业数据不出内网
- 📊 **可审计** - 完整的对话记录、审核日志和敏感内容检测

### 快速开始

```bash
# 使用 Docker Compose
docker-compose up -d

# 或手动启动
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

### 详细文档

查看 [项目总结文档.md](项目总结文档.md) 获取完整的中文文档。

---

**Keywords**: RAG, Document Q&A, Enterprise AI, Knowledge Base, Vector Search, FastAPI, Vue.js, Tongyi Qwen, OpenAI

