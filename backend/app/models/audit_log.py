"""
审计日志模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="audit_logs")
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # upload, query, delete, etc.
    resource_type = Column(String(50))  # file, conversation, user, etc.
    resource_id = Column(Integer)
    
    # 详细信息
    description = Column(String(500))
    details = Column(JSON, default={})
    
    # 请求信息
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_path = Column(String(500))
    request_method = Column(String(10))
    
    # 结果
    status_code = Column(Integer)
    success = Column(Integer, default=1)  # 1: 成功, 0: 失败
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by User {self.user_id}>"

