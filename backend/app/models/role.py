"""
角色权限模型
"""

from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # superadmin, admin, auditor, user
    display_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(String(500))
    
    # 权限配置（JSON格式）
    # {
    #   "document": {"read": true, "write": true, "delete": true},
    #   "conversation": {"read": true, "write": true, "export": true},
    #   "admin": {"manage_users": true, "view_audit": true}
    # }
    permissions = Column(JSON, default={})
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统内置角色，不可删除
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Role {self.name}>"


class UserRole(Base):
    """用户角色关联表（支持一个用户多个角色）"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role_id = Column(Integer, nullable=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"

