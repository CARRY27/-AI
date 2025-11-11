"""
用户反馈模型
记录用户对回答的评价（点赞/点踩）
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database.session import Base


class MessageFeedback(Base):
    """消息反馈表"""
    __tablename__ = "message_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 反馈类型：positive(点赞) / negative(点踩)
    feedback_type = Column(String(20), nullable=False)
    
    # 评分（1-5星）
    rating = Column(Integer, nullable=True)
    
    # 文字反馈
    comment = Column(Text, nullable=True)
    
    # 问题标签：inaccurate(不准确), incomplete(不完整), irrelevant(不相关), other(其他)
    issue_tags = Column(JSONB, default=list)
    
    # 是否已处理
    is_resolved = Column(Boolean, default=False)
    
    # 处理说明
    resolution_note = Column(Text, nullable=True)
    
    # 元数据
    meta_data = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    message = relationship("Message", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, type={self.feedback_type})>"


class FeedbackStats(Base):
    """反馈统计表"""
    __tablename__ = "feedback_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # 日期
    date = Column(DateTime, nullable=False)
    
    # 统计指标
    total_feedbacks = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    
    # 满意度（0-1）
    satisfaction_rate = Column(Float, default=0.0)
    
    # 平均评分
    average_rating = Column(Float, default=0.0)
    
    # 常见问题标签统计
    issue_tag_counts = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FeedbackStats(date={self.date}, satisfaction={self.satisfaction_rate})>"

