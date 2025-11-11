"""
管理员仪表盘 API
提供关键指标统计和数据可视化
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.database.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.file import File
from app.models.feedback import MessageFeedback, FeedbackStats
from app.models.audit_log import AuditLog
from app.models.review import SensitiveWordLog
from app.services.cache_service import cache_service
from app.services.model_orchestrator import model_orchestrator
from app.api.auth import get_current_active_user

router = APIRouter()


# ========== Schemas ==========

class DashboardOverview(BaseModel):
    """仪表盘概览"""
    # 基础统计
    total_users: int
    active_users_today: int
    total_conversations: int
    conversations_today: int
    total_messages: int
    messages_today: int
    
    # 文件统计
    total_files: int
    total_storage_bytes: int
    indexed_files: int
    
    # 性能指标
    average_response_time_ms: float
    success_rate: float
    
    # 满意度
    satisfaction_rate: float
    average_rating: float


class CallStatistics(BaseModel):
    """调用统计"""
    date: str
    total_calls: int
    success_calls: int
    failed_calls: int
    average_latency_ms: float


class TopQuestion(BaseModel):
    """热门问题"""
    question: str
    count: int
    satisfaction_rate: float


class ModelUsageStats(BaseModel):
    """模型使用统计"""
    model_name: str
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost: float  # 估算成本


class UserActivity(BaseModel):
    """用户活跃度"""
    user_id: int
    username: str
    conversation_count: int
    message_count: int
    last_active: datetime


class SensitiveContentStats(BaseModel):
    """敏感内容统计"""
    date: str
    total_detections: int
    blocked_count: int
    risk_levels: Dict[str, int]


# ========== 依赖项 ==========

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员权限"""
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# ========== API 端点 ==========

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表盘概览数据"""
    
    org_id = current_user.org_id
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    
    # 1. 用户统计
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.org_id == org_id)
    )
    total_users = total_users_result.scalar() or 0
    
    # 今日活跃用户（有消息的用户）
    active_users_result = await db.execute(
        select(func.count(func.distinct(Conversation.user_id)))
        .join(Message)
        .where(
            Conversation.org_id == org_id,
            Message.created_at >= today_start
        )
    )
    active_users_today = active_users_result.scalar() or 0
    
    # 2. 对话统计
    total_conversations_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.org_id == org_id)
    )
    total_conversations = total_conversations_result.scalar() or 0
    
    conversations_today_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.org_id == org_id,
            Conversation.created_at >= today_start
        )
    )
    conversations_today = conversations_today_result.scalar() or 0
    
    # 3. 消息统计
    total_messages_result = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(Conversation.org_id == org_id)
    )
    total_messages = total_messages_result.scalar() or 0
    
    messages_today_result = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(
            Conversation.org_id == org_id,
            Message.created_at >= today_start
        )
    )
    messages_today = messages_today_result.scalar() or 0
    
    # 4. 文件统计
    total_files_result = await db.execute(
        select(func.count(File.id)).where(File.org_id == org_id)
    )
    total_files = total_files_result.scalar() or 0
    
    storage_result = await db.execute(
        select(func.sum(File.size)).where(File.org_id == org_id)
    )
    total_storage_bytes = storage_result.scalar() or 0
    
    indexed_files_result = await db.execute(
        select(func.count(File.id)).where(
            File.org_id == org_id,
            File.status == "indexed"
        )
    )
    indexed_files = indexed_files_result.scalar() or 0
    
    # 5. 性能指标（假设从审计日志计算）
    # 这里简化处理，实际应该有专门的性能监控
    average_response_time_ms = 1500.0  # 示例值
    success_rate = 0.95  # 示例值
    
    # 6. 满意度统计
    feedback_result = await db.execute(
        select(
            func.count(MessageFeedback.id),
            func.sum(func.case(
                (MessageFeedback.feedback_type == "positive", 1),
                else_=0
            )),
            func.avg(MessageFeedback.rating)
        )
        .join(Message)
        .join(Conversation)
        .where(Conversation.org_id == org_id)
    )
    feedback_stats = feedback_result.first()
    
    total_feedbacks = feedback_stats[0] or 0
    positive_feedbacks = feedback_stats[1] or 0
    average_rating = feedback_stats[2] or 0.0
    
    satisfaction_rate = (positive_feedbacks / total_feedbacks) if total_feedbacks > 0 else 0.0
    
    return DashboardOverview(
        total_users=total_users,
        active_users_today=active_users_today,
        total_conversations=total_conversations,
        conversations_today=conversations_today,
        total_messages=total_messages,
        messages_today=messages_today,
        total_files=total_files,
        total_storage_bytes=total_storage_bytes,
        indexed_files=indexed_files,
        average_response_time_ms=average_response_time_ms,
        success_rate=success_rate,
        satisfaction_rate=satisfaction_rate,
        average_rating=float(average_rating)
    )


@router.get("/call-statistics", response_model=List[CallStatistics])
async def get_call_statistics(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取调用统计（按天）"""
    
    org_id = current_user.org_id
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    # 按天统计消息数量
    result = await db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("total"),
            func.sum(func.case(
                (Message.error_message == None, 1),
                else_=0
            )).label("success"),
            func.avg(Message.latency_ms).label("avg_latency")
        )
        .join(Conversation)
        .where(
            Conversation.org_id == org_id,
            func.date(Message.created_at) >= start_date
        )
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    )
    
    stats = []
    for row in result:
        total = row.total or 0
        success = row.success or 0
        stats.append(CallStatistics(
            date=row.date.isoformat(),
            total_calls=total,
            success_calls=success,
            failed_calls=total - success,
            average_latency_ms=float(row.avg_latency or 0)
        ))
    
    return stats


@router.get("/top-questions", response_model=List[TopQuestion])
async def get_top_questions(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取热门问题榜单"""
    
    org_id = current_user.org_id
    
    # 从缓存中获取热门问题
    hot_queries = cache_service.get_hot_queries(org_id, limit)
    
    if not hot_queries:
        # 如果缓存为空，从数据库统计
        result = await db.execute(
            select(
                Message.content,
                func.count(Message.id).label("count")
            )
            .join(Conversation)
            .where(
                Conversation.org_id == org_id,
                Message.role == "user"
            )
            .group_by(Message.content)
            .order_by(desc("count"))
            .limit(limit)
        )
        
        hot_queries = [
            {"query": row.content, "count": row.count}
            for row in result
        ]
    
    # 计算每个问题的满意度
    top_questions = []
    for item in hot_queries:
        # 查询该问题的反馈
        feedback_result = await db.execute(
            select(
                func.count(MessageFeedback.id),
                func.sum(func.case(
                    (MessageFeedback.feedback_type == "positive", 1),
                    else_=0
                ))
            )
            .join(Message)
            .join(Conversation)
            .where(
                Conversation.org_id == org_id,
                Message.content == item["query"]
            )
        )
        feedback_stats = feedback_result.first()
        
        total_feedback = feedback_stats[0] or 0
        positive_feedback = feedback_stats[1] or 0
        satisfaction = (positive_feedback / total_feedback) if total_feedback > 0 else 0.0
        
        top_questions.append(TopQuestion(
            question=item["query"],
            count=item["count"],
            satisfaction_rate=satisfaction
        ))
    
    return top_questions


@router.get("/model-usage", response_model=List[ModelUsageStats])
async def get_model_usage_stats(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取模型调用花费统计"""
    
    org_id = current_user.org_id
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 统计消息中的token使用
    result = await db.execute(
        select(
            func.count(Message.id).label("total_calls"),
            func.sum(Message.token_count).label("total_tokens")
        )
        .join(Conversation)
        .where(
            Conversation.org_id == org_id,
            Message.created_at >= start_date
        )
    )
    
    stats_row = result.first()
    total_calls = stats_row.total_calls or 0
    total_tokens = stats_row.total_tokens or 0
    
    # 估算成本（假设使用GPT-4o-mini，每1M token $0.15）
    estimated_cost = (total_tokens / 1_000_000) * 0.15
    
    return [
        ModelUsageStats(
            model_name="gpt-4o-mini",
            total_calls=total_calls,
            total_input_tokens=int(total_tokens * 0.7),  # 假设70%是输入
            total_output_tokens=int(total_tokens * 0.3),  # 假设30%是输出
            estimated_cost=round(estimated_cost, 2)
        )
    ]


@router.get("/user-activity", response_model=List[UserActivity])
async def get_user_activity(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户活跃度统计"""
    
    org_id = current_user.org_id
    
    # 统计每个用户的对话和消息数量
    result = await db.execute(
        select(
            User.id,
            User.username,
            func.count(func.distinct(Conversation.id)).label("conversation_count"),
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_active")
        )
        .join(Conversation, User.id == Conversation.user_id)
        .join(Message, Conversation.id == Message.conversation_id)
        .where(User.org_id == org_id)
        .group_by(User.id, User.username)
        .order_by(desc("message_count"))
        .limit(limit)
    )
    
    activities = []
    for row in result:
        activities.append(UserActivity(
            user_id=row.id,
            username=row.username,
            conversation_count=row.conversation_count,
            message_count=row.message_count,
            last_active=row.last_active
        ))
    
    return activities


@router.get("/sensitive-content-stats", response_model=List[SensitiveContentStats])
async def get_sensitive_content_stats(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取敏感内容检测统计"""
    
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    # 按天统计敏感内容检测
    result = await db.execute(
        select(
            func.date(SensitiveWordLog.created_at).label("date"),
            func.count(SensitiveWordLog.id).label("total"),
            func.sum(func.case(
                (SensitiveWordLog.is_blocked == True, 1),
                else_=0
            )).label("blocked"),
            SensitiveWordLog.risk_level
        )
        .where(func.date(SensitiveWordLog.created_at) >= start_date)
        .group_by(
            func.date(SensitiveWordLog.created_at),
            SensitiveWordLog.risk_level
        )
    )
    
    # 按日期组织数据
    stats_by_date: Dict[str, Dict] = {}
    for row in result:
        date_str = row.date.isoformat()
        if date_str not in stats_by_date:
            stats_by_date[date_str] = {
                "total_detections": 0,
                "blocked_count": 0,
                "risk_levels": {}
            }
        
        stats_by_date[date_str]["total_detections"] += row.total
        stats_by_date[date_str]["blocked_count"] += row.blocked
        stats_by_date[date_str]["risk_levels"][row.risk_level] = row.total
    
    # 转换为列表
    stats = [
        SensitiveContentStats(
            date=date,
            total_detections=data["total_detections"],
            blocked_count=data["blocked_count"],
            risk_levels=data["risk_levels"]
        )
        for date, data in sorted(stats_by_date.items())
    ]
    
    return stats


@router.get("/cache-stats")
async def get_cache_stats(
    current_user: User = Depends(require_admin)
):
    """获取缓存统计信息"""
    
    return cache_service.get_cache_stats()


@router.get("/model-health")
async def get_model_health(
    current_user: User = Depends(require_admin)
):
    """获取模型健康状态"""
    
    return model_orchestrator.get_model_stats()


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统健康状态"""
    
    # 检查数据库连接
    db_healthy = True
    try:
        await db.execute(select(1))
    except Exception:
        db_healthy = False
    
    # 检查Redis连接
    redis_healthy = True
    try:
        cache_service.redis_client.ping()
    except Exception:
        redis_healthy = False
    
    return {
        "status": "healthy" if (db_healthy and redis_healthy) else "degraded",
        "components": {
            "database": "up" if db_healthy else "down",
            "redis": "up" if redis_healthy else "down",
            "vector_db": "up",  # TODO: 实际检查
            "storage": "up"  # TODO: 实际检查
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/export-stats")
async def export_dashboard_stats(
    format: str = Query(default="json", regex="^(json|csv)$"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """导出仪表盘统计数据"""
    
    # 获取所有统计数据
    overview = await get_dashboard_overview(current_user, db)
    call_stats = await get_call_statistics(7, current_user, db)
    top_questions = await get_top_questions(10, current_user, db)
    
    data = {
        "overview": overview.dict(),
        "call_statistics": [s.dict() for s in call_stats],
        "top_questions": [q.dict() for q in top_questions],
        "exported_at": datetime.utcnow().isoformat()
    }
    
    if format == "json":
        return data
    
    elif format == "csv":
        # TODO: 实现CSV导出
        raise HTTPException(status_code=501, detail="CSV导出功能待实现")

