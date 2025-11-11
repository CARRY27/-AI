"""
对话消息模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class MessageRole(str, enum.Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """对话消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 会话关联
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    
    # 消息信息
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # 来源引用（JSON 格式）
    # [{"file_id": 1, "file_name": "xxx.pdf", "page": 3, "chunk_id": "xxx", "excerpt": "..."}]
    source_refs = Column(JSON, default=[])
    
    # 元数据
    meta_data = Column(JSON, default={})  # 改名避免与SQLAlchemy保留字冲突
    token_count = Column(Integer)
    
    # 评分与反馈
    rating = Column(Integer)  # 1-5 星
    feedback = Column(String(1000))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 反馈关系
    feedbacks = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message {self.id} ({self.role}) in Conversation {self.conversation_id}>"

