"""
文件模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class FileStatus(str, enum.Enum):
    """文件处理状态"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXED = "indexed"
    FAILED = "failed"


class File(Base):
    """文件表"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 组织关联
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="files")
    
    # 上传者
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploader = relationship("User", back_populates="files")
    
    # 文件信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    mime_type = Column(String(100))
    
    # 存储信息
    object_key = Column(String(500), nullable=False, unique=True)  # S3 对象键
    size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    
    # 处理状态
    status = Column(SQLEnum(FileStatus), default=FileStatus.UPLOADING, nullable=False)
    error_message = Column(String(1000))
    
    # 元数据
    page_count = Column(Integer)
    chunk_count = Column(Integer, default=0)
    language = Column(String(10))  # zh, en, etc.
    
    # 版本控制
    version = Column(Integer, default=1, nullable=False)  # 文档版本号
    previous_version_id = Column(Integer, ForeignKey("files.id"), nullable=True)  # 上一版本文件ID
    is_latest_version = Column(Integer, default=1)  # 是否为最新版本
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    parsed_at = Column(DateTime(timezone=True))
    indexed_at = Column(DateTime(timezone=True))
    last_refreshed_at = Column(DateTime(timezone=True))  # 最后刷新时间
    
    # 关系
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<File {self.filename} ({self.status})>"

