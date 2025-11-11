"""
Locust 压力测试脚本
用于模拟真实用户负载

运行方式:
    locust -f tests/locustfile.py --host=http://localhost:8000

然后访问 http://localhost:8089 打开 Web UI
"""

from locust import HttpUser, task, between, events
import random
import json


class DocAgentUser(HttpUser):
    """模拟 DocAgent 用户行为"""
    
    # 用户请求间隔：1-3秒
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        用户开始时执行：登录
        """
        # 登录获取 token
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": "admin@example.com",
                "password": "admin123"
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"登录失败: {response.status_code}")
            self.token = None
            self.headers = {}
    
    @task(5)
    def view_conversations(self):
        """查看对话列表（权重5 - 高频操作）"""
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="/api/conversations/ [列表]"
        )
    
    @task(3)
    def create_conversation(self):
        """创建新对话（权重3）"""
        response = self.client.post(
            "/api/conversations/",
            json={"title": f"压力测试对话 {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="/api/conversations/ [创建]"
        )
        
        if response.status_code == 200:
            # 保存对话ID供后续使用
            if not hasattr(self, 'conversation_ids'):
                self.conversation_ids = []
            self.conversation_ids.append(response.json()["id"])
    
    @task(10)
    def send_message(self):
        """发送消息（权重10 - 核心操作）"""
        if not hasattr(self, 'conversation_ids') or not self.conversation_ids:
            # 先创建对话
            self.create_conversation()
            return
        
        conv_id = random.choice(self.conversation_ids)
        questions = [
            "DocAgent 是什么？",
            "如何上传文档？",
            "支持哪些文件格式？",
            "如何提高准确度？",
            "系统有什么限制？"
        ]
        
        self.client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": random.choice(questions)},
            headers=self.headers,
            name="/api/conversations/{id}/messages [发送]"
        )
    
    @task(2)
    def view_files(self):
        """查看文件列表（权重2）"""
        self.client.get(
            "/api/files/",
            headers=self.headers,
            name="/api/files/ [列表]"
        )
    
    @task(4)
    def submit_feedback(self):
        """提交反馈（权重4）"""
        # 需要先有消息才能反馈
        # 这里简化，直接测试 API
        message_id = random.randint(1, 100)
        
        self.client.post(
            f"/api/feedback/messages/{message_id}",
            json={
                "feedback_type": random.choice(["positive", "negative"]),
                "rating": random.randint(1, 5)
            },
            headers=self.headers,
            name="/api/feedback/messages/{id} [提交]"
        )
    
    @task(1)
    def view_feedback_stats(self):
        """查看反馈统计（权重1）"""
        self.client.get(
            "/api/feedback/stats/org?days=30",
            headers=self.headers,
            name="/api/feedback/stats/org [统计]"
        )


class AdminUser(HttpUser):
    """模拟管理员用户"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """管理员登录"""
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": "admin@example.com",
                "password": "admin123"
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_admin_stats(self):
        """查看系统统计"""
        self.client.get(
            "/api/admin/stats",
            headers=self.headers,
            name="/api/admin/stats"
        )
    
    @task(2)
    def view_daily_feedback(self):
        """查看每日反馈"""
        self.client.get(
            "/api/feedback/stats/daily?days=7",
            headers=self.headers,
            name="/api/feedback/stats/daily"
        )
    
    @task(1)
    def view_negative_feedback(self):
        """查看负面反馈"""
        self.client.get(
            "/api/feedback/negative/recent?limit=20",
            headers=self.headers,
            name="/api/feedback/negative/recent"
        )


class ApiHealthCheck(HttpUser):
    """API 健康检查"""
    
    wait_time = between(5, 10)
    
    @task
    def health_check(self):
        """健康检查端点"""
        self.client.get("/health", name="/health")
    
    @task
    def root_endpoint(self):
        """根端点"""
        self.client.get("/", name="/")


# ========== 事件钩子 ==========

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print("\n" + "="*60)
    print("🚀 DocAgent 压力测试开始")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时执行"""
    print("\n" + "="*60)
    print("✅ DocAgent 压力测试完成")
    print("="*60)
    
    # 输出统计摘要
    stats = environment.stats
    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"失败数: {stats.total.num_failures}")
    print(f"成功率: {(1 - stats.total.fail_ratio) * 100:.2f}%")
    print(f"平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"中位数: {stats.total.median_response_time:.2f}ms")
    print(f"95分位: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99分位: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """每个请求完成时执行"""
    if exception:
        print(f"❌ 请求失败: {name} - {exception}")

