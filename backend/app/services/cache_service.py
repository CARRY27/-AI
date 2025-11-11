"""
Redis 缓存服务
实现热问句缓存、向量召回结果缓存、session管理
"""

import redis
import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import timedelta

from app.config import settings


class CacheService:
    """缓存服务"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 缓存过期时间配置
        self.QUERY_CACHE_TTL = 3600  # 热问句缓存1小时
        self.VECTOR_CACHE_TTL = 1800  # 向量结果缓存30分钟
        self.SESSION_TTL = 86400  # Session缓存24小时
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [str(arg) for arg in args]
        key_str = ":".join(key_parts)
        return f"{prefix}:{key_str}"
    
    def _generate_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()
    
    # ========== 热问句缓存 ==========
    
    def get_query_cache(self, org_id: int, query: str) -> Optional[Dict[str, Any]]:
        """
        获取热问句缓存
        相似问题直接返回上次结果
        """
        query_hash = self._generate_hash(query)
        key = self._generate_key("query_cache", org_id, query_hash)
        
        cached_data = self.redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def set_query_cache(
        self, 
        org_id: int, 
        query: str, 
        answer: str,
        sources: List[Dict],
        confidence: float,
        ttl: Optional[int] = None
    ):
        """
        设置热问句缓存
        """
        query_hash = self._generate_hash(query)
        key = self._generate_key("query_cache", org_id, query_hash)
        
        cache_data = {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "cached": True
        }
        
        ttl = ttl or self.QUERY_CACHE_TTL
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(cache_data, ensure_ascii=False)
        )
    
    def invalidate_query_cache(self, org_id: int, query: Optional[str] = None):
        """
        失效查询缓存
        如果不指定query，清空该组织的所有查询缓存
        """
        if query:
            query_hash = self._generate_hash(query)
            key = self._generate_key("query_cache", org_id, query_hash)
            self.redis_client.delete(key)
        else:
            pattern = self._generate_key("query_cache", org_id, "*")
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
    
    # ========== 向量召回结果缓存 ==========
    
    def get_vector_cache(
        self, 
        org_id: int, 
        query_embedding: List[float],
        top_k: int = 5
    ) -> Optional[List[Dict]]:
        """
        获取向量召回结果缓存
        """
        # 使用embedding前10个元素作为key的一部分（避免key过长）
        embedding_signature = self._generate_hash(
            str(query_embedding[:10])
        )
        key = self._generate_key(
            "vector_cache", 
            org_id, 
            embedding_signature,
            top_k
        )
        
        cached_data = self.redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def set_vector_cache(
        self,
        org_id: int,
        query_embedding: List[float],
        chunks: List[Dict],
        top_k: int = 5,
        ttl: Optional[int] = None
    ):
        """
        设置向量召回结果缓存
        """
        embedding_signature = self._generate_hash(
            str(query_embedding[:10])
        )
        key = self._generate_key(
            "vector_cache",
            org_id,
            embedding_signature,
            top_k
        )
        
        ttl = ttl or self.VECTOR_CACHE_TTL
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(chunks, ensure_ascii=False)
        )
    
    def invalidate_vector_cache(self, org_id: int):
        """
        失效向量缓存（文档更新时调用）
        """
        pattern = self._generate_key("vector_cache", org_id, "*")
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    # ========== Session 管理 ==========
    
    def set_session(
        self, 
        user_id: int, 
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        设置用户 session
        """
        key = self._generate_key("session", user_id)
        ttl = ttl or self.SESSION_TTL
        
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(session_data, ensure_ascii=False)
        )
    
    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户 session
        """
        key = self._generate_key("session", user_id)
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def update_session(self, user_id: int, updates: Dict[str, Any]):
        """
        更新 session 中的部分字段
        """
        key = self._generate_key("session", user_id)
        session_data = self.get_session(user_id)
        
        if session_data:
            session_data.update(updates)
            ttl = self.redis_client.ttl(key)
            if ttl > 0:
                self.set_session(user_id, session_data, ttl)
    
    def delete_session(self, user_id: int):
        """
        删除用户 session（登出时调用）
        """
        key = self._generate_key("session", user_id)
        self.redis_client.delete(key)
    
    # ========== 热度统计 ==========
    
    def increment_query_count(self, org_id: int, query: str):
        """
        增加查询次数（用于统计热门问题）
        """
        query_hash = self._generate_hash(query)
        key = self._generate_key("query_stats", org_id)
        
        # 使用有序集合存储查询频率
        self.redis_client.zincrby(key, 1, query_hash)
        
        # 存储查询内容映射
        content_key = self._generate_key("query_content", org_id, query_hash)
        self.redis_client.setex(content_key, 86400 * 7, query)  # 保存7天
    
    def get_hot_queries(
        self, 
        org_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取热门问题
        """
        key = self._generate_key("query_stats", org_id)
        
        # 获取频率最高的查询
        hot_hashes = self.redis_client.zrevrange(key, 0, limit - 1, withscores=True)
        
        result = []
        for query_hash, count in hot_hashes:
            content_key = self._generate_key("query_content", org_id, query_hash)
            query_content = self.redis_client.get(content_key)
            
            if query_content:
                result.append({
                    "query": query_content,
                    "count": int(count)
                })
        
        return result
    
    # ========== 缓存统计 ==========
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        info = self.redis_client.info("stats")
        
        # 统计各类型缓存的键数量
        query_cache_count = len(self.redis_client.keys("query_cache:*"))
        vector_cache_count = len(self.redis_client.keys("vector_cache:*"))
        session_count = len(self.redis_client.keys("session:*"))
        
        return {
            "total_keys": self.redis_client.dbsize(),
            "query_cache_count": query_cache_count,
            "vector_cache_count": vector_cache_count,
            "session_count": session_count,
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": self._calculate_hit_rate(
                info.get("keyspace_hits", 0),
                info.get("keyspace_misses", 0)
            )
        }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total, 4)
    
    # ========== 限流 ==========
    
    def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> bool:
        """
        检查限流
        
        Args:
            key: 限流键（通常是 user_id 或 ip）
            limit: 窗口内最大请求数
            window: 时间窗口（秒）
        
        Returns:
            是否允许请求
        """
        rate_key = self._generate_key("rate_limit", key)
        
        # 使用滑动窗口限流
        current_count = self.redis_client.incr(rate_key)
        
        if current_count == 1:
            self.redis_client.expire(rate_key, window)
        
        return current_count <= limit


# 全局缓存服务实例
cache_service = CacheService()

