-- 高级功能数据库迁移脚本
-- 添加角色权限、标签、审核等功能

-- ========== 角色权限系统 ==========

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);


-- ========== 文档标签系统 ==========

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- department, project, time, custom
    color VARCHAR(20),
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_org_id ON tags(org_id);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);

-- 文档-标签关联表
CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON document_tags(tag_id);


-- ========== 审核系统 ==========

-- 消息审核表
CREATE TABLE IF NOT EXISTS message_reviews (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL,  -- pending, approved, rejected, flagged
    review_type VARCHAR(30),  -- accuracy, inappropriate, vague, hallucination, sensitive
    comment TEXT,
    suggestion TEXT,
    requires_human_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_message_reviews_message_id ON message_reviews(message_id);
CREATE INDEX IF NOT EXISTS idx_message_reviews_reviewer_id ON message_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_message_reviews_status ON message_reviews(status);


-- 敏感词检测日志表
CREATE TABLE IF NOT EXISTS sensitive_word_logs (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    file_id INTEGER REFERENCES files(id) ON DELETE SET NULL,
    content_type VARCHAR(50),  -- question, answer, document
    detected_words TEXT,  -- JSON array
    risk_level VARCHAR(20),  -- low, medium, high, critical
    original_text TEXT,
    context TEXT,
    is_blocked BOOLEAN DEFAULT FALSE,
    handled BOOLEAN DEFAULT FALSE,
    handler_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    handled_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_sensitive_logs_message_id ON sensitive_word_logs(message_id);
CREATE INDEX IF NOT EXISTS idx_sensitive_logs_file_id ON sensitive_word_logs(file_id);
CREATE INDEX IF NOT EXISTS idx_sensitive_logs_risk_level ON sensitive_word_logs(risk_level);
CREATE INDEX IF NOT EXISTS idx_sensitive_logs_handled ON sensitive_word_logs(handled);


-- ========== 消息表增强 ==========

-- 为消息表添加新字段（如果不存在）
ALTER TABLE messages ADD COLUMN IF NOT EXISTS rating INTEGER;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS feedback TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS confidence FLOAT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';


-- ========== 用户表增强 ==========

-- 为用户表添加角色字段（兼容旧系统）
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);


-- ========== 插入初始角色数据 ==========

INSERT INTO roles (name, display_name, description, permissions, is_system) VALUES
('superuser', '超级管理员', '拥有系统所有权限', 
'{
  "document": {"read": true, "write": true, "delete": true, "manage": true},
  "conversation": {"read": true, "write": true, "delete": true, "export": true},
  "user": {"read": true, "write": true, "delete": true, "manage": true},
  "admin": {"manage_users": true, "manage_roles": true, "view_audit": true, "manage_config": true},
  "review": {"review_messages": true, "handle_sensitive": true, "view_reports": true}
}'::jsonb, true),

('admin', '管理员', '管理知识库与权限', 
'{
  "document": {"read": true, "write": true, "delete": true, "manage": true},
  "conversation": {"read": true, "write": true, "delete": true, "export": true},
  "user": {"read": true, "write": true, "manage": true},
  "admin": {"manage_users": true, "view_audit": true},
  "review": {"review_messages": true, "view_reports": true}
}'::jsonb, true),

('auditor', '审核员', '审核AI输出的合规性', 
'{
  "document": {"read": true},
  "conversation": {"read": true},
  "review": {"review_messages": true, "handle_sensitive": true, "view_reports": true}
}'::jsonb, true),

('user', '普通用户', '企业内部普通使用者', 
'{
  "document": {"read": true, "write": false},
  "conversation": {"read": true, "write": true, "export": true}
}'::jsonb, true)
ON CONFLICT (name) DO NOTHING;


-- ========== 创建视图 ==========

-- 消息审核统计视图
CREATE OR REPLACE VIEW message_review_stats AS
SELECT 
    mr.status,
    COUNT(*) as count,
    COUNT(DISTINCT mr.message_id) as unique_messages,
    COUNT(DISTINCT mr.reviewer_id) as unique_reviewers,
    DATE(mr.created_at) as review_date
FROM message_reviews mr
GROUP BY mr.status, DATE(mr.created_at);

-- 敏感内容检测统计视图
CREATE OR REPLACE VIEW sensitive_detection_stats AS
SELECT 
    swl.risk_level,
    swl.content_type,
    COUNT(*) as count,
    SUM(CASE WHEN swl.is_blocked THEN 1 ELSE 0 END) as blocked_count,
    SUM(CASE WHEN swl.handled THEN 1 ELSE 0 END) as handled_count,
    DATE(swl.created_at) as detection_date
FROM sensitive_word_logs swl
GROUP BY swl.risk_level, swl.content_type, DATE(swl.created_at);


-- ========== 完成标记 ==========

COMMENT ON TABLE roles IS '角色表 - 定义系统角色和权限';
COMMENT ON TABLE user_roles IS '用户角色关联表 - 支持用户多角色';
COMMENT ON TABLE tags IS '标签表 - 文档分类标签';
COMMENT ON TABLE document_tags IS '文档标签关联表';
COMMENT ON TABLE message_reviews IS '消息审核表 - 审核员审核AI回答';
COMMENT ON TABLE sensitive_word_logs IS '敏感词检测日志表 - 内容安全监控';

