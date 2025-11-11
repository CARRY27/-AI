"""
定时任务
用于CRON job调度
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func, and_

from app.tasks.celery_app import celery_app
from app.database.session import SessionLocal
from app.models.message import Message
from app.models.feedback import MessageFeedback, FeedbackStats
from app.models.conversation import Conversation
from app.models.audit_log import AuditLog
from app.services.cache_service import cache_service


@celery_app.task(name="cleanup_expired_cache")
def cleanup_expired_cache_task():
    """
    清理过期缓存
    Redis会自动清理过期key，这里主要是清理一些统计数据
    """
    try:
        # 清理超过7天的查询统计
        # 这里可以添加更多清理逻辑
        print("清理过期缓存完成")
        
    except Exception as e:
        print(f"清理缓存时发生错误: {str(e)}")


@celery_app.task(name="generate_daily_stats")
def generate_daily_stats_task():
    """
    生成每日统计报告
    包括：调用次数、反馈统计、用户活跃度等
    """
    
    db = SessionLocal()
    
    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        print(f"生成 {yesterday} 的统计报告")
        
        # 获取所有组织
        from app.models.organization import Organization
        orgs = db.query(Organization).all()
        
        for org in orgs:
            # 1. 统计反馈数据
            feedbacks = db.query(MessageFeedback).join(Message).join(Conversation).filter(
                Conversation.org_id == org.id,
                and_(
                    MessageFeedback.created_at >= yesterday_start,
                    MessageFeedback.created_at <= yesterday_end
                )
            ).all()
            
            total_feedbacks = len(feedbacks)
            positive_count = len([f for f in feedbacks if f.feedback_type == "positive"])
            negative_count = len([f for f in feedbacks if f.feedback_type == "negative"])
            
            satisfaction_rate = positive_count / total_feedbacks if total_feedbacks > 0 else 0.0
            
            # 计算平均评分
            ratings = [f.rating for f in feedbacks if f.rating]
            average_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            # 统计问题标签
            issue_tag_counts = {}
            for feedback in feedbacks:
                if feedback.issue_tags:
                    for tag in feedback.issue_tags:
                        issue_tag_counts[tag] = issue_tag_counts.get(tag, 0) + 1
            
            # 2. 保存统计数据
            stats = FeedbackStats(
                org_id=org.id,
                date=yesterday_start,
                total_feedbacks=total_feedbacks,
                positive_count=positive_count,
                negative_count=negative_count,
                satisfaction_rate=satisfaction_rate,
                average_rating=average_rating,
                issue_tag_counts=issue_tag_counts
            )
            
            db.add(stats)
            
            print(f"组织 {org.name} - 总反馈: {total_feedbacks}, 满意度: {satisfaction_rate:.2%}")
        
        db.commit()
        print("每日统计报告生成完成")
        
    except Exception as e:
        print(f"生成统计报告时发生错误: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


@celery_app.task(name="cleanup_old_logs")
def cleanup_old_logs_task(days: int = 90):
    """
    清理旧日志
    默认清理90天前的日志
    """
    
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 清理审计日志
        deleted = db.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        print(f"已清理 {deleted} 条旧审计日志")
        
    except Exception as e:
        print(f"清理旧日志时发生错误: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


@celery_app.task(name="update_model_usage_stats")
def update_model_usage_stats_task():
    """
    更新模型使用统计
    用于成本分析和优化
    """
    
    db = SessionLocal()
    
    try:
        # 统计今日模型调用
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        
        result = db.query(
            func.count(Message.id),
            func.sum(Message.token_count)
        ).filter(
            Message.created_at >= today_start
        ).first()
        
        total_calls = result[0] or 0
        total_tokens = result[1] or 0
        
        print(f"今日模型调用: {total_calls} 次, 总tokens: {total_tokens}")
        
        # 可以将统计结果保存到数据库或发送到监控系统
        
    except Exception as e:
        print(f"更新模型统计时发生错误: {str(e)}")
    
    finally:
        db.close()


@celery_app.task(name="backup_database")
def backup_database_task():
    """
    数据库备份任务
    定期备份重要数据
    """
    
    try:
        # 这里可以调用数据库备份命令或导出数据
        # 例如：pg_dump 或导出到 S3
        print("数据库备份任务执行")
        
    except Exception as e:
        print(f"数据库备份时发生错误: {str(e)}")

