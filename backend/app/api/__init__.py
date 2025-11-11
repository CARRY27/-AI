"""
API 路由模块
"""

from fastapi import APIRouter
from app.api import auth, files, conversations, admin, review, export, streaming, config, feedback, prompt_templates, dashboard

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(files.router, prefix="/files", tags=["文件"])
router.include_router(conversations.router, prefix="/conversations", tags=["对话"])
router.include_router(feedback.router, tags=["反馈"])
router.include_router(admin.router, prefix="/admin", tags=["管理"])
router.include_router(review.router, prefix="/review", tags=["审核"])
router.include_router(export.router, prefix="/export", tags=["导出"])
router.include_router(streaming.router, prefix="/streaming", tags=["流式输出"])
router.include_router(config.router, prefix="/config", tags=["系统配置"])
router.include_router(prompt_templates.router, prefix="/prompt-templates", tags=["Prompt模板"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])

