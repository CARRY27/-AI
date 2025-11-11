"""
审核相关 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.review import MessageReview, ReviewStatus, ReviewType, SensitiveWordLog
from app.api.auth import get_current_active_user

router = APIRouter()


# ========== Schemas ==========

class ReviewCreate(BaseModel):
    message_id: int
    status: str
    review_type: Optional[str] = None
    comment: Optional[str] = None
    suggestion: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    message_id: int
    reviewer_id: int
    status: str
    review_type: Optional[str]
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SensitiveLogResponse(BaseModel):
    id: int
    content_type: str
    detected_words: str
    risk_level: str
    is_blocked: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class QualityReportResponse(BaseModel):
    total_messages: int
    reviewed_messages: int
    approved_count: int
    rejected_count: int
    flagged_count: int
    avg_confidence: float
    sensitive_detections: int


# ========== 依赖项 ==========

async def require_auditor(current_user: User = Depends(get_current_active_user)) -> User:
    """要求审核员权限"""
    if current_user.role not in ["admin", "auditor", "superuser"]:
        raise HTTPException(status_code=403, detail="需要审核员权限")
    return current_user


# ========== API 端点 ==========

@router.post("/messages", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def review_message(
    data: ReviewCreate,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """审核消息"""
    
    # 验证消息存在
    result = await db.execute(
        select(Message).where(Message.id == data.message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 创建审核记录
    review = MessageReview(
        message_id=data.message_id,
        reviewer_id=current_user.id,
        status=ReviewStatus(data.status),
        review_type=ReviewType(data.review_type) if data.review_type else None,
        comment=data.comment,
        suggestion=data.suggestion
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    return review


@router.get("/messages/{message_id}", response_model=List[ReviewResponse])
async def get_message_reviews(
    message_id: int,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """获取消息的审核记录"""
    
    result = await db.execute(
        select(MessageReview).where(
            MessageReview.message_id == message_id
        ).order_by(desc(MessageReview.created_at))
    )
    reviews = result.scalars().all()
    
    return reviews


@router.get("/pending", response_model=List[dict])
async def get_pending_reviews(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """获取待审核的消息列表"""
    
    # 查找还没有审核记录的助手消息
    result = await db.execute(
        select(Message).outerjoin(MessageReview).where(
            Message.role == "assistant",
            MessageReview.id.is_(None)
        ).order_by(desc(Message.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    messages = result.scalars().all()
    
    return [
        {
            "message_id": msg.id,
            "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
            "created_at": msg.created_at,
            "conversation_id": msg.conversation_id
        }
        for msg in messages
    ]


@router.get("/sensitive-logs", response_model=List[SensitiveLogResponse])
async def get_sensitive_logs(
    page: int = 1,
    page_size: int = 20,
    unhandled_only: bool = False,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """获取敏感词检测日志"""
    
    query = select(SensitiveWordLog)
    
    if unhandled_only:
        query = query.where(SensitiveWordLog.handled == False)
    
    query = query.order_by(desc(SensitiveWordLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs


@router.post("/sensitive-logs/{log_id}/handle")
async def handle_sensitive_log(
    log_id: int,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """处理敏感词检测日志"""
    
    result = await db.execute(
        select(SensitiveWordLog).where(SensitiveWordLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    log.handled = True
    log.handler_id = current_user.id
    log.handled_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "已标记为已处理"}


@router.get("/quality-report", response_model=QualityReportResponse)
async def get_quality_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db)
):
    """获取AI输出质量报告"""
    
    # 统计总消息数
    result = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.role == "assistant"
        )
    )
    total_messages = result.scalar()
    
    # 统计已审核消息数
    result = await db.execute(
        select(func.count(func.distinct(MessageReview.message_id))).select_from(MessageReview)
    )
    reviewed_messages = result.scalar()
    
    # 统计各状态数量
    result = await db.execute(
        select(MessageReview.status, func.count()).group_by(MessageReview.status)
    )
    status_counts = dict(result.all())
    
    approved_count = status_counts.get(ReviewStatus.APPROVED, 0)
    rejected_count = status_counts.get(ReviewStatus.REJECTED, 0)
    flagged_count = status_counts.get(ReviewStatus.FLAGGED, 0)
    
    # 计算平均置信度（简化，实际需要从message metadata中获取）
    avg_confidence = 0.85  # 示例值
    
    # 敏感内容检测数量
    result = await db.execute(
        select(func.count()).select_from(SensitiveWordLog)
    )
    sensitive_detections = result.scalar()
    
    return {
        "total_messages": total_messages,
        "reviewed_messages": reviewed_messages,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "flagged_count": flagged_count,
        "avg_confidence": avg_confidence,
        "sensitive_detections": sensitive_detections
    }

