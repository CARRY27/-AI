"""
文件管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.user import User
from app.models.file import File, FileStatus
from app.api.auth import get_current_active_user
from app.services.file_service import FileService
from app.config import settings

router = APIRouter()


# ========== Schemas ==========

class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    status: str
    message: str


class FileInfoResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    size: int
    status: str
    page_count: Optional[int]
    chunk_count: int
    created_at: datetime
    indexed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: List[FileInfoResponse]
    total: int
    page: int
    page_size: int


# ========== API 端点 ==========

@router.post("/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """上传文件"""
    
    # 验证文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # 验证文件大小（在内存中读取可能不适合大文件，这里简化处理）
    file_service = FileService(db)
    
    try:
        # 上传文件到 S3 并创建数据库记录
        file_record = await file_service.upload_file(
            file=file,
            user_id=current_user.id,
            org_id=current_user.org_id
        )
        
        return {
            "file_id": file_record.id,
            "filename": file_record.filename,
            "status": file_record.status.value,
            "message": "文件上传成功，正在处理中..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/", response_model=FileListResponse)
async def list_files(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件列表"""
    
    # 构建查询
    query = select(File).where(File.org_id == current_user.org_id)
    
    if status_filter:
        query = query.where(File.status == status_filter)
    
    # 计算总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    # 分页查询
    query = query.order_by(desc(File.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    return {
        "files": files,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件详情"""
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.org_id == current_user.org_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除文件"""
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.org_id == current_user.org_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 使用文件服务删除文件（包括 S3 和向量）
    file_service = FileService(db)
    await file_service.delete_file(file)
    
    return {"message": "文件删除成功"}


@router.get("/{file_id}/status")
async def get_file_status(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件处理状态"""
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.org_id == current_user.org_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {
        "file_id": file.id,
        "filename": file.filename,
        "status": file.status.value,
        "chunk_count": file.chunk_count,
        "error_message": file.error_message
    }


from sqlalchemy import func

