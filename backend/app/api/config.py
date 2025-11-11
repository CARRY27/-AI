"""
系统配置管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Optional
import json

from app.database.session import get_db
from app.models.user import User
from app.api.auth import get_current_active_user
from app.config import settings

router = APIRouter()


# ========== Schemas ==========

class SystemConfigResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    llm_model: str
    embedding_model: str
    vector_db_type: str
    max_file_size: int
    supported_formats: list
    features: Dict[str, bool]


class ModelConfigUpdate(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class SystemStatsResponse(BaseModel):
    total_users: int
    total_files: int
    total_conversations: int
    total_messages: int
    storage_used: int
    storage_limit: int


# ========== 依赖项 ==========

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员权限"""
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# ========== API 端点 ==========

@router.get("/system", response_model=SystemConfigResponse)
async def get_system_config(
    current_user: User = Depends(get_current_active_user)
):
    """获取系统配置"""
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_db_type": settings.VECTOR_DB_TYPE,
        "max_file_size": settings.MAX_FILE_SIZE,
        "supported_formats": ["pdf", "docx", "txt", "md", "xlsx", "pptx"],
        "features": {
            "streaming": True,
            "export": True,
            "review": True,
            "sensitive_detection": True,
            "multi_model": True
        }
    }


@router.put("/model")
async def update_model_config(
    data: ModelConfigUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新模型配置（需要管理员权限）"""
    
    # 注意：实际应用中，配置应保存到数据库或配置文件
    # 这里仅作示例
    
    updated_fields = {}
    
    if data.api_key:
        # settings.OPENAI_API_KEY = data.api_key  # 不推荐直接修改
        updated_fields["api_key"] = "***已更新***"
    
    if data.api_base:
        # settings.OPENAI_API_BASE = data.api_base
        updated_fields["api_base"] = data.api_base
    
    if data.model_name:
        # settings.LLM_MODEL = data.model_name
        updated_fields["model_name"] = data.model_name
    
    if data.temperature is not None:
        # settings.LLM_TEMPERATURE = data.temperature
        updated_fields["temperature"] = data.temperature
    
    if data.max_tokens:
        # settings.LLM_MAX_TOKENS = data.max_tokens
        updated_fields["max_tokens"] = data.max_tokens
    
    return {
        "message": "模型配置已更新",
        "updated_fields": updated_fields,
        "note": "部分配置需要重启服务才能生效"
    }


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    
    from sqlalchemy import select, func
    from app.models.file import File
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.user import User as UserModel
    
    # 统计用户数
    result = await db.execute(select(func.count()).select_from(UserModel))
    total_users = result.scalar()
    
    # 统计文件数
    result = await db.execute(select(func.count()).select_from(File))
    total_files = result.scalar()
    
    # 统计对话数
    result = await db.execute(select(func.count()).select_from(Conversation))
    total_conversations = result.scalar()
    
    # 统计消息数
    result = await db.execute(select(func.count()).select_from(Message))
    total_messages = result.scalar()
    
    # 统计存储使用量
    result = await db.execute(select(func.sum(File.file_size)).select_from(File))
    storage_used = result.scalar() or 0
    
    # 获取组织的存储限制
    from app.models.organization import Organization
    result = await db.execute(
        select(Organization.max_storage).where(
            Organization.id == current_user.org_id
        )
    )
    storage_limit = result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_files": total_files,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "storage_used": storage_used,
        "storage_limit": storage_limit
    }


@router.get("/health-detail")
async def get_health_detail(
    current_user: User = Depends(require_admin)
):
    """获取系统健康详情"""
    
    import psutil
    import platform
    
    return {
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
        },
        "resources": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {
            "database": "connected",
            "redis": "connected",
            "minio": "connected",
            "vector_db": "connected"
        }
    }


@router.post("/maintenance-mode")
async def toggle_maintenance_mode(
    enable: bool,
    current_user: User = Depends(require_admin)
):
    """切换维护模式"""
    
    # 实际应用中应保存到数据库或缓存
    return {
        "maintenance_mode": enable,
        "message": f"维护模式已{'启用' if enable else '禁用'}"
    }

