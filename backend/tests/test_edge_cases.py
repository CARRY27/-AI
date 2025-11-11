"""
边缘测试（Edge Case Testing）
测试边界条件、异常情况、极端场景
"""

import pytest
from datetime import datetime, timedelta


class TestInputBoundaries:
    """测试输入边界"""
    
    def test_empty_feedback_comment(self, client, test_message, auth_headers):
        """测试空反馈评论"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "comment": ""
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_very_long_feedback_comment(self, client, test_message, auth_headers):
        """测试超长反馈评论"""
        long_comment = "A" * 10000  # 10000字符
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "negative",
                "comment": long_comment
            },
            headers=auth_headers
        )
        
        # 应该成功或返回长度限制错误
        assert response.status_code in [200, 422]
    
    def test_special_characters_in_comment(self, client, test_message, auth_headers):
        """测试特殊字符"""
        special_chars = "🎉 <script>alert('xss')</script> '\" \n\t \\  中文 😊"
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "comment": special_chars
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # 验证数据未被破坏
        data = response.json()
        assert special_chars in data["comment"]
    
    def test_null_and_undefined_values(self, client, test_message, auth_headers):
        """测试 null 和未定义值"""
        # 只提供必需字段
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] is None
        assert data["comment"] is None
    
    def test_rating_boundary_values(self, client, test_message, auth_headers):
        """测试评分边界值"""
        # 最小值
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "negative", "rating": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 最大值
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive", "rating": 5},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_zero_and_negative_ids(self, client, auth_headers):
        """测试零和负数 ID"""
        # ID = 0
        response = client.get(
            "/api/feedback/messages/0",
            headers=auth_headers
        )
        assert response.status_code in [404, 422]
        
        # ID = -1
        response = client.get(
            "/api/feedback/messages/-1",
            headers=auth_headers
        )
        assert response.status_code in [404, 422]
    
    def test_extremely_large_id(self, client, auth_headers):
        """测试超大 ID"""
        response = client.get(
            "/api/feedback/messages/999999999999",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestConcurrencyEdgeCases:
    """测试并发边缘情况"""
    
    def test_race_condition_feedback_update(
        self,
        client,
        db_session,
        test_message,
        test_org
    ):
        """测试竞态条件：多个用户同时反馈同一消息"""
        from app.models.user import User
        from app.utils.security import hash_password
        
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                email=f"race{i}@test.com",
                username=f"race{i}",
                hashed_password=hash_password("pass"),
                org_id=test_org.id,
                role="member"
            )
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        
        # 所有用户同时对同一消息反馈
        from concurrent.futures import ThreadPoolExecutor
        
        def submit_feedback(user):
            login = client.post(
                "/api/auth/login",
                data={"username": user.email, "password": "pass"}
            )
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            return client.post(
                f"/api/feedback/messages/{test_message.id}",
                json={"feedback_type": "positive"},
                headers=headers
            )
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_feedback, user) for user in users]
            results = [f.result() for f in futures]
        
        # 所有请求都应该成功
        assert all(r.status_code == 200 for r in results)
        
        # 验证数据库中有3条反馈
        from app.models.feedback import MessageFeedback
        count = db_session.query(MessageFeedback).filter(
            MessageFeedback.message_id == test_message.id
        ).count()
        
        assert count == 3
    
    def test_same_user_rapid_updates(self, client, test_message, auth_headers):
        """测试同一用户快速多次更新反馈"""
        # 快速提交5次反馈
        for i in range(5):
            response = client.post(
                f"/api/feedback/messages/{test_message.id}",
                json={
                    "feedback_type": "positive" if i % 2 == 0 else "negative",
                    "rating": i + 1
                },
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # 最终应该只有1条反馈（最后一次的）
        final = client.get(
            f"/api/feedback/messages/{test_message.id}",
            headers=auth_headers
        ).json()
        
        assert final is not None
        assert final["rating"] == 5  # 最后一次的评分


class TestDataIntegrity:
    """测试数据完整性"""
    
    def test_orphaned_feedback_prevention(self, client, db_session, test_message, test_user, auth_headers):
        """测试防止孤立反馈"""
        # 创建反馈
        feedback_response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        assert feedback_response.status_code == 200
        
        # 删除消息
        db_session.delete(test_message)
        db_session.commit()
        
        # 验证反馈也被删除（级联删除）
        from app.models.feedback import MessageFeedback
        orphaned = db_session.query(MessageFeedback).filter(
            MessageFeedback.message_id == test_message.id
        ).first()
        
        assert orphaned is None
    
    def test_feedback_datetime_accuracy(self, client, test_message, auth_headers):
        """测试时间戳准确性"""
        before = datetime.utcnow()
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        
        after = datetime.utcnow()
        
        assert response.status_code == 200
        data = response.json()
        
        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        # 创建时间应该在请求前后之间
        assert before <= created_at <= after + timedelta(seconds=1)
    
    def test_json_field_integrity(self, client, db_session, test_message, test_user, auth_headers):
        """测试 JSON 字段完整性"""
        complex_tags = [
            "tag1", "tag2", "中文标签", "🏷️emoji",
            "very_long_tag_" + "x" * 100
        ]
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "negative",
                "issue_tags": complex_tags
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证所有标签都保存了
        assert len(data["issue_tags"]) == len(complex_tags)
        for tag in complex_tags:
            assert tag in data["issue_tags"]


class TestSecurityEdgeCases:
    """测试安全边缘情况"""
    
    def test_sql_injection_attempt(self, client, auth_headers):
        """测试 SQL 注入防护"""
        malicious_inputs = [
            "'; DROP TABLE message_feedbacks; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users WHERE 1=1; --"
        ]
        
        for malicious in malicious_inputs:
            response = client.post(
                "/api/feedback/messages/1",
                json={
                    "feedback_type": "positive",
                    "comment": malicious
                },
                headers=auth_headers
            )
            
            # 不应该导致数据库错误
            assert response.status_code in [200, 404, 422]
    
    def test_xss_attempt(self, client, test_message, auth_headers):
        """测试 XSS 攻击防护"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            response = client.post(
                f"/api/feedback/messages/{test_message.id}",
                json={
                    "feedback_type": "positive",
                    "comment": payload
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            # 数据应该被原样存储，由前端负责转义
    
    def test_access_other_org_data(self, client, db_session):
        """测试跨组织数据访问防护"""
        from app.models.organization import Organization
        from app.models.user import User
        from app.utils.security import hash_password
        
        # 创建两个组织
        org1 = Organization(name="Org1", slug="org1")
        org2 = Organization(name="Org2", slug="org2")
        db_session.add_all([org1, org2])
        db_session.commit()
        
        # 每个组织一个用户
        user1 = User(
            email="user1@org1.com",
            username="org1user",
            hashed_password=hash_password("pass"),
            org_id=org1.id,
            role="member"
        )
        user2 = User(
            email="user2@org2.com",
            username="org2user",
            hashed_password=hash_password("pass"),
            org_id=org2.id,
            role="member"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # 用户1登录
        login1 = client.post(
            "/api/auth/login",
            data={"username": "user1@org1.com", "password": "pass"}
        )
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # 用户2登录
        login2 = client.post(
            "/api/auth/login",
            data={"username": "user2@org2.com", "password": "pass"}
        )
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # 用户1创建对话
        conv1 = client.post(
            "/api/conversations/",
            json={"title": "Org1对话"},
            headers=headers1
        ).json()
        
        # 用户2不应该能访问用户1的对话
        response = client.get(
            f"/api/conversations/{conv1['id']}",
            headers=headers2
        )
        
        # 应该返回404或403
        assert response.status_code in [403, 404]
    
    def test_token_reuse_after_logout(self, client, test_user):
        """测试登出后 token 复用"""
        # 登录
        login = client.post(
            "/api/auth/login",
            data={"username": test_user.email, "password": "testpass123"}
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 登出
        client.post("/api/auth/logout", headers=headers)
        
        # 尝试使用旧 token
        response = client.get("/api/conversations/", headers=headers)
        
        # 根据实现，可能仍然有效（JWT是无状态的）或返回401
        # 这取决于是否实现了 token 黑名单
        print(f"\n登出后使用旧token: {response.status_code}")


class TestMalformedRequests:
    """测试畸形请求"""
    
    def test_missing_required_fields(self, client, test_message, auth_headers):
        """测试缺少必需字段"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={},  # 缺少 feedback_type
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_invalid_json(self, client, test_message, auth_headers):
        """测试无效的 JSON"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            data="invalid json {{{",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_wrong_content_type(self, client, test_message, auth_headers):
        """测试错误的 Content-Type"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            data="feedback_type=positive",
            headers={**auth_headers, "Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # 可能返回 422 或 415
        assert response.status_code in [415, 422]
    
    def test_extra_fields(self, client, test_message, auth_headers):
        """测试额外的未定义字段"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "rating": 5,
                "extra_field": "should be ignored",
                "another_extra": 123
            },
            headers=auth_headers
        )
        
        # Pydantic 应该忽略额外字段
        assert response.status_code == 200


class TestResourceLimits:
    """测试资源限制"""
    
    def test_max_issue_tags(self, client, test_message, auth_headers):
        """测试最大标签数量"""
        # 尝试添加大量标签
        many_tags = [f"tag{i}" for i in range(100)]
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "negative",
                "issue_tags": many_tags
            },
            headers=auth_headers
        )
        
        # 应该接受或有合理的限制
        assert response.status_code in [200, 422]
    
    def test_stats_with_large_date_range(self, client, auth_headers):
        """测试大日期范围的统计查询"""
        # 请求10年的数据
        response = client.get(
            "/api/feedback/stats/org?days=3650",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # 应该能处理，即使数据为空
    
    def test_pagination_edge_cases(self, client, auth_headers):
        """测试分页边缘情况"""
        # page = 0
        response = client.get(
            "/api/conversations/?page=0&page_size=20",
            headers=auth_headers
        )
        # 可能返回错误或默认为第1页
        assert response.status_code in [200, 422]
        
        # 超大 page_size
        response = client.get(
            "/api/conversations/?page=1&page_size=10000",
            headers=auth_headers
        )
        # 应该有最大限制或返回错误
        assert response.status_code in [200, 422]


class TestErrorRecovery:
    """测试错误恢复"""
    
    def test_partial_failure_handling(self, client, db_session, test_conversation, auth_headers):
        """测试部分失败处理"""
        from app.models.message import Message
        
        # 创建消息
        msg = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Test"
        )
        db_session.add(msg)
        db_session.commit()
        
        # 提交反馈
        response1 = client.post(
            f"/api/feedback/messages/{msg.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # 删除消息（模拟异常情况）
        db_session.delete(msg)
        db_session.commit()
        
        # 尝试再次提交（应该失败）
        response2 = client.post(
            f"/api/feedback/messages/{msg.id}",
            json={"feedback_type": "negative"},
            headers=auth_headers
        )
        assert response2.status_code == 404
    
    def test_database_rollback_on_error(self, client, db_session, test_message, test_user):
        """测试数据库错误时的回滚"""
        from app.models.feedback import MessageFeedback
        
        initial_count = db_session.query(MessageFeedback).count()
        
        # 尝试创建无效的反馈（会触发约束错误）
        try:
            feedback = MessageFeedback(
                message_id=999999,  # 不存在的消息ID
                user_id=test_user.id,
                feedback_type="positive"
            )
            db_session.add(feedback)
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # 验证没有脏数据
        final_count = db_session.query(MessageFeedback).count()
        assert final_count == initial_count


class TestUnicodecodeAndLocalization:
    """测试 Unicode 和本地化"""
    
    def test_chinese_characters(self, client, test_message, auth_headers):
        """测试中文字符"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "comment": "这个回答非常好！👍 很有帮助。"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "这个回答非常好" in data["comment"]
    
    def test_mixed_languages(self, client, test_message, auth_headers):
        """测试混合语言"""
        mixed = "English 中文 日本語 한국어 العربية"
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "comment": mixed
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_emoji_handling(self, client, test_message, auth_headers):
        """测试 Emoji 处理"""
        emojis = "😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘"
        
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "comment": emojis
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert emojis in response.json()["comment"]


class TestTimeZoneHandling:
    """测试时区处理"""
    
    def test_utc_timestamps(self, client, test_message, auth_headers):
        """测试 UTC 时间戳"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        created_at = response.json()["created_at"]
        
        # 应该是 ISO 8601 格式
        assert "T" in created_at
        # 验证可以解析
        datetime.fromisoformat(created_at.replace("Z", "+00:00"))

