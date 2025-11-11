-- 添加用户反馈系统
-- 创建时间: 2025-11-07

-- 反馈表
CREATE TABLE IF NOT EXISTS message_feedbacks (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 反馈类型：positive(点赞) / negative(点踩)
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('positive', 'negative')),
    
    -- 评分（1-5星）可选
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    -- 文字反馈
    comment TEXT,
    
    -- 问题标签：inaccurate(不准确), incomplete(不完整), irrelevant(不相关), other(其他)
    issue_tags JSONB DEFAULT '[]'::jsonb,
    
    -- 是否已处理
    is_resolved BOOLEAN DEFAULT FALSE,
    
    -- 处理说明
    resolution_note TEXT,
    
    -- 元数据
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保每个用户对每条消息只能有一个反馈
    UNIQUE(message_id, user_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_feedbacks_message ON message_feedbacks(message_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user ON message_feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_type ON message_feedbacks(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created ON message_feedbacks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedbacks_unresolved ON message_feedbacks(is_resolved) WHERE is_resolved = FALSE;

-- 反馈统计表
CREATE TABLE IF NOT EXISTS feedback_stats (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- 日期
    date DATE NOT NULL,
    
    -- 统计指标
    total_feedbacks INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    
    -- 满意度（0-1）
    satisfaction_rate FLOAT DEFAULT 0.0,
    
    -- 平均评分
    average_rating FLOAT DEFAULT 0.0,
    
    -- 常见问题标签统计
    issue_tag_counts JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保每个组织每天只有一条统计记录
    UNIQUE(org_id, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_feedback_stats_org ON feedback_stats(org_id);
CREATE INDEX IF NOT EXISTS idx_feedback_stats_date ON feedback_stats(date DESC);

-- 添加注释
COMMENT ON TABLE message_feedbacks IS '用户对AI回答的反馈（点赞/点踩）';
COMMENT ON TABLE feedback_stats IS '反馈统计数据（按天汇总）';

COMMENT ON COLUMN message_feedbacks.feedback_type IS '反馈类型：positive或negative';
COMMENT ON COLUMN message_feedbacks.issue_tags IS '问题标签数组，用于分类负面反馈';
COMMENT ON COLUMN message_feedbacks.is_resolved IS '负面反馈是否已被处理';

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_message_feedbacks_updated_at 
    BEFORE UPDATE ON message_feedbacks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_stats_updated_at 
    BEFORE UPDATE ON feedback_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入一些示例数据（可选）
-- INSERT INTO message_feedbacks (message_id, user_id, feedback_type, rating) 
-- VALUES (1, 1, 'positive', 5);

