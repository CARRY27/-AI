"""
对话管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.api.auth import get_current_active_user
from app.services.conversation_service import ConversationService
from app.services.rag_service import RAGService

router = APIRouter()


# ========== Schemas ==========

class ConversationCreate(BaseModel):
    title: Optional[str] = "新对话"


class ConversationResponse(BaseModel):
    id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_message_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class SourceRef(BaseModel):
    file_id: int
    file_name: str
    page: Optional[int]
    chunk_id: str
    excerpt: str
    similarity: Optional[float]


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    source_refs: List[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]


class QueryResponse(BaseModel):
    message_id: int
    answer: str
    sources: List[SourceRef]
    confidence: Optional[float]


# ========== API 端点 ==========

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    
    conversation = Conversation(
        user_id=current_user.id,
        org_id=current_user.org_id,
        title=data.title or "新对话"
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话列表"""
    
    query = select(Conversation).where(
        Conversation.user_id == current_user.id
    ).order_by(desc(Conversation.updated_at))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return conversations


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话详情"""
    
    # 获取对话
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 获取消息
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return {
        "conversation": conversation,
        "messages": messages
    }


# 新增：获取指定对话的消息列表，供前端加载使用
@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取某个对话的消息列表"""
    # 验证对话归属
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.post("/{conversation_id}/messages", response_model=QueryResponse)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """发送消息并获取回复"""
    
    # 验证对话归属
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=data.content
    )
    db.add(user_message)
    await db.flush()
    
    # 使用 RAG 服务生成回答
    rag_service = RAGService(db)
    
    try:
        answer_data = await rag_service.generate_answer(
            question=data.content,
            conversation_id=conversation_id,
            org_id=current_user.org_id
        )
        
        # 保存助手回复
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=answer_data["answer"],
            source_refs=answer_data.get("sources", [])
        )
        db.add(assistant_message)
        
        # 更新对话信息
        conversation.message_count += 2
        conversation.last_message_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(assistant_message)
        
        return {
            "message_id": assistant_message.id,
            "answer": answer_data["answer"],
            "sources": answer_data.get("sources", []),
            "confidence": answer_data.get("confidence")
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"生成回答失败: {str(e)}")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除对话"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "对话删除成功"}


@router.post("/{conversation_id}/messages/{message_id}/feedback")
async def feedback_message(
    conversation_id: int,
    message_id: int,
    rating: int,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """对消息进行反馈"""
    
    # 验证消息归属
    result = await db.execute(
        select(Message).join(Conversation).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    message.rating = rating
    message.feedback = feedback
    
    await db.commit()
    
    return {"message": "反馈已保存"}

