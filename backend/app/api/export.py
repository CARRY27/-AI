"""
导出相关 API
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.auth import get_current_active_user
from app.services.export_service import ExportService

router = APIRouter()


# ========== Schemas ==========

class ExportRequest(BaseModel):
    conversation_id: int
    format: str  # markdown, html, pdf


# ========== API 端点 ==========

@router.post("/conversation")
async def export_conversation(
    data: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """导出对话"""
    
    # 验证对话归属
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == data.conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 获取消息
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == data.conversation_id
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    if not messages:
        raise HTTPException(status_code=400, detail="对话没有消息，无法导出")
    
    # 转换消息格式
    messages_data = [
        {
            "role": msg.role.value,
            "content": msg.content,
            "source_refs": msg.source_refs,
            "created_at": msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in messages
    ]
    
    export_service = ExportService()
    
    try:
        if data.format == "markdown":
            content = export_service.export_to_markdown(
                conversation.title,
                messages_data,
                current_user.username
            )
            
            return Response(
                content=content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename={conversation.title}.md"
                }
            )
        
        elif data.format == "html":
            content = export_service.export_to_html(
                conversation.title,
                messages_data,
                current_user.username
            )
            
            return Response(
                content=content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={conversation.title}.html"
                }
            )
        
        elif data.format == "pdf":
            pdf_bytes = export_service.export_to_pdf(
                conversation.title,
                messages_data,
                current_user.username
            )
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={conversation.title}.pdf"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {data.format}")
    
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

