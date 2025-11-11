"""
管理员 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Dict

from app.database.session import get_db
from app.models.user import User
from app.models.file import File
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.auth import get_current_active_user

router = APIRouter()


# ========== Schemas ==========

class SystemStats(BaseModel):
    total_users: int
    total_files: int
    total_conversations: int
    total_messages: int
    total_storage_bytes: int


class ReindexRequest(BaseModel):
    file_id: int


# ========== 依赖项 ==========

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员权限"""
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# ========== API 端点 ==========

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    
    # 统计用户数
    result = await db.execute(
        select(func.count()).select_from(User).where(User.org_id == current_user.org_id)
    )
    total_users = result.scalar()
    
    # 统计文件数
    result = await db.execute(
        select(func.count()).select_from(File).where(File.org_id == current_user.org_id)
    )
    total_files = result.scalar()
    
    # 统计对话数
    result = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.org_id == current_user.org_id)
    )
    total_conversations = result.scalar()
    
    # 统计消息数
    result = await db.execute(
        select(func.count()).select_from(Message).join(Conversation).where(
            Conversation.org_id == current_user.org_id
        )
    )
    total_messages = result.scalar()
    
    # 统计存储大小
    result = await db.execute(
        select(func.sum(File.size)).where(File.org_id == current_user.org_id)
    )
    total_storage_bytes = result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_files": total_files,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_storage_bytes": total_storage_bytes
    }


@router.post("/reindex")
async def trigger_reindex(
    data: ReindexRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """触发重新索引"""
    
    # 验证文件归属
    result = await db.execute(
        select(File).where(
            File.id == data.file_id,
            File.org_id == current_user.org_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 触发重新索引任务（通过 Celery）
    from app.tasks.document_tasks import process_document_task
    process_document_task.delay(file.id)
    
    return {"message": "重新索引任务已触发", "file_id": file.id}

