"""
流式输出服务
支持 SSE (Server-Sent Events) 实时输出
"""

import asyncio
from typing import AsyncGenerator
import openai
from app.config import settings


class StreamingService:
    """流式输出服务"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        openai.api_base = settings.OPENAI_API_BASE
    
    async def stream_chat_completion(
        self,
        prompt: str,
        model: str = None
    ) -> AsyncGenerator[str, None]:
        """流式生成聊天回复
        
        Yields:
            每个token或文本块
        """
        model = model or settings.LLM_MODEL
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                stream=True  # 启用流式输出
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.get("content"):
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"\n\n❌ 生成答案时出错: {str(e)}"
    
    async def format_sse_message(self, data: str, event: str = "message") -> str:
        """格式化为 SSE 消息格式"""
        return f"event: {event}\ndata: {data}\n\n"

