# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- RAG-based document Q&A system
- Multi-model support (Tongyi Qwen, OpenAI, Ollama)
- Document version control and incremental updates
- Role-based access control
- Content security and review system
- Admin dashboard
- User feedback system
- Prompt template management
- Streaming responses
- Export functionality

### Changed
- Upgraded FastAPI to 0.121.1 for better compatibility

### Fixed
- Fixed Pydantic regex parameter compatibility issue
- Fixed database connection configuration

## [1.0.0] - 2024-XX-XX

### Added
- Initial release
- Core RAG functionality
- Multi-format document support (PDF, Word, Excel, PPT, TXT, Markdown, HTML)
- Vector search with FAISS
- Model orchestrator with fallback mechanism
- Celery async task processing
- Redis caching layer
- MinIO object storage
- PostgreSQL database
- Vue 3 frontend
- Docker Compose deployment
- API documentation
- User authentication and authorization
- Organization multi-tenant support
- Sensitive content detection
- Content review system
- Admin dashboard with statistics
- Prompt template management
- Conversation export (Markdown/PDF)
- Streaming responses
- User feedback system

### Security
- JWT authentication
- Role-based access control
- Sensitive word detection
- Content review workflow
- Audit logging

---

## Version History

- **1.0.0** - Initial release with core features

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes

