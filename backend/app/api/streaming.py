"""
流式输出 API
支持 SSE (Server-Sent Events)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import json
from datetime import datetime

from app.database.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services.rag_service import RAGService
from app.api.auth import get_current_active_user

router = APIRouter()


# ========== Schemas ==========

class StreamQueryRequest(BaseModel):
    conversation_id: int
    question: str


# ========== API 端点 ==========

@router.post("/chat")
async def stream_chat(
    data: StreamQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """流式聊天接口（SSE）"""
    
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
    
    # 创建用户消息
    user_message = Message(
        conversation_id=data.conversation_id,
        role=MessageRole.USER,
        content=data.question
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    # 流式生成器
    async def generate_sse_stream():
        """生成SSE事件流"""
        rag_service = RAGService(db)
        
        try:
            # 发送开始事件
            event_data = {
                "type": "start",
                "user_message_id": user_message.id,
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 流式生成答案
            full_answer = ""
            async for chunk in rag_service.stream_generate_answer(
                question=data.question,
                conversation_id=data.conversation_id,
                org_id=current_user.org_id
            ):
                full_answer += chunk
                
                event_data = {
                    "type": "chunk",
                    "content": chunk
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 保存AI回复消息
            ai_message = Message(
                conversation_id=data.conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_answer
            )
            db.add(ai_message)
            
            # 更新对话统计
            conversation.message_count += 2
            conversation.last_message_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(ai_message)
            
            # 发送完成事件
            event_data = {
                "type": "complete",
                "ai_message_id": ai_message.id,
                "full_answer": full_answer,
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            # 发送错误事件
            error_data = {
                "type": "error",
                "message": f"生成答案时出错: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/health")
async def streaming_health():
    """流式服务健康检查"""
    return {
        "status": "healthy",
        "service": "streaming",
        "features": ["SSE", "real-time chat"]
    }

