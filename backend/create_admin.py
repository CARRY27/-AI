"""
创建管理员用户脚本
"""
import asyncio
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash


async def create_admin():
    """创建管理员用户"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在
        result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ 管理员用户已存在，更新密码...")
            existing_user.hashed_password = get_password_hash("admin123")
            await db.commit()
            print("✅ 密码已更新！")
        else:
            print("创建新的管理员用户...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                org_id=1,
                role="admin",
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            await db.commit()
            print("✅ 管理员用户创建成功！")
        
        # 验证
        result = await db.execute(
            select(User).where(User.email == "admin@example.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"\n用户信息:")
            print(f"  ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  邮箱: {user.email}")
            print(f"  角色: {user.role}")
            print(f"  密码哈希: {user.hashed_password[:30]}...")


if __name__ == "__main__":
    asyncio.run(create_admin())

