"""
缓存服务 - 单元测试
测试 Redis 缓存功能
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock


class TestCacheService:
    """测试缓存服务基础功能"""
    
    @patch('app.services.cache_service.redis.Redis')
    def test_query_cache_set_and_get(self, mock_redis):
        """测试查询缓存的设置和获取"""
        from app.services.cache_service import CacheService
        
        # Mock Redis 客户端
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 设置缓存
        cache.set_query_cache(
            org_id=1,
            query="测试问题",
            answer="测试答案",
            sources=[],
            confidence=0.85
        )
        
        # 验证 setex 被调用
        assert mock_client.setex.called
        
        # Mock get 返回
        mock_client.get.return_value = '{"answer":"测试答案","sources":[],"confidence":0.85,"cached":true}'
        
        # 获取缓存
        result = cache.get_query_cache(org_id=1, query="测试问题")
        
        assert result is not None
        assert result["answer"] == "测试答案"
        assert result["cached"] is True
    
    @patch('app.services.cache_service.redis.Redis')
    def test_cache_miss(self, mock_redis):
        """测试缓存未命中"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None
        
        cache = CacheService()
        result = cache.get_query_cache(org_id=1, query="不存在的问题")
        
        assert result is None
    
    @patch('app.services.cache_service.redis.Redis')
    def test_cache_invalidation(self, mock_redis):
        """测试缓存失效"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 失效特定缓存
        cache.invalidate_query_cache(org_id=1, query="测试问题")
        assert mock_client.delete.called
        
        # 失效组织所有缓存
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        cache.invalidate_query_cache(org_id=1)
        
        # 应该调用 keys 和 delete
        assert mock_client.keys.called
        assert mock_client.delete.called
    
    @patch('app.services.cache_service.redis.Redis')
    def test_vector_cache(self, mock_redis):
        """测试向量缓存"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 设置向量缓存
        embedding = [0.1] * 1536
        chunks = [{"content": "chunk1"}, {"content": "chunk2"}]
        
        cache.set_vector_cache(
            org_id=1,
            query_embedding=embedding,
            chunks=chunks,
            top_k=5
        )
        
        assert mock_client.setex.called
    
    @patch('app.services.cache_service.redis.Redis')
    def test_session_management(self, mock_redis):
        """测试 Session 管理"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 设置 session
        session_data = {
            "username": "testuser",
            "org_id": 1,
            "role": "member"
        }
        
        cache.set_session(user_id=1, session_data=session_data)
        assert mock_client.setex.called
        
        # 获取 session
        import json
        mock_client.get.return_value = json.dumps(session_data)
        
        result = cache.get_session(user_id=1)
        assert result["username"] == "testuser"
        assert result["org_id"] == 1
        
        # 删除 session
        cache.delete_session(user_id=1)
        assert mock_client.delete.called
    
    @patch('app.services.cache_service.redis.Redis')
    def test_hot_queries_tracking(self, mock_redis):
        """测试热门查询追踪"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 增加查询计数
        cache.increment_query_count(org_id=1, query="热门问题")
        
        assert mock_client.zincrby.called
        assert mock_client.setex.called
        
        # 获取热门查询
        mock_client.zrevrange.return_value = [
            (b"hash1", 10.0),
            (b"hash2", 5.0)
        ]
        mock_client.get.side_effect = ["热门问题1", "热门问题2"]
        
        hot_queries = cache.get_hot_queries(org_id=1, limit=10)
        
        assert len(hot_queries) == 2
        assert hot_queries[0]["query"] == "热门问题1"
        assert hot_queries[0]["count"] == 10
    
    @patch('app.services.cache_service.redis.Redis')
    def test_rate_limiting(self, mock_redis):
        """测试限流功能"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 第一次请求
        mock_client.incr.return_value = 1
        allowed = cache.check_rate_limit(key="user:1", limit=10, window=60)
        
        assert allowed is True
        assert mock_client.incr.called
        assert mock_client.expire.called
        
        # 超过限制
        mock_client.incr.return_value = 11
        allowed = cache.check_rate_limit(key="user:1", limit=10, window=60)
        
        assert allowed is False


class TestCachePerformance:
    """测试缓存性能"""
    
    @patch('app.services.cache_service.redis.Redis')
    def test_cache_hit_rate_calculation(self, mock_redis):
        """测试缓存命中率计算"""
        from app.services.cache_service import CacheService
        
        cache = CacheService()
        
        # 测试计算逻辑
        hit_rate = cache._calculate_hit_rate(hits=75, misses=25)
        assert hit_rate == 0.75
        
        # 零除处理
        hit_rate = cache._calculate_hit_rate(hits=0, misses=0)
        assert hit_rate == 0.0
    
    @patch('app.services.cache_service.redis.Redis')
    def test_key_generation(self, mock_redis):
        """测试缓存键生成"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 测试键生成的一致性
        key1 = cache._generate_key("prefix", 1, "test")
        key2 = cache._generate_key("prefix", 1, "test")
        
        assert key1 == key2
        assert key1 == "prefix:1:test"
        
        # 测试哈希生成
        hash1 = cache._generate_hash("相同内容")
        hash2 = cache._generate_hash("相同内容")
        hash3 = cache._generate_hash("不同内容")
        
        assert hash1 == hash2
        assert hash1 != hash3


class TestCacheEdgeCases:
    """测试缓存边缘情况"""
    
    @patch('app.services.cache_service.redis.Redis')
    def test_large_cache_value(self, mock_redis):
        """测试大数据缓存"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 大量数据
        large_answer = "A" * 100000  # 100KB
        large_sources = [{"content": "x" * 1000} for _ in range(100)]
        
        cache.set_query_cache(
            org_id=1,
            query="大数据测试",
            answer=large_answer,
            sources=large_sources,
            confidence=0.9
        )
        
        # 应该成功调用
        assert mock_client.setex.called
    
    @patch('app.services.cache_service.redis.Redis')
    def test_special_characters_in_cache_key(self, mock_redis):
        """测试缓存键中的特殊字符"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 包含特殊字符的查询
        special_queries = [
            "如何使用 ? 符号",
            "价格是 $100",
            "路径: C:\\Users\\test",
            "表达式: a > b && c < d"
        ]
        
        for query in special_queries:
            cache.set_query_cache(
                org_id=1,
                query=query,
                answer="测试答案",
                sources=[],
                confidence=0.8
            )
            
            assert mock_client.setex.called
            mock_client.reset_mock()
    
    @patch('app.services.cache_service.redis.Redis')
    def test_cache_expiration(self, mock_redis):
        """测试缓存过期"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # 设置自定义TTL
        cache.set_query_cache(
            org_id=1,
            query="测试",
            answer="答案",
            sources=[],
            confidence=0.8,
            ttl=600  # 10分钟
        )
        
        # 验证TTL参数
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 600  # TTL = 600秒
    
    @patch('app.services.cache_service.redis.Redis')
    def test_unicode_in_cache(self, mock_redis):
        """测试 Unicode 字符缓存"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        cache = CacheService()
        
        # Unicode 内容
        unicode_answer = "这是中文回答 🎉 with emoji 和 العربية"
        
        cache.set_query_cache(
            org_id=1,
            query="Unicode测试",
            answer=unicode_answer,
            sources=[],
            confidence=0.9
        )
        
        # 验证调用
        assert mock_client.setex.called


class TestCacheStats:
    """测试缓存统计"""
    
    @patch('app.services.cache_service.redis.Redis')
    def test_get_cache_stats(self, mock_redis):
        """测试获取缓存统计"""
        from app.services.cache_service import CacheService
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        # Mock Redis info 响应
        mock_client.info.return_value = {
            "keyspace_hits": 1000,
            "keyspace_misses": 200
        }
        
        # Mock dbsize
        mock_client.dbsize.return_value = 1500
        
        # Mock keys 查询
        mock_client.keys.side_effect = [
            ["key1", "key2"],  # query_cache
            ["key3"],          # vector_cache
            ["key4", "key5", "key6"]  # session
        ]
        
        cache = CacheService()
        stats = cache.get_cache_stats()
        
        assert stats["total_keys"] == 1500
        assert stats["query_cache_count"] == 2
        assert stats["vector_cache_count"] == 1
        assert stats["session_count"] == 3
        assert stats["hits"] == 1000
        assert stats["misses"] == 200
        assert 0.8 <= stats["hit_rate"] <= 0.85  # 1000/(1000+200) ≈ 0.833

