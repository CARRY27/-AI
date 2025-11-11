"""
文档处理异步任务
"""

import hashlib
import uuid
from sqlalchemy import select
from minio import Minio

from app.tasks.celery_app import celery_app
from app.models.file import File, FileStatus
from app.models.chunk import Chunk
from app.database.session import SessionLocal
from app.services.document_parser import DocumentParser
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.config import settings


@celery_app.task(name="process_document")
def process_document_task(file_id: int):
    """处理文档：解析、切片、embedding、向量化"""
    
    db = SessionLocal()
    
    try:
        # 1. 获取文件记录
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            print(f"文件不存在: {file_id}")
            return
        
        # 2. 更新状态为解析中
        file.status = FileStatus.PARSING
        db.commit()
        
        # 3. 从 S3 下载文件
        print(f"开始处理文件: {file.filename}")
        s3_client = _get_s3_client()
        
        try:
            response = s3_client.get_object(settings.S3_BUCKET, file.object_key)
            file_content = response.read()
        except Exception as e:
            file.status = FileStatus.FAILED
            file.error_message = f"从 S3 下载文件失败: {str(e)}"
            db.commit()
            return
        
        # 4. 解析文档
        try:
            parser = DocumentParser()
            document_chunks = parser.parse(file_content, file.file_type)
            print(f"解析完成，共 {len(document_chunks)} 个片段")
        except Exception as e:
            file.status = FileStatus.FAILED
            file.error_message = f"文档解析失败: {str(e)}"
            db.commit()
            return
        
        # 5. 更新状态为切片中
        file.status = FileStatus.CHUNKING
        db.commit()
        
        # 6. 进行文本切片
        chunking_service = ChunkingService()
        all_chunks = []
        
        for doc_chunk in document_chunks:
            chunks = chunking_service.chunk_text(
                text=doc_chunk.text,
                strategy="sentences",
                metadata={
                    "page": doc_chunk.page,
                    "heading": doc_chunk.heading
                }
            )
            all_chunks.extend(chunks)
        
        print(f"切片完成，共 {len(all_chunks)} 个 chunk")
        
        # 7. 保存 chunks 到数据库
        chunk_records = []
        for chunk_data in all_chunks:
            # 计算内容哈希
            text_hash = hashlib.sha256(chunk_data["text"].encode()).hexdigest()
            
            chunk_id = f"{file.id}_{uuid.uuid4().hex[:8]}"
            
            chunk = Chunk(
                chunk_id=chunk_id,
                file_id=file.id,
                text=chunk_data["text"],
                text_hash=text_hash,
                page_number=chunk_data.get("metadata", {}).get("page"),
                heading=chunk_data.get("metadata", {}).get("heading"),
                token_count=chunk_data.get("token_count"),
                metadata=chunk_data.get("metadata", {}),
                is_embedded=0
            )
            
            db.add(chunk)
            chunk_records.append(chunk)
        
        db.commit()
        
        # 8. 更新状态为嵌入中
        file.status = FileStatus.EMBEDDING
        file.chunk_count = len(chunk_records)
        db.commit()
        
        # 9. 生成 embeddings
        embedding_service = EmbeddingService()
        texts = [chunk.text for chunk in chunk_records]
        
        try:
            import asyncio
            embeddings = asyncio.run(embedding_service.embed_batch(texts))
            print(f"Embedding 完成，共 {len(embeddings)} 个向量")
        except Exception as e:
            file.status = FileStatus.FAILED
            file.error_message = f"生成 embedding 失败: {str(e)}"
            db.commit()
            return
        
        # 10. 存储到向量数据库
        vector_service = VectorService()
        chunk_ids = [chunk.chunk_id for chunk in chunk_records]
        metadata = [
            {
                "file_id": file.id,
                "file_name": file.original_filename,
                "page": chunk.page_number,
                "heading": chunk.heading
            }
            for chunk in chunk_records
        ]
        
        try:
            asyncio.run(vector_service.add_vectors(chunk_ids, embeddings, metadata))
            print(f"向量存储完成")
        except Exception as e:
            file.status = FileStatus.FAILED
            file.error_message = f"存储向量失败: {str(e)}"
            db.commit()
            return
        
        # 11. 更新 chunks 状态
        for chunk in chunk_records:
            chunk.is_embedded = 1
        
        # 12. 更新文件状态为已索引
        file.status = FileStatus.INDEXED
        from datetime import datetime
        file.indexed_at = datetime.utcnow()
        db.commit()
        
        print(f"文件处理完成: {file.filename}")
        
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        if file:
            file.status = FileStatus.FAILED
            file.error_message = str(e)
            db.commit()
    
    finally:
        db.close()


def _get_s3_client():
    """获取 S3 客户端"""
    endpoint = settings.S3_ENDPOINT.replace("http://", "").replace("https://", "")
    
    return Minio(
        endpoint,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=settings.S3_USE_SSL
    )

