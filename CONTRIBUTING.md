# Contributing to DocAgent

Thank you for your interest in contributing to DocAgent! 🎉

This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please be respectful and considerate of others.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the issue list to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **Actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Screenshots** (if applicable)
- **Error logs** (if applicable)

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) when creating an issue.

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - Why is this feature useful?
- **Proposed solution** (if you have one)
- **Alternatives considered** (if any)

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) when creating an issue.

### 🔧 Pull Requests

- Fill in the required template
- Do not include issue numbers in the PR title
- Include screenshots and animated GIFs if applicable
- Follow the Python and JavaScript styleguides
- Include thoughtfully-worded, well-structured tests
- Document new code based on the Documentation Styleguide
- End all files with a newline

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 16+
- PostgreSQL 15+
- Redis 7+
- Git

### Setup Steps

1. **Fork and Clone**

```bash
git clone https://github.com/yourusername/docagent.git
cd docagent
```

2. **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

3. **Frontend Setup**

```bash
cd frontend
npm install
```

4. **Database Setup**

```bash
# Start PostgreSQL and Redis (using Docker or locally)
docker-compose up -d postgres redis minio

# Run migrations
cd backend
alembic upgrade head
```

5. **Run Development Servers**

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Celery Worker
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

## Development Workflow

1. **Create a Branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Make Changes**

- Write clean, readable code
- Add tests for new features
- Update documentation as needed

3. **Test Your Changes**

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests (if available)
cd frontend
npm test
```

4. **Commit Your Changes**

Follow the [Commit Message Guidelines](#commit-message-guidelines).

5. **Push and Create Pull Request**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use `black` for code formatting
- Use `flake8` for linting

```bash
# Format code
black backend/app/

# Check linting
flake8 backend/app/
```

### JavaScript/Vue

- Follow [Vue.js Style Guide](https://vuejs.org/style-guide/)
- Use ESLint for linting
- Use Prettier for formatting

```bash
# Format code
npm run lint -- --fix
```

### Code Style Examples

**Good:**
```python
async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**Bad:**
```python
def get_user(id,db):
    r=db.query(User).filter(User.id==id).first()
    return r
```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(api): add document version control endpoint

Add new API endpoint for managing document versions with
incremental update support.

Closes #123
```

```
fix(rag): fix similarity threshold filtering issue

The similarity threshold was not being applied correctly
during vector search, causing irrelevant results.

Fixes #456
```

## Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add/update code comments
   - Update API documentation

2. **Add Tests**
   - Add tests for new features
   - Ensure all tests pass
   - Maintain or improve code coverage

3. **Update CHANGELOG.md**
   - Add entry describing your changes
   - Follow the existing format

4. **Request Review**
   - Assign reviewers
   - Respond to review comments
   - Make requested changes

5. **Merge**
   - Squash and merge (preferred)
   - Delete the branch after merge

## Project Structure

```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   └── tasks/        # Async tasks
└── tests/            # Test files

frontend/
├── src/
│   ├── views/        # Page components
│   ├── services/     # API services
│   └── ...
```

## Testing Guidelines

- Write unit tests for new features
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Test edge cases and error handling

## Documentation

- Use docstrings for all functions and classes
- Follow Google-style docstrings
- Update README.md for user-facing changes
- Update API documentation for endpoint changes

## Questions?

If you have questions, feel free to:
- Open an issue with the `question` label
- Contact the maintainers

Thank you for contributing to DocAgent! 🚀

