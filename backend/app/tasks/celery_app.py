"""
Celery 应用配置
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "docagent",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.refresh_tasks",
        "app.tasks.scheduled_tasks"
    ]
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)

# Celery Beat 定期任务配置
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 每天凌晨2点刷新所有文档
    'refresh-all-documents-daily': {
        'task': 'refresh_all_documents',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'refresh'}
    },
    
    # 每小时清理过期缓存
    'cleanup-expired-cache-hourly': {
        'task': 'cleanup_expired_cache',
        'schedule': crontab(minute=0),
        'options': {'queue': 'maintenance'}
    },
    
    # 每天凌晨1点生成统计报告
    'generate-daily-stats': {
        'task': 'generate_daily_stats',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'stats'}
    },
}

