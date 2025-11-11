"""
向量数据库服务
支持 FAISS、Milvus、Chroma
"""

import os
import pickle
from typing import List, Dict, Optional
import numpy as np
import faiss
from app.config import settings


class VectorService:
    """向量数据库服务"""
    
    def __init__(self):
        self.db_type = settings.VECTOR_DB_TYPE
        self.dimension = settings.EMBEDDING_DIMENSION
        
        if self.db_type == "faiss":
            self.index = self._init_faiss()
            self.metadata_store = {}  # 存储元数据
        elif self.db_type == "milvus":
            self.index = self._init_milvus()
        elif self.db_type == "chroma":
            self.index = self._init_chroma()
        else:
            raise ValueError(f"不支持的向量数据库类型: {self.db_type}")
    
    def _init_faiss(self):
        """初始化 FAISS 索引"""
        index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
        metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.pkl")
        
        # 确保目录存在
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        
        if os.path.exists(index_path):
            # 加载现有索引
            index = faiss.read_index(index_path)
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    self.metadata_store = pickle.load(f)
        else:
            # 创建新索引（使用 L2 距离）
            index = faiss.IndexFlatL2(self.dimension)
            # 或使用 Inner Product（余弦相似度）
            # index = faiss.IndexFlatIP(self.dimension)
        
        return index
    
    def _save_faiss(self):
        """保存 FAISS 索引"""
        index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
        metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata_store, f)
    
    def _init_milvus(self):
        """初始化 Milvus 连接"""
        from pymilvus import connections, Collection
        
        connections.connect(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # 这里需要创建 collection（简化示例）
        # 实际应用需要更完善的配置
        return None
    
    def _init_chroma(self):
        """初始化 Chroma 客户端"""
        import chromadb
        
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        collection = client.get_or_create_collection("docagent")
        
        return collection
    
    async def add_vectors(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict]
    ):
        """添加向量到数据库"""
        
        if self.db_type == "faiss":
            await self._add_faiss(chunk_ids, embeddings, metadata)
        elif self.db_type == "chroma":
            await self._add_chroma(chunk_ids, embeddings, metadata)
        else:
            raise NotImplementedError(f"未实现 {self.db_type} 的添加功能")
    
    async def _add_faiss(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict]
    ):
        """添加向量到 FAISS"""
        vectors = np.array(embeddings, dtype=np.float32)
        
        # 归一化（如果使用 Inner Product）
        # faiss.normalize_L2(vectors)
        
        # 获取当前索引大小作为起始 ID
        start_idx = self.index.ntotal
        
        # 添加向量
        self.index.add(vectors)
        
        # 保存元数据
        for i, chunk_id in enumerate(chunk_ids):
            self.metadata_store[start_idx + i] = {
                "chunk_id": chunk_id,
                **metadata[i]
            }
        
        # 保存到磁盘
        self._save_faiss()
    
    async def _add_chroma(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict]
    ):
        """添加向量到 Chroma"""
        self.index.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadata
        )
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """搜索相似向量"""
        
        if self.db_type == "faiss":
            return await self._search_faiss(query_embedding, top_k)
        elif self.db_type == "chroma":
            return await self._search_chroma(query_embedding, top_k, filters)
        else:
            raise NotImplementedError(f"未实现 {self.db_type} 的搜索功能")
    
    async def _search_faiss(
        self,
        query_embedding: List[float],
        top_k: int
    ) -> List[Dict]:
        """在 FAISS 中搜索"""
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # 归一化（如果使用 Inner Product）
        # faiss.normalize_L2(query_vector)
        
        # 搜索
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS 返回 -1 表示未找到
                continue
            
            metadata = self.metadata_store.get(int(idx), {})
            results.append({
                "chunk_id": metadata.get("chunk_id"),
                "distance": float(dist),
                "similarity": 1 / (1 + float(dist)),  # 转换为相似度分数
                "metadata": metadata
            })
        
        return results
    
    async def _search_chroma(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """在 Chroma 中搜索"""
        results = self.index.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "distance": results['distances'][0][i],
                "similarity": 1 - results['distances'][0][i],
                "metadata": results['metadatas'][0][i]
            })
        
        return formatted_results
    
    async def delete_file_vectors(self, file_id: int):
        """删除文件的所有向量"""
        
        if self.db_type == "faiss":
            # FAISS 不支持直接删除，需要重建索引
            # 这里简化处理，实际应用需要更复杂的逻辑
            new_metadata = {
                k: v for k, v in self.metadata_store.items()
                if v.get("file_id") != file_id
            }
            
            if len(new_metadata) < len(self.metadata_store):
                # 需要重建索引
                self.metadata_store = new_metadata
                self._save_faiss()
        
        elif self.db_type == "chroma":
            # Chroma 支持按元数据删除
            self.index.delete(where={"file_id": file_id})

