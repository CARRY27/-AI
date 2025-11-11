"""
Pytest 配置文件
提供测试fixture和通用配置
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.file import File
from app.models.feedback import MessageFeedback
from app.utils.security import hash_password


# 测试数据库（使用内存数据库）
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_org(db_session):
    """创建测试组织"""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        settings={}
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_user(db_session, test_org):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        org_id=test_org.id,
        role="member",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, test_org):
    """创建管理员用户"""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        org_id=test_org.id,
        role="admin",
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(client, test_user):
    """获取认证token"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    """获取管理员token"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": admin_user.email,
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """管理员请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_conversation(db_session, test_user, test_org):
    """创建测试对话"""
    conversation = Conversation(
        user_id=test_user.id,
        org_id=test_org.id,
        title="Test Conversation"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def test_message(db_session, test_conversation):
    """创建测试消息"""
    message = Message(
        conversation_id=test_conversation.id,
        role="assistant",
        content="This is a test answer",
        source_refs=[],
        meta_data={}
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 测试数据
@pytest.fixture
def sample_queries():
    """示例查询"""
    return [
        "DocAgent 是什么？",
        "如何上传文档？",
        "支持哪些文件格式？",
        "如何提高回答准确度？",
        "系统有哪些限制？"
    ]


@pytest.fixture
def sample_feedbacks():
    """示例反馈"""
    return [
        {"feedback_type": "positive", "rating": 5},
        {"feedback_type": "positive", "rating": 4},
        {"feedback_type": "negative", "rating": 2, "comment": "不够准确"},
        {"feedback_type": "positive", "rating": 5},
        {"feedback_type": "negative", "rating": 1, "comment": "答非所问"}
    ]

