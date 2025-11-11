"""
对话服务
管理对话会话和消息
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:
    """对话服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_conversation(self, user_id: int, org_id: int, title: str = None) -> Conversation:
        """创建新对话"""
        conversation = Conversation(
            user_id=user_id,
            org_id=org_id,
            title=title or "新对话"
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        source_refs: list = None
    ) -> Message:
        """添加消息到对话"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            source_refs=source_refs or []
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message

