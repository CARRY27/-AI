"""
文档标签模型
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


# 文档-标签关联表（多对多）
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('files.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 标签信息
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # department, project, time, custom
    color = Column(String(20))  # 标签颜色
    
    # 组织关联
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Tag {self.name} ({self.category})>"

