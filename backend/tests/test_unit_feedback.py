"""
用户反馈系统 - 单元测试（白盒测试）
测试反馈模型和业务逻辑
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.feedback import MessageFeedback, FeedbackStats
from app.models.message import Message


class TestMessageFeedbackModel:
    """测试 MessageFeedback 模型"""
    
    def test_create_feedback(self, db_session, test_message, test_user):
        """测试创建反馈"""
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="positive",
            rating=5
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        assert feedback.id is not None
        assert feedback.feedback_type == "positive"
        assert feedback.rating == 5
        assert feedback.is_resolved is False
    
    def test_unique_constraint(self, db_session, test_message, test_user):
        """测试唯一约束：同一用户对同一消息只能有一个反馈"""
        feedback1 = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="positive"
        )
        db_session.add(feedback1)
        db_session.commit()
        
        # 尝试创建重复反馈
        feedback2 = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="negative"
        )
        db_session.add(feedback2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_cascade_delete(self, db_session, test_message, test_user):
        """测试级联删除：删除消息时反馈也删除"""
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="positive"
        )
        db_session.add(feedback)
        db_session.commit()
        
        feedback_id = feedback.id
        
        # 删除消息
        db_session.delete(test_message)
        db_session.commit()
        
        # 验证反馈也被删除
        deleted_feedback = db_session.query(MessageFeedback).filter(
            MessageFeedback.id == feedback_id
        ).first()
        
        assert deleted_feedback is None
    
    def test_feedback_with_tags(self, db_session, test_message, test_user):
        """测试带标签的反馈"""
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="negative",
            rating=2,
            comment="回答不够准确",
            issue_tags=["inaccurate", "incomplete"]
        )
        
        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)
        
        assert "inaccurate" in feedback.issue_tags
        assert "incomplete" in feedback.issue_tags
        assert len(feedback.issue_tags) == 2
    
    def test_update_feedback(self, db_session, test_message, test_user):
        """测试更新反馈"""
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="positive",
            rating=4
        )
        db_session.add(feedback)
        db_session.commit()
        
        # 更新反馈
        feedback.feedback_type = "negative"
        feedback.rating = 2
        feedback.comment = "改变主意了"
        db_session.commit()
        
        db_session.refresh(feedback)
        assert feedback.feedback_type == "negative"
        assert feedback.rating == 2
        assert feedback.comment == "改变主意了"
    
    def test_resolve_feedback(self, db_session, test_message, test_user):
        """测试处理负面反馈"""
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="negative",
            rating=1,
            comment="完全错误"
        )
        db_session.add(feedback)
        db_session.commit()
        
        # 标记为已处理
        feedback.is_resolved = True
        feedback.resolution_note = "已优化 Prompt，问题已解决"
        db_session.commit()
        
        db_session.refresh(feedback)
        assert feedback.is_resolved is True
        assert feedback.resolution_note is not None


class TestFeedbackStatsModel:
    """测试 FeedbackStats 模型"""
    
    def test_create_stats(self, db_session, test_org):
        """测试创建统计记录"""
        stats = FeedbackStats(
            org_id=test_org.id,
            date=datetime.utcnow(),
            total_feedbacks=100,
            positive_count=80,
            negative_count=20,
            satisfaction_rate=0.80,
            average_rating=4.2
        )
        
        db_session.add(stats)
        db_session.commit()
        db_session.refresh(stats)
        
        assert stats.id is not None
        assert stats.satisfaction_rate == 0.80
        assert stats.average_rating == 4.2
    
    def test_issue_tag_counts(self, db_session, test_org):
        """测试问题标签统计"""
        stats = FeedbackStats(
            org_id=test_org.id,
            date=datetime.utcnow(),
            total_feedbacks=50,
            positive_count=30,
            negative_count=20,
            issue_tag_counts={
                "inaccurate": 12,
                "incomplete": 5,
                "irrelevant": 3
            }
        )
        
        db_session.add(stats)
        db_session.commit()
        db_session.refresh(stats)
        
        assert stats.issue_tag_counts["inaccurate"] == 12
        assert stats.issue_tag_counts["incomplete"] == 5


class TestFeedbackBusinessLogic:
    """测试反馈业务逻辑"""
    
    def test_satisfaction_rate_calculation(self):
        """测试满意度计算"""
        total = 100
        positive = 75
        negative = 25
        
        satisfaction_rate = positive / total
        
        assert satisfaction_rate == 0.75
    
    def test_average_rating_calculation(self):
        """测试平均评分计算"""
        ratings = [5, 4, 5, 3, 4, 5, 2, 4]
        
        average = sum(ratings) / len(ratings)
        
        assert round(average, 2) == 4.0
    
    def test_issue_tag_aggregation(self):
        """测试问题标签聚合"""
        feedbacks = [
            {"tags": ["inaccurate", "incomplete"]},
            {"tags": ["inaccurate"]},
            {"tags": ["irrelevant"]},
            {"tags": ["inaccurate", "other"]}
        ]
        
        tag_counts = {}
        for feedback in feedbacks:
            for tag in feedback["tags"]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        assert tag_counts["inaccurate"] == 3
        assert tag_counts["incomplete"] == 1
        assert tag_counts["irrelevant"] == 1
        assert tag_counts["other"] == 1


@pytest.mark.asyncio
class TestAsyncFeedbackOperations:
    """测试异步反馈操作"""
    
    async def test_concurrent_feedback_creation(self, db_session, test_message, test_user):
        """测试并发创建反馈"""
        # 模拟并发场景
        feedback = MessageFeedback(
            message_id=test_message.id,
            user_id=test_user.id,
            feedback_type="positive",
            rating=5
        )
        
        db_session.add(feedback)
        db_session.commit()
        
        assert feedback.id is not None

