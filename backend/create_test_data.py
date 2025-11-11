"""
创建测试数据
用于测试反馈功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.conversation import Conversation
from app.models.message import Message
from datetime import datetime


def create_test_data():
    """创建测试数据"""
    db = SessionLocal()
    
    try:
        print("开始创建测试数据...")
        
        # 查找admin用户
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        
        if not admin:
            print("❌ 未找到admin用户")
            return
        
        print(f"✅ 找到用户: {admin.username}")
        
        # 查找或创建测试对话
        test_conv = db.query(Conversation).filter(
            Conversation.user_id == admin.id,
            Conversation.title == "测试对话-反馈功能"
        ).first()
        
        if not test_conv:
            test_conv = Conversation(
                user_id=admin.id,
                org_id=admin.org_id,
                title="测试对话-反馈功能",
                message_count=0
            )
            db.add(test_conv)
            db.commit()
            db.refresh(test_conv)
            print(f"✅ 创建测试对话: ID={test_conv.id}")
        else:
            print(f"✅ 使用现有对话: ID={test_conv.id}")
        
        # 创建一些测试消息
        test_questions = [
            "DocAgent 是什么？",
            "如何上传文档？",
            "支持哪些文件格式？"
        ]
        
        test_answers = [
            "DocAgent 是一个企业级智能文档问答系统，基于RAG技术。",
            "点击文件管理页面的上传按钮，选择文件即可上传。",
            "支持 PDF、DOCX、TXT、HTML、XLSX、PPTX、Markdown 等格式。"
        ]
        
        created_messages = []
        
        for i, (question, answer) in enumerate(zip(test_questions, test_answers)):
            # 用户消息
            user_msg = Message(
                conversation_id=test_conv.id,
                role="user",
                content=question
            )
            db.add(user_msg)
            
            # AI消息
            ai_msg = Message(
                conversation_id=test_conv.id,
                role="assistant",
                content=answer,
                source_refs=[],
                meta_data={"confidence": 0.85}
            )
            db.add(ai_msg)
            created_messages.append(ai_msg)
        
        db.commit()
        
        print(f"✅ 创建了 {len(created_messages)} 组测试消息")
        
        # 显示消息ID
        for msg in created_messages:
            db.refresh(msg)
            print(f"   消息 ID: {msg.id} - {msg.content[:30]}...")
        
        print("\n" + "="*60)
        print("测试数据创建完成！")
        print("="*60)
        print(f"\n可以使用消息ID进行反馈测试:")
        print(f"例如: POST /api/feedback/messages/{created_messages[0].id}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()

