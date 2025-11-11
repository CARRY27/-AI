"""
用户反馈 API
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.feedback import MessageFeedback, FeedbackStats
from app.api.auth import get_current_active_user


router = APIRouter(prefix="/feedback", tags=["反馈"])


# ========== Pydantic 模型 ==========

class FeedbackCreate(BaseModel):
    """创建反馈"""
    feedback_type: str = Field(..., description="反馈类型: positive 或 negative")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(None, description="文字反馈")
    issue_tags: List[str] = Field(default=[], description="问题标签")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: int
    message_id: int
    feedback_type: str
    rating: Optional[int]
    comment: Optional[str]
    issue_tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackStatsResponse(BaseModel):
    """反馈统计响应"""
    total_feedbacks: int
    positive_count: int
    negative_count: int
    satisfaction_rate: float
    average_rating: float
    issue_tag_counts: dict


# ========== API 端点 ==========

@router.post("/messages/{message_id}", response_model=FeedbackResponse)
async def create_feedback(
    message_id: int,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为消息创建反馈
    """
    # 验证消息是否存在
    result = await db.execute(select(Message).filter(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 检查是否已经反馈过
    result = await db.execute(
        select(MessageFeedback).filter(
            and_(
                MessageFeedback.message_id == message_id,
                MessageFeedback.user_id == current_user.id
            )
        )
    )
    existing_feedback = result.scalar_one_or_none()
    
    if existing_feedback:
        # 更新现有反馈
        existing_feedback.feedback_type = feedback_data.feedback_type
        existing_feedback.rating = feedback_data.rating
        existing_feedback.comment = feedback_data.comment
        existing_feedback.issue_tags = feedback_data.issue_tags
        existing_feedback.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(existing_feedback)
        return existing_feedback
    
    # 创建新反馈
    new_feedback = MessageFeedback(
        message_id=message_id,
        user_id=current_user.id,
        feedback_type=feedback_data.feedback_type,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
        issue_tags=feedback_data.issue_tags
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    return new_feedback


@router.get("/messages/{message_id}", response_model=Optional[FeedbackResponse])
async def get_message_feedback(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户对某条消息的反馈
    """
    result = await db.execute(
        select(MessageFeedback).filter(
            and_(
                MessageFeedback.message_id == message_id,
                MessageFeedback.user_id == current_user.id
            )
        )
    )
    feedback = result.scalar_one_or_none()
    
    return feedback


@router.delete("/messages/{message_id}")
async def delete_feedback(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除反馈
    """
    result = await db.execute(
        select(MessageFeedback).filter(
            and_(
                MessageFeedback.message_id == message_id,
                MessageFeedback.user_id == current_user.id
            )
        )
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    await db.delete(feedback)
    await db.commit()
    
    return {"message": "反馈已删除"}


@router.get("/stats/org", response_model=FeedbackStatsResponse)
async def get_org_feedback_stats(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取组织的反馈统计（最近N天）
    """
    from app.models.conversation import Conversation
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询反馈统计 - 通过 Conversation 关联获取 org_id
    query = (
        select(MessageFeedback)
        .join(Message, MessageFeedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            MessageFeedback.created_at >= start_date,
            Conversation.org_id == current_user.org_id
        )
    )
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    # 计算统计指标
    total = len(feedbacks)
    positive = sum(1 for f in feedbacks if f.feedback_type == "positive")
    negative = sum(1 for f in feedbacks if f.feedback_type == "negative")
    
    satisfaction_rate = positive / total if total > 0 else 0.0
    
    # 计算平均评分
    ratings = [f.rating for f in feedbacks if f.rating is not None]
    average_rating = sum(ratings) / len(ratings) if ratings else 0.0
    
    # 统计问题标签
    issue_tag_counts = {}
    for feedback in feedbacks:
        if feedback.issue_tags:
            for tag in feedback.issue_tags:
                issue_tag_counts[tag] = issue_tag_counts.get(tag, 0) + 1
    
    return {
        "total_feedbacks": total,
        "positive_count": positive,
        "negative_count": negative,
        "satisfaction_rate": round(satisfaction_rate, 2),
        "average_rating": round(average_rating, 2),
        "issue_tag_counts": issue_tag_counts
    }


@router.get("/stats/daily")
async def get_daily_feedback_stats(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日反馈趋势
    """
    from app.models.conversation import Conversation
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 简化版本：获取所有反馈，然后在Python中分组
    query = (
        select(MessageFeedback)
        .join(Message, MessageFeedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            and_(
                MessageFeedback.created_at >= start_date,
                Conversation.org_id == current_user.org_id
            )
        )
        .order_by(MessageFeedback.created_at)
    )
    
    result_set = await db.execute(query)
    feedbacks = result_set.scalars().all()
    
    # 在Python中进行分组统计
    daily_data = {}
    for feedback in feedbacks:
        date_str = feedback.created_at.date().isoformat()
        if date_str not in daily_data:
            daily_data[date_str] = {"positive": 0, "negative": 0, "total": 0}
        
        daily_data[date_str]["total"] += 1
        if feedback.feedback_type == "positive":
            daily_data[date_str]["positive"] += 1
        else:
            daily_data[date_str]["negative"] += 1
    
    # 格式化返回
    result = []
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        satisfaction = data["positive"] / data["total"] if data["total"] > 0 else 0
        result.append({
            "date": date_str,
            "total": data["total"],
            "positive": data["positive"],
            "negative": data["negative"],
            "satisfaction_rate": round(satisfaction, 2)
        })
    
    return result


@router.get("/negative/recent")
async def get_recent_negative_feedback(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的负面反馈（用于改进）
    """
    from app.models.conversation import Conversation
    from sqlalchemy.orm import selectinload
    
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="需要管理员或审核员权限")
    
    query = (
        select(MessageFeedback)
        .join(Message, MessageFeedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .options(selectinload(MessageFeedback.message))
        .filter(
            and_(
                MessageFeedback.feedback_type == "negative",
                Conversation.org_id == current_user.org_id,
                MessageFeedback.is_resolved == False
            )
        )
        .order_by(MessageFeedback.created_at.desc())
        .limit(limit)
    )
    
    result_set = await db.execute(query)
    feedbacks = result_set.scalars().all()
    
    result = []
    for feedback in feedbacks:
        message = feedback.message
        result.append({
            "id": feedback.id,
            "message_id": message.id,
            "question": "",  # 简化：需要额外查询
            "answer": message.content[:200] + "..." if len(message.content) > 200 else message.content,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "issue_tags": feedback.issue_tags,
            "created_at": feedback.created_at.isoformat()
        })
    
    return result


@router.patch("/negative/{feedback_id}/resolve")
async def resolve_negative_feedback(
    feedback_id: int,
    resolution_note: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记负面反馈为已处理
    """
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="需要管理员或审核员权限")
    
    result = await db.execute(
        select(MessageFeedback).filter(MessageFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    feedback.is_resolved = True
    feedback.resolution_note = resolution_note
    feedback.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "已标记为已处理"}

