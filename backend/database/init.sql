-- DocAgent 数据库初始化脚本
-- 此文件在 PostgreSQL 容器首次启动时自动执行

-- 创建扩展（如需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 注意：实际的表结构由 SQLAlchemy 自动创建
-- 这里只做一些初始化配置

-- 创建索引（可选，提升性能）
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_files_org_id ON files(org_id);
-- CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id);
-- CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
-- CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- 设置时区
SET timezone = 'UTC';

-- 完成
SELECT 'Database initialization completed' as status;

