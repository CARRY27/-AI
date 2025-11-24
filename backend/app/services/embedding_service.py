"""
Embedding 服务
将文本转换为向量
"""

from typing import List
import openai
from app.config import settings


class EmbeddingService:
    """Embedding 服务"""
    
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE

        # 如果配置为 openai 但未提供 API Key，则自动回退到本地模型
        if self.provider == "openai" and not settings.OPENAI_API_KEY:
            print("⚠️ 未检测到 OPENAI_API_KEY，Embedding 将回退为本地模型 (sentence-transformers)")
            self.provider = "local"
            # 选择一个轻量通用的本地模型名称
            self.model = "all-MiniLM-L6-v2"
        
        if self.provider == "openai":
            openai.api_key = settings.OPENAI_API_KEY
            openai.api_base = settings.OPENAI_API_BASE
    
    async def embed_text(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        embeddings = await self.embed_batch([text])
        return embeddings[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        
        if self.provider == "openai":
            return await self._embed_openai(texts)
        if self.provider == "local":
            return await self._embed_local(texts)
        raise ValueError(f"不支持的 embedding 提供商: {self.provider}")
    
    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """使用 OpenAI API 生成 embeddings"""
        
        all_embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await openai.Embedding.acreate(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item["embedding"] for item in response["data"]]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"OpenAI Embedding 错误: {e}")
                raise
        
        return all_embeddings
    
    async def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型生成 embeddings（备用方案）"""
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(self.model)
        embeddings = model.encode(texts, convert_to_numpy=True)
        
        return embeddings.tolist()

