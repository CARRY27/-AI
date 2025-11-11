"""
实时系统测试脚本
直接测试运行中的 DocAgent 系统（不使用测试数据库）

运行方式:
    python backend/tests/test_live_system.py
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any


class LiveSystemTester:
    """实时系统测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {}
        self.test_results = []
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }
        symbol = symbols.get(level, "•")
        print(f"[{timestamp}] {symbol} {message}")
    
    def run_test(self, name: str, func):
        """运行单个测试"""
        self.log(f"开始测试: {name}", "TEST")
        start = time.time()
        try:
            result = func()
            elapsed = time.time() - start
            self.log(f"测试通过: {name} ({elapsed:.2f}s)", "SUCCESS")
            self.test_results.append({
                "name": name,
                "success": True,
                "elapsed": elapsed
            })
            return result
        except AssertionError as e:
            elapsed = time.time() - start
            self.log(f"测试失败: {name} - {e}", "ERROR")
            self.test_results.append({
                "name": name,
                "success": False,
                "elapsed": elapsed,
                "error": str(e)
            })
            return None
        except Exception as e:
            elapsed = time.time() - start
            self.log(f"测试错误: {name} - {e}", "ERROR")
            self.test_results.append({
                "name": name,
                "success": False,
                "elapsed": elapsed,
                "error": str(e)
            })
            return None
    
    def _test_health(self):
        """测试健康检查端点"""
        response = requests.get(f"{self.base_url}/health", timeout=5)
        assert response.status_code == 200, f"健康检查失败: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy", "系统状态不健康"
        
        self.log(f"系统版本: {data.get('version', 'unknown')}")
        self.log(f"环境: {data.get('environment', 'unknown')}")
        return data
    
    def _test_login(self):
        """测试登录功能"""
        response = requests.post(
            f"{self.api_url}/auth/login",
            data={
                "username": "admin@example.com",
                "password": "admin123"
            },
            timeout=10
        )
        
        assert response.status_code == 200, f"登录失败: {response.status_code}"
        
        data = response.json()
        assert "access_token" in data, "响应中没有 access_token"
        
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        self.log(f"登录成功，用户: {data.get('username', 'admin')}")
        return data
    
    def _test_create_conversation(self):
        """测试创建对话"""
        response = requests.post(
            f"{self.api_url}/conversations/",
            json={"title": f"测试对话 {datetime.now().strftime('%H:%M:%S')}"},
            headers=self.headers,
            timeout=10
        )
        
        assert response.status_code in [200, 201], f"创建对话失败: {response.status_code}"
        
        data = response.json()
        assert "id" in data, "响应中没有 id"
        
        self.conversation_id = data["id"]
        self.log(f"创建对话成功，ID: {self.conversation_id}")
        return data
    
    def _test_list_conversations(self):
        """测试获取对话列表"""
        response = requests.get(
            f"{self.api_url}/conversations/",
            headers=self.headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"获取列表失败: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "响应不是列表"
        
        self.log(f"对话列表包含 {len(data)} 条记录")
        return data
    
    def _test_list_files(self):
        """测试获取文件列表"""
        response = requests.get(
            f"{self.api_url}/files/",
            headers=self.headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"获取文件列表失败: {response.status_code}"
        
        data = response.json()
        files = data.get("files", [])
        total = data.get("total", 0)
        
        self.log(f"文件列表包含 {total} 个文件")
        return files
    
    def _test_submit_feedback(self):
        """测试提交反馈"""
        # 使用已知的测试消息ID（由create_test_data.py创建）
        # 尝试几个可能的ID
        test_message_ids = [4, 6, 8, 2]
        
        for message_id in test_message_ids:
            try:
                response = requests.post(
                    f"{self.api_url}/feedback/messages/{message_id}",
                    json={
                        "feedback_type": "positive",
                        "rating": 5,
                        "comment": "自动化测试 - 正面反馈"
                    },
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"提交正面反馈成功 (消息ID: {message_id})")
                    return response.json()
                elif response.status_code == 404:
                    continue  # 尝试下一个ID
                else:
                    self.log(f"消息ID {message_id} 返回 {response.status_code}: {response.text[:100]}", "WARNING")
            except Exception as e:
                self.log(f"消息ID {message_id} 测试失败: {e}", "WARNING")
                continue
        
        self.log("没有可用的消息进行反馈测试（请先运行: docker-compose exec backend python create_test_data.py）", "WARNING")
        return None
    
    def _test_get_feedback_stats(self):
        """测试获取反馈统计"""
        response = requests.get(
            f"{self.api_url}/feedback/stats/org?days=30",
            headers=self.headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"获取统计失败: {response.status_code}"
        
        data = response.json()
        assert "total_feedbacks" in data
        assert "satisfaction_rate" in data
        
        self.log(f"反馈统计 - 总数: {data['total_feedbacks']}, 满意度: {data['satisfaction_rate']*100:.1f}%")
        return data
    
    def _test_response_times(self):
        """测试各端点响应时间"""
        endpoints = [
            "/api/conversations/",
            "/api/files/",
            "/api/feedback/stats/org"
        ]
        
        times = {}
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=10
            )
            elapsed = time.time() - start
            times[endpoint] = elapsed
            
            self.log(f"{endpoint}: {elapsed*1000:.0f}ms")
        
        slow_endpoints = [ep for ep, t in times.items() if t > 1.0]
        assert len(slow_endpoints) == 0, f"慢端点: {slow_endpoints}"
        return times
    
    def _test_concurrent_requests(self):
        """测试并发请求"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def make_request():
            response = requests.get(
                f"{self.api_url}/conversations/",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(results)
        success_rate = success_count / len(results)
        
        self.log(f"并发测试: {success_count}/{len(results)} 成功 ({success_rate*100:.1f}%)")
        
        assert success_rate >= 0.95, f"成功率过低: {success_rate*100:.1f}%"
        return success_rate
    
    def run(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("  DocAgent 实时系统测试")
        print(f"  目标: {self.base_url}")
        print("="*80 + "\n")
        
        # 按顺序执行测试
        self.run_test("系统健康检查", self._test_health)
        self.run_test("用户登录", self._test_login)
        
        if self.token:
            self.run_test("创建对话", self._test_create_conversation)
            self.run_test("查看对话列表", self._test_list_conversations)
            self.run_test("查看文件列表", self._test_list_files)
            self.run_test("提交反馈", self._test_submit_feedback)
            self.run_test("获取反馈统计", self._test_get_feedback_stats)
            self.run_test("API响应时间", self._test_response_times)
            self.run_test("并发请求", self._test_concurrent_requests)
        else:
            self.log("登录失败，跳过后续测试", "WARNING")
        
        # 生成报告
        return self.generate_summary()
    
    def generate_summary(self):
        """生成测试摘要"""
        print("\n" + "="*80)
        print("📊 测试摘要")
        print("="*80 + "\n")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%\n")
        
        if failed > 0:
            print("失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['name']}")
                    if "error" in result:
                        print(f"    错误: {result['error']}")
        
        print("\n" + "="*80)
        
        # 返回结果
        return failed == 0


def main():
    """主函数"""
    import sys
    
    # 可以从命令行参数指定URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = LiveSystemTester(base_url)
    success = tester.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

