"""
RAG (Retrieval Augmented Generation) 服务
检索增强生成服务，整合检索和 LLM
"""

from typing import List, Dict, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import openai

from app.models.chunk import Chunk
from app.models.file import File
from app.models.message import Message
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.security_service import SecurityService
from app.services.model_orchestrator import model_orchestrator, TaskType
from app.config import settings


class RAGService:
    """RAG 服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
        self.security_service = SecurityService(db)
        
        # 配置 OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        openai.api_base = settings.OPENAI_API_BASE
    
    async def generate_answer(
        self,
        question: str,
        conversation_id: int,
        org_id: int
    ) -> Dict:
        """生成答案（完整 RAG 流程）"""
        
        # 1. 生成问题的 embedding
        query_embedding = await self.embedding_service.embed_text(question)
        
        # 2. 向量检索 Top-N
        search_results = await self.vector_service.search(
            query_embedding=query_embedding,
            top_k=settings.RETRIEVAL_TOP_N
        )
        
        if not search_results:
            return {
                "answer": "抱歉，我在知识库中未找到相关信息。请确保已上传相关文档。",
                "sources": [],
                "confidence": 0.0
            }
        
        # 3. 获取 chunk 详细信息
        chunk_ids = [r["chunk_id"] for r in search_results]
        result = await self.db.execute(
            select(Chunk, File).join(File).where(
                Chunk.chunk_id.in_(chunk_ids),
                File.org_id == org_id
            )
        )
        chunks_with_files = result.all()
        
        # 4. 构建证据列表
        evidence_list = []
        for chunk, file in chunks_with_files:
            # 找到对应的相似度分数
            similarity = next(
                (r["similarity"] for r in search_results if r["chunk_id"] == chunk.chunk_id),
                0.0
            )
            
            # 过滤低相似度
            if similarity < settings.SIMILARITY_THRESHOLD:
                continue
            
            evidence_list.append({
                "chunk_id": chunk.chunk_id,
                "file_id": file.id,
                "file_name": file.original_filename,
                "page": chunk.page_number,
                "text": chunk.text,
                "similarity": similarity,
                "heading": chunk.heading
            })
        
        # 按相似度排序并取 Top-K
        evidence_list.sort(key=lambda x: x["similarity"], reverse=True)
        top_evidence = evidence_list[:settings.RETRIEVAL_TOP_K]
        
        if not top_evidence:
            return {
                "answer": "找到了一些相关文档，但相关性较低。请尝试换一个问题。",
                "sources": [],
                "confidence": 0.0
            }
        
        # 5. 获取对话历史
        conversation_history = await self._get_conversation_history(conversation_id)
        
        # 6. 构建 Prompt
        prompt = self._build_prompt(question, top_evidence, conversation_history)
        
        # 7. 调用 LLM 生成答案（使用模型调度器）
        try:
            messages = [{"role": "user", "content": prompt}]
            answer_text = await model_orchestrator.generate(
                messages=messages,
                task_type=TaskType.QA,
                fallback=True
            )
        except Exception as e:
            return {
                "answer": f"生成答案时出错: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "model_error": True
            }
        
        # 8. 安全检测
        security_check = self.security_service.check_sensitive_content(answer_text)
        
        # 如果检测到高风险内容，记录日志
        if security_check["has_sensitive"]:
            await self.security_service.log_sensitive_detection(
                content_type="answer",
                text=answer_text,
                detection_result=security_check
            )
            
            # 如果需要屏蔽
            if security_check["should_block"]:
                return {
                    "answer": "⚠️ 检测到敏感内容，该回答已被系统自动屏蔽。请重新表述您的问题。",
                    "sources": [],
                    "confidence": 0.0,
                    "security_warning": True
                }
        
        # 9. 计算置信度
        similarities = [e["similarity"] for e in top_evidence]
        confidence = self.security_service.calculate_confidence(similarities)
        
        # 10. 添加免责声明
        answer_with_disclaimer = self.security_service.add_disclaimer(answer_text)
        
        # 11. 构建来源引用（增强版）
        sources = [
            {
                "doc": e["file_name"],
                "file_id": e["file_id"],
                "page": e["page"],
                "paragraph": e["text"][:200] + "..." if len(e["text"]) > 200 else e["text"],
                "chunk_id": e["chunk_id"],
                "heading": e.get("heading"),
                "similarity": round(e["similarity"], 4),
                "relevance_score": round(e["similarity"] * 100, 2)  # 百分制
            }
            for e in top_evidence
        ]
        
        return {
            "answer": answer_with_disclaimer,
            "source": sources,  # 使用 source 而不是 sources（符合需求文档）
            "sources": sources,  # 同时保留 sources 以兼容旧版
            "confidence": round(confidence, 4),
            "confidence_level": self._get_confidence_level(confidence),
            "evidence_count": len(top_evidence),
            "security_check": security_check if security_check["has_sensitive"] else None,
            "metadata": {
                "retrieval_count": len(search_results),
                "filtered_count": len(evidence_list),
                "used_count": len(top_evidence)
            }
        }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """获取置信度等级"""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.8:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        elif confidence >= 0.6:
            return "low"
        else:
            return "very_low"
    
    async def _get_conversation_history(self, conversation_id: int, limit: int = 5) -> List[Dict]:
        """获取对话历史"""
        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(limit)
        )
        messages = result.scalars().all()
        
        # 反转顺序（从旧到新）
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in reversed(messages)
        ]
    
    def _build_prompt(
        self,
        question: str,
        evidence: List[Dict],
        history: List[Dict]
    ) -> str:
        """构建 Prompt"""
        
        # 系统提示
        system_prompt = """你是一个专业的文档助理，基于提供的证据回答用户问题。

**重要规则：**
1. 只基于提供的证据回答问题，不要使用外部知识
2. 如果证据不足以回答问题，请明确说明
3. 回答时引用证据来源（文件名和页码）
4. 保持回答简洁、准确、专业
5. 使用清晰的格式，如有必要使用列表或段落"""
        
        # 构建证据部分
        evidence_text = "\n\n".join([
            f"【证据 {i+1}】\n"
            f"来源：{e['file_name']}，第 {e['page']} 页\n"
            f"内容：{e['text']}"
            for i, e in enumerate(evidence)
        ])
        
        # 构建完整 Prompt
        full_prompt = f"""{system_prompt}

===== 证据材料 =====
{evidence_text}

===== 用户问题 =====
{question}

请基于以上证据回答问题："""
        
        return full_prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成答案"""
        
        if settings.LLM_PROVIDER == "openai":
            response = await openai.ChatCompletion.acreate(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            return response.choices[0].message.content
        
        else:
            raise ValueError(f"不支持的 LLM 提供商: {settings.LLM_PROVIDER}")
    
    async def stream_generate_answer(
        self,
        question: str,
        conversation_id: int,
        org_id: int
    ) -> AsyncGenerator[str, None]:
        """流式生成答案（实时输出）
        
        Yields:
            每个文本块
        """
        # 1-6步与普通生成相同（检索和准备）
        query_embedding = await self.embedding_service.embed_text(question)
        search_results = await self.vector_service.search(
            query_embedding=query_embedding,
            top_k=settings.RETRIEVAL_TOP_N
        )
        
        if not search_results:
            yield "抱歉，我在知识库中未找到相关信息。"
            return
        
        # 获取chunks和构建evidence
        chunk_ids = [r["chunk_id"] for r in search_results]
        result = await self.db.execute(
            select(Chunk, File).join(File).where(
                Chunk.chunk_id.in_(chunk_ids),
                File.org_id == org_id
            )
        )
        chunks_with_files = result.all()
        
        evidence_list = []
        for chunk, file in chunks_with_files:
            similarity = next(
                (r["similarity"] for r in search_results if r["chunk_id"] == chunk.chunk_id),
                0.0
            )
            
            if similarity < settings.SIMILARITY_THRESHOLD:
                continue
            
            evidence_list.append({
                "chunk_id": chunk.chunk_id,
                "file_id": file.id,
                "file_name": file.original_filename,
                "page": chunk.page_number,
                "text": chunk.text,
                "similarity": similarity,
                "heading": chunk.heading
            })
        
        evidence_list.sort(key=lambda x: x["similarity"], reverse=True)
        top_evidence = evidence_list[:settings.RETRIEVAL_TOP_K]
        
        if not top_evidence:
            yield "找到了一些相关文档，但相关性较低。请尝试换一个问题。"
            return
        
        # 构建Prompt
        conversation_history = await self._get_conversation_history(conversation_id)
        prompt = self._build_prompt(question, top_evidence, conversation_history)
        
        # 流式调用LLM（使用模型调度器）
        try:
            messages = [{"role": "user", "content": prompt}]
            
            async for chunk in model_orchestrator.stream_generate(
                messages=messages,
                task_type=TaskType.QA
            ):
                yield chunk
        
        except Exception as e:
            yield f"\n\n❌ 生成答案时出错: {str(e)}"

