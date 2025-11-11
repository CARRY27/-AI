"""
文档切片服务
将长文档切分成适合向量化的小块
"""

from typing import List
import tiktoken
from app.config import settings


class ChunkingService:
    """文档切片服务"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量"""
        return len(self.encoding.encode(text))
    
    def chunk_by_tokens(self, text: str, metadata: dict = None) -> List[dict]:
        """按 token 数量切分文本"""
        chunks = []
        tokens = self.encoding.encode(text)
        
        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append({
                "text": chunk_text,
                "token_count": len(chunk_tokens),
                "start_offset": start,
                "end_offset": end,
                "metadata": metadata or {}
            })
            
            # 移动到下一个块，考虑重叠
            start = end - self.chunk_overlap
        
        return chunks
    
    def chunk_by_sentences(self, text: str, metadata: dict = None) -> List[dict]:
        """按句子切分文本（保持语义完整性）"""
        import re
        
        # 简单的句子分割（支持中英文）
        sentences = re.split(r'([。！？\.!?])', text)
        sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2])]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # 当前块已满，保存并开始新块
                chunk_text = ''.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "token_count": current_tokens,
                    "metadata": metadata or {}
                })
                
                # 保留重叠部分
                overlap_sentences = []
                overlap_tokens = 0
                for s in reversed(current_chunk):
                    s_tokens = self.count_tokens(s)
                    if overlap_tokens + s_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # 添加最后一个块
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "token_count": current_tokens,
                "metadata": metadata or {}
            })
        
        return chunks
    
    def chunk_text(self, text: str, strategy: str = "sentences", metadata: dict = None) -> List[dict]:
        """切分文本
        
        Args:
            text: 要切分的文本
            strategy: 切分策略 ("tokens" 或 "sentences")
            metadata: 附加元数据
        
        Returns:
            切片列表
        """
        if strategy == "tokens":
            return self.chunk_by_tokens(text, metadata)
        else:
            return self.chunk_by_sentences(text, metadata)

