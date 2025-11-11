"""
压力测试和负载测试
使用 locust 进行性能测试
"""

import pytest
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestLoadTesting:
    """负载测试"""
    
    def test_concurrent_api_calls(self, client, auth_headers):
        """测试并发 API 调用"""
        
        def make_request(endpoint):
            """发起单个请求"""
            start = time.time()
            response = client.get(endpoint, headers=auth_headers)
            elapsed = time.time() - start
            return {
                "endpoint": endpoint,
                "status": response.status_code,
                "time": elapsed
            }
        
        # 模拟100个并发请求
        endpoints = ["/api/conversations/"] * 100
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == 200)
        avg_time = sum(r["time"] for r in results) / len(results)
        max_time = max(r["time"] for r in results)
        
        print(f"\n=== 负载测试结果 ===")
        print(f"总请求数: {len(results)}")
        print(f"成功请求: {success_count}")
        print(f"成功率: {success_count/len(results)*100:.2f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"QPS: {len(results)/total_time:.2f}")
        print(f"平均响应: {avg_time:.3f}秒")
        print(f"最大响应: {max_time:.3f}秒")
        
        # 断言
        assert success_count >= 95  # 至少95%成功
        assert avg_time < 1.0  # 平均响应时间 < 1秒
    
    def test_database_connection_pool(self, client, auth_headers):
        """测试数据库连接池压力"""
        
        def create_and_query():
            """创建对话并查询"""
            # 创建对话
            conv = client.post(
                "/api/conversations/",
                json={"title": f"压力测试 {random.randint(1000, 9999)}"},
                headers=auth_headers
            )
            
            if conv.status_code == 200:
                conv_id = conv.json()["id"]
                # 查询对话
                detail = client.get(
                    f"/api/conversations/{conv_id}",
                    headers=auth_headers
                )
                return detail.status_code == 200
            return False
        
        # 50个并发数据库操作
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_query) for _ in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        
        print(f"\n数据库压力测试成功率: {success_rate*100:.2f}%")
        
        assert success_rate >= 0.9  # 至少90%成功
    
    def test_memory_usage_under_load(self, client, auth_headers):
        """测试高负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行1000次请求
        for i in range(1000):
            client.get("/api/conversations/", headers=auth_headers)
            
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"\n请求 {i}: 内存使用 {current_memory:.2f} MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"\n=== 内存使用 ===")
        print(f"初始: {initial_memory:.2f} MB")
        print(f"最终: {final_memory:.2f} MB")
        print(f"增长: {memory_increase:.2f} MB")
        
        # 内存增长不应超过100MB
        assert memory_increase < 100


class TestStressTesting:
    """压力测试"""
    
    def test_sustained_load(self, client, auth_headers):
        """测试持续负载"""
        duration = 10  # 10秒持续测试
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                response = client.get("/api/conversations/", headers=auth_headers)
                if response.status_code == 200:
                    request_count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
        
        elapsed = time.time() - start_time
        qps = request_count / elapsed
        error_rate = errors / (request_count + errors) if (request_count + errors) > 0 else 0
        
        print(f"\n=== 持续负载测试 ===")
        print(f"持续时间: {elapsed:.2f}秒")
        print(f"成功请求: {request_count}")
        print(f"失败请求: {errors}")
        print(f"QPS: {qps:.2f}")
        print(f"错误率: {error_rate*100:.2f}%")
        
        assert qps > 5  # 至少 5 QPS
        assert error_rate < 0.05  # 错误率 < 5%
    
    def test_spike_load(self, client, auth_headers):
        """测试突发负载"""
        # 模拟流量突增：瞬间100个请求
        results = []
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(
                    client.get,
                    "/api/conversations/",
                    headers=auth_headers
                )
                for _ in range(100)
            ]
            
            for future in as_completed(futures):
                try:
                    response = future.result()
                    results.append(response.status_code == 200)
                except Exception:
                    results.append(False)
        
        elapsed = time.time() - start
        success_rate = sum(results) / len(results)
        
        print(f"\n=== 突发负载测试 ===")
        print(f"请求数: {len(results)}")
        print(f"耗时: {elapsed:.2f}秒")
        print(f"成功率: {success_rate*100:.2f}%")
        
        # 突发负载下也应该有较高成功率
        assert success_rate >= 0.85
    
    def test_gradual_load_increase(self, client, auth_headers):
        """测试逐渐增加负载"""
        load_levels = [5, 10, 20, 30]
        
        for load in load_levels:
            start = time.time()
            
            with ThreadPoolExecutor(max_workers=load) as executor:
                futures = [
                    executor.submit(
                        client.get,
                        "/api/conversations/",
                        headers=auth_headers
                    )
                    for _ in range(load * 2)
                ]
                
                results = [f.result().status_code == 200 for f in as_completed(futures)]
            
            elapsed = time.time() - start
            success_rate = sum(results) / len(results)
            
            print(f"\n负载级别 {load}: 成功率 {success_rate*100:.2f}%, 耗时 {elapsed:.2f}秒")
            
            assert success_rate >= 0.9


class TestResourceExhaustion:
    """测试资源耗尽场景"""
    
    def test_large_response_handling(self, client, db_session, test_user, test_org, auth_headers):
        """测试处理大量数据"""
        from app.models.conversation import Conversation
        
        # 创建大量对话
        conversations = []
        for i in range(200):
            conv = Conversation(
                user_id=test_user.id,
                org_id=test_org.id,
                title=f"对话 {i}"
            )
            conversations.append(conv)
        
        db_session.add_all(conversations)
        db_session.commit()
        
        # 请求大分页
        start = time.time()
        response = client.get(
            "/api/conversations/?page=1&page_size=100",
            headers=auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0  # 即使大分页也应该快
        
        print(f"\n查询200条记录(分页100)耗时: {elapsed:.3f}秒")
    
    def test_deep_pagination(self, client, auth_headers):
        """测试深度分页"""
        # 请求很后面的页
        response = client.get(
            "/api/conversations/?page=100&page_size=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # 可能没有数据，但不应该报错

