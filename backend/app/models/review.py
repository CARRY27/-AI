"""
审核相关模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class ReviewStatus(str, enum.Enum):
    """审核状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已通过
    REJECTED = "rejected"    # 已拒绝
    FLAGGED = "flagged"      # 已标记


class ReviewType(str, enum.Enum):
    """审核类型"""
    ACCURACY = "accuracy"        # 准确性问题
    INAPPROPRIATE = "inappropriate"  # 不当内容
    VAGUE = "vague"             # 模糊不清
    HALLUCINATION = "hallucination"  # 虚构内容
    SENSITIVE = "sensitive"      # 敏感内容


class MessageReview(Base):
    """消息审核表"""
    __tablename__ = "message_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 消息关联
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # 审核员
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 审核结果
    status = Column(SQLEnum(ReviewStatus), nullable=False)
    review_type = Column(SQLEnum(ReviewType))
    
    # 审核意见
    comment = Column(Text)
    suggestion = Column(Text)  # 改进建议
    
    # 是否需要人工介入
    requires_human_review = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MessageReview {self.id} ({self.status})>"


class SensitiveWordLog(Base):
    """敏感词检测日志"""
    __tablename__ = "sensitive_word_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的消息或文档
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    
    # 检测结果
    content_type = Column(String(50))  # question, answer, document
    detected_words = Column(Text)  # 检测到的敏感词（JSON数组）
    risk_level = Column(String(20))  # low, medium, high, critical
    
    # 详细信息
    original_text = Column(Text)  # 原始文本片段
    context = Column(Text)  # 上下文
    
    # 处理状态
    is_blocked = Column(Boolean, default=False)  # 是否已屏蔽
    handled = Column(Boolean, default=False)  # 是否已处理
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    handled_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<SensitiveWordLog {self.id} ({self.risk_level})>"

