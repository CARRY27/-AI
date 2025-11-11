-- 初始化数据脚本
-- 创建默认组织、用户、角色等

-- ========== 创建默认组织 ==========

INSERT INTO organizations (name, domain, max_users, max_storage, is_active) VALUES
('默认组织', 'example.com', 1000, 107374182400, true)  -- 100GB
ON CONFLICT DO NOTHING;

-- ========== 创建系统管理员 ==========

-- 密码: admin123 (已使用bcrypt哈希)
INSERT INTO users (username, email, password_hash, org_id, role, is_active, is_verified) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5Zv.QOkZc7qKm', 
 (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1), 
 'superuser', true, true)
ON CONFLICT (email) DO NOTHING;

-- 为管理员分配角色
INSERT INTO user_roles (user_id, role_id)
SELECT 
    (SELECT id FROM users WHERE email = 'admin@example.com' LIMIT 1),
    (SELECT id FROM roles WHERE name = 'superuser' LIMIT 1)
ON CONFLICT DO NOTHING;

-- ========== 创建示例标签 ==========

INSERT INTO tags (name, category, color, org_id) VALUES
-- 部门标签
('人力资源部', 'department', '#409EFF', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('技术部', 'department', '#67C23A', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('市场部', 'department', '#E6A23C', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('财务部', 'department', '#F56C6C', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),

-- 项目标签
('产品文档', 'project', '#909399', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('内部规章', 'project', '#303133', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('培训资料', 'project', '#606266', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),

-- 时间标签
('2024', 'time', '#409EFF', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1)),
('2025', 'time', '#67C23A', (SELECT id FROM organizations WHERE name = '默认组织' LIMIT 1))
ON CONFLICT DO NOTHING;

-- ========== 查询验证 ==========

-- 显示创建的组织
SELECT id, name, domain FROM organizations;

-- 显示创建的用户
SELECT id, username, email, role FROM users;

-- 显示创建的角色
SELECT id, name, display_name FROM roles;

-- 显示创建的标签
SELECT id, name, category, color FROM tags;

