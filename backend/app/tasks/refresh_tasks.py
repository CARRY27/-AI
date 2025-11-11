"""
定期文档刷新任务
用于知识更新机制
"""

import hashlib
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.models.file import File, FileStatus
from app.models.chunk import Chunk
from app.database.session import SessionLocal
from app.services.document_parser import DocumentParser
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.cache_service import cache_service
from app.config import settings


@celery_app.task(name="refresh_document")
def refresh_document_task(file_id: int, force: bool = False):
    """
    刷新单个文档
    
    Args:
        file_id: 文件ID
        force: 是否强制刷新（即使内容未变化）
    """
    
    db = SessionLocal()
    
    try:
        # 获取文件记录
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            print(f"文件不存在: {file_id}")
            return
        
        # 检查是否需要刷新
        if not force and file.last_refreshed_at:
            time_since_refresh = datetime.utcnow() - file.last_refreshed_at
            if time_since_refresh < timedelta(hours=settings.REFRESH_INTERVAL_HOURS):
                print(f"文件 {file.filename} 最近已刷新，跳过")
                return
        
        print(f"开始刷新文件: {file.filename}")
        
        # 从S3重新下载文件
        from app.tasks.document_tasks import _get_s3_client
        s3_client = _get_s3_client()
        
        try:
            response = s3_client.get_object(settings.S3_BUCKET, file.object_key)
            new_file_content = response.read()
        except Exception as e:
            print(f"从 S3 下载文件失败: {str(e)}")
            return
        
        # 计算新文件内容的哈希
        new_hash = hashlib.sha256(new_file_content).hexdigest()
        
        # 获取旧哈希（从文件元数据或数据库）
        # 如果内容未变化且非强制刷新，跳过
        old_chunks = db.query(Chunk).filter(Chunk.file_id == file_id).all()
        if old_chunks and not force:
            # 简单比较：如果chunk数量和总内容长度相同，认为未变化
            old_content_length = sum(len(c.text) for c in old_chunks)
            if len(new_file_content) == file.size:
                print(f"文件内容未变化，更新刷新时间")
                file.last_refreshed_at = datetime.utcnow()
                db.commit()
                return
        
        # 增量更新：检测变化的部分
        incremental_update_chunks(
            db=db,
            file=file,
            new_file_content=new_file_content,
            force=force
        )
        
        # 更新刷新时间
        file.last_refreshed_at = datetime.utcnow()
        db.commit()
        
        # 清除缓存
        cache_service.invalidate_vector_cache(file.org_id)
        cache_service.invalidate_query_cache(file.org_id)
        
        print(f"文件刷新完成: {file.filename}")
        
    except Exception as e:
        print(f"刷新文件时发生错误: {str(e)}")
    
    finally:
        db.close()


def incremental_update_chunks(
    db: Session,
    file: File,
    new_file_content: bytes,
    force: bool = False
):
    """
    增量更新chunks
    只对改动部分重新embedding
    
    Args:
        db: 数据库会话
        file: 文件对象
        new_file_content: 新文件内容
        force: 是否强制全量更新
    """
    
    # 1. 解析新文档
    parser = DocumentParser()
    new_document_chunks = parser.parse(new_file_content, file.file_type)
    
    # 2. 切片
    chunking_service = ChunkingService()
    new_chunks = []
    
    for doc_chunk in new_document_chunks:
        chunks = chunking_service.chunk_text(
            text=doc_chunk.text,
            strategy="sentences",
            metadata={
                "page": doc_chunk.page,
                "heading": doc_chunk.heading
            }
        )
        new_chunks.extend(chunks)
    
    # 3. 获取旧chunks
    old_chunks = db.query(Chunk).filter(Chunk.file_id == file.id).all()
    old_chunks_dict = {chunk.text_hash: chunk for chunk in old_chunks}
    
    # 4. 计算差异
    chunks_to_add = []
    chunks_to_update = []
    chunks_to_delete = []
    
    # 计算新chunk的哈希
    new_chunks_hashes = set()
    for chunk_data in new_chunks:
        text_hash = hashlib.sha256(chunk_data["text"].encode()).hexdigest()
        new_chunks_hashes.add(text_hash)
        
        if text_hash not in old_chunks_dict:
            # 新增的chunk
            chunks_to_add.append((text_hash, chunk_data))
        else:
            # 已存在的chunk（可能需要更新元数据）
            old_chunk = old_chunks_dict[text_hash]
            if (old_chunk.page_number != chunk_data.get("metadata", {}).get("page") or
                old_chunk.heading != chunk_data.get("metadata", {}).get("heading")):
                chunks_to_update.append((old_chunk, chunk_data))
    
    # 找出需要删除的chunks
    for text_hash, chunk in old_chunks_dict.items():
        if text_hash not in new_chunks_hashes:
            chunks_to_delete.append(chunk)
    
    print(f"增量更新统计: 新增 {len(chunks_to_add)}, 更新 {len(chunks_to_update)}, 删除 {len(chunks_to_delete)}")
    
    # 如果强制更新或变化较大（超过50%），执行全量更新
    change_ratio = (len(chunks_to_add) + len(chunks_to_delete)) / max(len(old_chunks), 1)
    if force or change_ratio > 0.5:
        print("变化较大，执行全量更新")
        
        # 删除所有旧chunks
        db.query(Chunk).filter(Chunk.file_id == file.id).delete()
        
        # 从向量库删除
        vector_service = VectorService()
        old_chunk_ids = [chunk.chunk_id for chunk in old_chunks]
        if old_chunk_ids:
            import asyncio
            asyncio.run(vector_service.delete_vectors(old_chunk_ids))
        
        # 添加所有新chunks
        add_new_chunks(db, file, new_chunks)
        
    else:
        # 增量更新
        
        # 1. 删除旧chunks
        vector_service = VectorService()
        if chunks_to_delete:
            delete_chunk_ids = [chunk.chunk_id for chunk in chunks_to_delete]
            import asyncio
            asyncio.run(vector_service.delete_vectors(delete_chunk_ids))
            
            for chunk in chunks_to_delete:
                db.delete(chunk)
        
        # 2. 更新元数据
        for old_chunk, new_data in chunks_to_update:
            old_chunk.page_number = new_data.get("metadata", {}).get("page")
            old_chunk.heading = new_data.get("metadata", {}).get("heading")
            old_chunk.metadata = new_data.get("metadata", {})
        
        # 3. 添加新chunks
        if chunks_to_add:
            new_chunk_data_list = [chunk_data for _, chunk_data in chunks_to_add]
            add_new_chunks(db, file, new_chunk_data_list)
    
    db.commit()


def add_new_chunks(db: Session, file: File, chunk_data_list: list):
    """添加新chunks并生成embedding"""
    
    import uuid
    import asyncio
    from app.services.embedding_service import EmbeddingService
    from app.services.vector_service import VectorService
    
    # 创建chunk记录
    chunk_records = []
    for chunk_data in chunk_data_list:
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
    
    db.flush()  # 获取ID
    
    # 生成embeddings
    embedding_service = EmbeddingService()
    texts = [chunk.text for chunk in chunk_records]
    embeddings = asyncio.run(embedding_service.embed_batch(texts))
    
    # 存储到向量数据库
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
    
    asyncio.run(vector_service.add_vectors(chunk_ids, embeddings, metadata))
    
    # 更新chunk状态
    for chunk in chunk_records:
        chunk.is_embedded = 1


@celery_app.task(name="refresh_all_documents")
def refresh_all_documents_task(org_id: int = None):
    """
    刷新所有文档（定期任务）
    
    Args:
        org_id: 组织ID，如果指定则只刷新该组织的文档
    """
    
    db = SessionLocal()
    
    try:
        # 查询需要刷新的文件
        query = db.query(File).filter(
            File.status == FileStatus.INDEXED,
            File.is_latest_version == 1
        )
        
        if org_id:
            query = query.filter(File.org_id == org_id)
        
        files = query.all()
        
        print(f"找到 {len(files)} 个文件需要检查刷新")
        
        # 触发每个文件的刷新任务
        for file in files:
            refresh_document_task.delay(file.id, force=False)
        
        print(f"已触发 {len(files)} 个刷新任务")
        
    except Exception as e:
        print(f"刷新所有文档时发生错误: {str(e)}")
    
    finally:
        db.close()


@celery_app.task(name="create_document_version")
def create_document_version_task(original_file_id: int, new_file_content: bytes):
    """
    创建文档新版本
    
    Args:
        original_file_id: 原始文件ID
        new_file_content: 新文件内容
    """
    
    db = SessionLocal()
    
    try:
        # 获取原始文件
        original_file = db.query(File).filter(File.id == original_file_id).first()
        if not original_file:
            print(f"原始文件不存在: {original_file_id}")
            return
        
        # 将原文件标记为非最新版本
        original_file.is_latest_version = 0
        
        # 创建新版本文件记录
        import uuid
        new_object_key = f"{original_file.org_id}/{uuid.uuid4().hex}_{original_file.original_filename}"
        
        new_file = File(
            org_id=original_file.org_id,
            uploaded_by=original_file.uploaded_by,
            filename=original_file.filename,
            original_filename=original_file.original_filename,
            file_type=original_file.file_type,
            mime_type=original_file.mime_type,
            object_key=new_object_key,
            size=len(new_file_content),
            status=FileStatus.UPLOADED,
            version=original_file.version + 1,
            previous_version_id=original_file_id,
            is_latest_version=1
        )
        
        db.add(new_file)
        db.commit()
        
        # 上传新文件到S3
        from app.tasks.document_tasks import _get_s3_client
        s3_client = _get_s3_client()
        
        from io import BytesIO
        s3_client.put_object(
            settings.S3_BUCKET,
            new_object_key,
            BytesIO(new_file_content),
            len(new_file_content)
        )
        
        # 触发文档处理任务
        from app.tasks.document_tasks import process_document_task
        process_document_task.delay(new_file.id)
        
        print(f"已创建文档新版本: {new_file.id}, 版本号: {new_file.version}")
        
        return new_file.id
        
    except Exception as e:
        print(f"创建文档版本时发生错误: {str(e)}")
        db.rollback()
    
    finally:
        db.close()

