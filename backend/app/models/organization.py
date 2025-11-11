"""
组织模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Organization(Base):
    """组织表"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    
    # 设置（JSON 格式存储）
    settings = Column(JSON, default={})
    
    # 配额
    max_file_size_mb = Column(Integer, default=50)
    max_storage_gb = Column(Integer, default=100)
    max_users = Column(Integer, default=50)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    users = relationship("User", back_populates="organization")
    files = relationship("File", back_populates="organization")
    conversations = relationship("Conversation", back_populates="organization")
    prompt_templates = relationship("PromptTemplate", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization {self.name}>"

