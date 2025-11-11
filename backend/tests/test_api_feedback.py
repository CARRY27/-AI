"""
反馈 API - 黑盒测试
测试 API 端点的功能和响应
"""

import pytest
from fastapi.testclient import TestClient


class TestFeedbackAPI:
    """测试反馈 API 端点"""
    
    def test_create_positive_feedback(self, client, test_message, auth_headers):
        """测试创建正面反馈"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "positive",
                "rating": 5,
                "comment": "非常有帮助！"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] == "positive"
        assert data["rating"] == 5
        assert data["comment"] == "非常有帮助！"
    
    def test_create_negative_feedback(self, client, test_message, auth_headers):
        """测试创建负面反馈"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "negative",
                "rating": 2,
                "comment": "回答不准确",
                "issue_tags": ["inaccurate", "incomplete"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] == "negative"
        assert data["rating"] == 2
        assert "inaccurate" in data["issue_tags"]
    
    def test_update_existing_feedback(self, client, test_message, auth_headers):
        """测试更新已有反馈"""
        # 首先创建反馈
        client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive", "rating": 4},
            headers=auth_headers
        )
        
        # 更新为负面反馈
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "negative", "rating": 2},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] == "negative"
        assert data["rating"] == 2
    
    def test_get_feedback(self, client, test_message, auth_headers):
        """测试获取反馈"""
        # 创建反馈
        client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive", "rating": 5},
            headers=auth_headers
        )
        
        # 获取反馈
        response = client.get(
            f"/api/feedback/messages/{test_message.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] == "positive"
    
    def test_delete_feedback(self, client, test_message, auth_headers):
        """测试删除反馈"""
        # 创建反馈
        client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        
        # 删除反馈
        response = client.delete(
            f"/api/feedback/messages/{test_message.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # 验证已删除
        get_response = client.get(
            f"/api/feedback/messages/{test_message.id}",
            headers=auth_headers
        )
        assert get_response.json() is None
    
    def test_feedback_without_auth(self, client, test_message):
        """测试未认证访问"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive"}
        )
        
        assert response.status_code == 401
    
    def test_feedback_nonexistent_message(self, client, auth_headers):
        """测试对不存在的消息创建反馈"""
        response = client.post(
            "/api/feedback/messages/99999",
            json={"feedback_type": "positive"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]


class TestFeedbackStatsAPI:
    """测试反馈统计 API"""
    
    def test_get_org_stats(self, client, test_message, auth_headers, sample_feedbacks):
        """测试获取组织统计"""
        # 创建多个反馈
        for fb_data in sample_feedbacks:
            client.post(
                f"/api/feedback/messages/{test_message.id}",
                json=fb_data,
                headers=auth_headers
            )
            # 删除之前的，模拟不同消息
            client.delete(
                f"/api/feedback/messages/{test_message.id}",
                headers=auth_headers
            )
        
        # 获取统计
        response = client.get(
            "/api/feedback/stats/org?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_feedbacks" in data
        assert "positive_count" in data
        assert "negative_count" in data
        assert "satisfaction_rate" in data
        assert data["satisfaction_rate"] >= 0.0
        assert data["satisfaction_rate"] <= 1.0
    
    def test_get_daily_stats(self, client, admin_headers):
        """测试获取每日统计"""
        response = client.get(
            "/api/feedback/stats/daily?days=7",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_daily_stats_requires_admin(self, client, auth_headers):
        """测试每日统计需要管理员权限"""
        response = client.get(
            "/api/feedback/stats/daily",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_get_recent_negative(self, client, admin_headers):
        """测试获取最近负面反馈"""
        response = client.get(
            "/api/feedback/negative/recent?limit=20",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_resolve_negative_feedback(self, client, db_session, test_message, test_user, admin_headers):
        """测试处理负面反馈"""
        # 创建负面反馈
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="negative",
            comment="回答错误"
        )
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        # 标记为已处理
        response = client.patch(
            f"/api/feedback/negative/{feedback.id}/resolve",
            json={"resolution_note": "已优化模型"},
            headers=admin_headers
        )
        
        assert response.status_code == 200


class TestFeedbackValidation:
    """测试反馈数据验证"""
    
    def test_invalid_feedback_type(self, client, test_message, auth_headers):
        """测试无效的反馈类型"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "invalid_type"},
            headers=auth_headers
        )
        
        # 应该返回验证错误
        assert response.status_code in [422, 400]
    
    def test_invalid_rating_range(self, client, test_message, auth_headers):
        """测试无效的评分范围"""
        # 评分 < 1
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive", "rating": 0},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # 评分 > 5
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={"feedback_type": "positive", "rating": 6},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_empty_issue_tags(self, client, test_message, auth_headers):
        """测试空的问题标签"""
        response = client.post(
            f"/api/feedback/messages/{test_message.id}",
            json={
                "feedback_type": "negative",
                "issue_tags": []
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestFeedbackPerformance:
    """测试反馈性能"""
    
    def test_batch_feedback_creation(self, client, db_session, test_conversation, test_user, auth_headers):
        """测试批量创建反馈的性能"""
        import time
        
        # 创建多条消息
        messages = []
        for i in range(10):
            msg = Message(
                conversation_id=test_conversation.id,
                role="assistant",
                content=f"Test answer {i}"
            )
            db_session.add(msg)
            messages.append(msg)
        
        db_session.commit()
        
        # 批量创建反馈并计时
        start_time = time.time()
        
        for msg in messages:
            response = client.post(
                f"/api/feedback/messages/{msg.id}",
                json={"feedback_type": "positive", "rating": 5},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        
        # 10个反馈应该在2秒内完成
        assert elapsed < 2.0
        print(f"\n批量创建10个反馈耗时: {elapsed:.3f}秒")

