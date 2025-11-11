"""
文档切片模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Chunk(Base):
    """文档切片表"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(100), unique=True, index=True, nullable=False)  # 用于向量库关联
    
    # 文件关联
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file = relationship("File", back_populates="chunks")
    
    # 内容
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), index=True)  # 内容哈希，用于去重
    
    # 位置信息
    page_number = Column(Integer)
    start_offset = Column(Integer)
    end_offset = Column(Integer)
    
    # 结构信息
    heading = Column(String(500))
    section = Column(String(500))
    
    # 元数据
    token_count = Column(Integer)
    language = Column(String(10))
    meta_data = Column(JSON, default={})  # 改名避免与SQLAlchemy保留字冲突
    
    # 向量信息
    embedding_model = Column(String(100))
    is_embedded = Column(Integer, default=0)  # 0: 未嵌入, 1: 已嵌入
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    embedded_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Chunk {self.chunk_id} from File {self.file_id}>"

