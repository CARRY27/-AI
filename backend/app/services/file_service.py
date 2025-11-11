"""
文件服务
处理文件上传、存储、删除等操作
"""

import os
import uuid
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio
from minio.error import S3Error

from app.models.file import File, FileStatus
from app.config import settings


class FileService:
    """文件服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = self._get_s3_client()
    
    def _get_s3_client(self) -> Minio:
        """获取 S3/MinIO 客户端"""
        endpoint = settings.S3_ENDPOINT.replace("http://", "").replace("https://", "")
        
        client = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_USE_SSL
        )
        
        # 确保 bucket 存在
        try:
            if not client.bucket_exists(settings.S3_BUCKET):
                client.make_bucket(settings.S3_BUCKET)
        except S3Error as e:
            print(f"S3 错误: {e}")
        
        return client
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        org_id: int
    ) -> File:
        """上传文件到 S3 并创建数据库记录"""
        
        # 生成唯一文件名
        file_ext = file.filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        object_key = f"{org_id}/{user_id}/{unique_filename}"
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 上传到 S3
        try:
            from io import BytesIO
            self.s3_client.put_object(
                settings.S3_BUCKET,
                object_key,
                BytesIO(content),
                length=file_size,
                content_type=file.content_type or "application/octet-stream"
            )
        except S3Error as e:
            raise Exception(f"文件上传到 S3 失败: {e}")
        
        # 创建数据库记录
        file_record = File(
            org_id=org_id,
            uploaded_by=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_ext,
            mime_type=file.content_type,
            object_key=object_key,
            size=file_size,
            status=FileStatus.UPLOADED
        )
        
        self.db.add(file_record)
        await self.db.commit()
        await self.db.refresh(file_record)
        
        # 触发异步处理任务
        from app.tasks.document_tasks import process_document_task
        process_document_task.delay(file_record.id)
        
        return file_record
    
    async def delete_file(self, file: File):
        """删除文件（S3 和数据库）"""
        
        # 从 S3 删除
        try:
            self.s3_client.remove_object(settings.S3_BUCKET, file.object_key)
        except S3Error as e:
            print(f"从 S3 删除文件失败: {e}")
        
        # 从向量数据库删除
        from app.services.vector_service import VectorService
        vector_service = VectorService()
        await vector_service.delete_file_vectors(file.id)
        
        # 从数据库删除
        await self.db.delete(file)
        await self.db.commit()
    
    def get_file_url(self, object_key: str, expires: int = 3600) -> str:
        """获取文件的预签名 URL"""
        try:
            url = self.s3_client.presigned_get_object(
                settings.S3_BUCKET,
                object_key,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            raise Exception(f"生成预签名 URL 失败: {e}")


from datetime import timedelta

