-- 003_add_knowledge_update_features.sql
-- 添加知识更新机制相关字段

-- 1. 为files表添加版本控制字段
ALTER TABLE files 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL,
ADD COLUMN IF NOT EXISTS previous_version_id INTEGER REFERENCES files(id),
ADD COLUMN IF NOT EXISTS is_latest_version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMP WITH TIME ZONE;

-- 2. 为messages表添加latency_ms字段（如果不存在）
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS latency_ms INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- 3. 创建文件版本历史索引
CREATE INDEX IF NOT EXISTS idx_files_version ON files(version);
CREATE INDEX IF NOT EXISTS idx_files_latest_version ON files(is_latest_version) WHERE is_latest_version = 1;
CREATE INDEX IF NOT EXISTS idx_files_refresh ON files(last_refreshed_at);

-- 4. 为提示词模板使用日志表添加字段（如果表不存在则创建）
CREATE TABLE IF NOT EXISTS prompt_template_usage_logs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES prompt_templates(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    message_id INTEGER REFERENCES messages(id),
    
    -- 使用信息
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    
    -- 结果
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- 评价
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 创建相关索引
CREATE INDEX IF NOT EXISTS idx_prompt_usage_template ON prompt_template_usage_logs(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_user ON prompt_template_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_created ON prompt_template_usage_logs(created_at);

-- 6. 为messages表添加token统计字段（如果不存在）
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0;

-- 7. 添加索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user_org ON conversations(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON message_feedbacks(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- 8. 为审计日志添加用户关联索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);

COMMENT ON COLUMN files.version IS '文档版本号';
COMMENT ON COLUMN files.previous_version_id IS '上一版本文件ID';
COMMENT ON COLUMN files.is_latest_version IS '是否为最新版本';
COMMENT ON COLUMN files.last_refreshed_at IS '最后刷新时间';

