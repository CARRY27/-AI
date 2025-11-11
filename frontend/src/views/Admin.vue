<template>
  <div class="admin-container">
    <div class="page-header">
      <h2>⚙️ 系统管理</h2>
    </div>
    
    <el-row :gutter="24" style="margin-bottom: 24px">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总用户数" :value="stats.total_users">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总文件数" :value="stats.total_files">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总对话数" :value="stats.total_conversations">
            <template #prefix>
              <el-icon><ChatDotRound /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="存储空间" :value="formatStorage(stats.total_storage_bytes)">
            <template #prefix>
              <el-icon><FolderOpened /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="admin-actions">
      <template #header>
        <span>管理操作</span>
      </template>
      
      <el-space direction="vertical" :size="16" style="width: 100%">
        <div>
          <h4>系统维护</h4>
          <el-button type="warning" @click="handleReindexAll">
            重建所有索引
          </el-button>
          <el-button type="info" @click="handleClearCache">
            清理缓存
          </el-button>
        </div>
        
        <el-divider />
        
        <div>
          <h4>数据统计</h4>
          <p>总消息数: {{ stats.total_messages }}</p>
          <p>存储使用: {{ formatStorage(stats.total_storage_bytes) }} / 100 GB</p>
        </div>
      </el-space>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/services/api'
import { ElMessage } from 'element-plus'
import { User, Document, ChatDotRound, FolderOpened } from '@element-plus/icons-vue'

const stats = ref({
  total_users: 0,
  total_files: 0,
  total_conversations: 0,
  total_messages: 0,
  total_storage_bytes: 0
})

const loadStats = async () => {
  try {
    const response = await adminApi.getStats()
    stats.value = response
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleReindexAll = () => {
  ElMessage.info('重建索引功能开发中')
}

const handleClearCache = () => {
  ElMessage.info('清理缓存功能开发中')
}

const formatStorage = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.admin-container {
  padding: 32px;
  background: #f8f9fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 28px;
}

.page-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.stat-card {
  text-align: center;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stat-card :deep(.el-statistic__head) {
  font-size: 13px;
  font-weight: 600;
  color: #6e6e73;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-card :deep(.el-statistic__content) {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
}

.stat-card :deep(.el-icon) {
  font-size: 24px;
  color: #667eea;
  margin-right: 8px;
}

.admin-actions {
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.admin-actions :deep(.el-card__header) {
  background: #f8f9fa;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  font-weight: 600;
  font-size: 16px;
  color: #1a1a1a;
}

.admin-actions h4 {
  margin: 0 0 16px 0;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
}

.admin-actions p {
  margin: 10px 0;
  color: #6e6e73;
  font-size: 14px;
  font-weight: 500;
}

.admin-actions :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.2s;
}

.admin-actions :deep(.el-button:hover) {
  transform: translateY(-1px);
}

.admin-actions :deep(.el-button--warning) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.25);
}

.admin-actions :deep(.el-button--warning:hover) {
  box-shadow: 0 6px 16px rgba(245, 87, 108, 0.35);
}

.admin-actions :deep(.el-button--info) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.25);
}

.admin-actions :deep(.el-button--info:hover) {
  box-shadow: 0 6px 16px rgba(79, 172, 254, 0.35);
}
</style>

