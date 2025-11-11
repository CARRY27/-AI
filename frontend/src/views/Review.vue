<template>
  <div class="review-container">
    <h1 class="title">消息审核</h1>
    
    <el-tabs v-model="activeTab">
      <!-- 待审核 -->
      <el-tab-pane label="待审核" name="pending">
        <el-table :data="pendingMessages" v-loading="loading">
          <el-table-column prop="message_id" label="ID" width="80" />
          <el-table-column prop="content" label="消息内容" min-width="300">
            <template #default="{ row }">
              <div class="message-content">{{ row.content }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column label="操作" width="280">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="reviewMessage(row, 'approved')">
                通过
              </el-button>
              <el-button type="warning" size="small" @click="reviewMessage(row, 'flagged')">
                标记
              </el-button>
              <el-button type="danger" size="small" @click="reviewMessage(row, 'rejected')">
                拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadPendingMessages"
        />
      </el-tab-pane>
      
      <!-- 敏感内容 -->
      <el-tab-pane label="敏感内容" name="sensitive">
        <el-table :data="sensitiveLogs" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="content_type" label="类型" width="100" />
          <el-table-column prop="detected_words" label="检测到的敏感词" min-width="200" />
          <el-table-column prop="risk_level" label="风险等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getRiskLevelType(row.risk_level)">
                {{ row.risk_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_blocked" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_blocked ? 'danger' : 'info'">
                {{ row.is_blocked ? '已屏蔽' : '已记录' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="handleSensitiveLog(row)"
                :disabled="row.handled"
              >
                {{ row.handled ? '已处理' : '标记处理' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 质量报告 -->
      <el-tab-pane label="质量报告" name="report">
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-card>
              <template #header>
                <span>总消息数</span>
              </template>
              <div class="stat-value">{{ report.total_messages }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <template #header>
                <span>已审核</span>
              </template>
              <div class="stat-value">{{ report.reviewed_messages }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <template #header>
                <span>通过率</span>
              </template>
              <div class="stat-value">
                {{ ((report.approved_count / report.reviewed_messages) * 100).toFixed(1) }}%
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <template #header>
                <span>敏感检测</span>
              </template>
              <div class="stat-value">{{ report.sensitive_detections }}</div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-card class="chart-card">
          <template #header>
            <span>审核状态分布</span>
          </template>
          <div class="pie-chart">
            <el-descriptions :column="2">
              <el-descriptions-item label="通过">{{ report.approved_count }}</el-descriptions-item>
              <el-descriptions-item label="拒绝">{{ report.rejected_count }}</el-descriptions-item>
              <el-descriptions-item label="标记">{{ report.flagged_count }}</el-descriptions-item>
              <el-descriptions-item label="平均置信度">
                {{ (report.avg_confidence * 100).toFixed(1) }}%
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 审核对话框 -->
    <el-dialog v-model="reviewDialogVisible" title="审核消息" width="600px">
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="审核状态">
          <el-radio-group v-model="reviewForm.status">
            <el-radio label="approved">通过</el-radio>
            <el-radio label="flagged">标记</el-radio>
            <el-radio label="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="问题类型">
          <el-select v-model="reviewForm.review_type" placeholder="请选择">
            <el-option label="准确性问题" value="accuracy" />
            <el-option label="不当内容" value="inappropriate" />
            <el-option label="模糊不清" value="vague" />
            <el-option label="虚构内容" value="hallucination" />
            <el-option label="敏感内容" value="sensitive" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核意见">
          <el-input 
            v-model="reviewForm.comment" 
            type="textarea" 
            :rows="4"
            placeholder="请输入审核意见..."
          />
        </el-form-item>
        <el-form-item label="改进建议">
          <el-input 
            v-model="reviewForm.suggestion" 
            type="textarea" 
            :rows="3"
            placeholder="请输入改进建议..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const activeTab = ref('pending')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const pendingMessages = ref([])
const sensitiveLogs = ref([])
const report = ref({
  total_messages: 0,
  reviewed_messages: 0,
  approved_count: 0,
  rejected_count: 0,
  flagged_count: 0,
  avg_confidence: 0,
  sensitive_detections: 0
})

const reviewDialogVisible = ref(false)
const reviewForm = ref({
  message_id: null,
  status: 'approved',
  review_type: '',
  comment: '',
  suggestion: ''
})

// 加载待审核消息
const loadPendingMessages = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/review/pending', {
      params: { page: currentPage.value, page_size: pageSize.value }
    })
    pendingMessages.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 加载敏感词日志
const loadSensitiveLogs = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/review/sensitive-logs', {
      params: { page: 1, page_size: 50, unhandled_only: false }
    })
    sensitiveLogs.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 加载质量报告
const loadQualityReport = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/review/quality-report')
    report.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 审核消息
const reviewMessage = (row, status) => {
  reviewForm.value = {
    message_id: row.message_id,
    status: status,
    review_type: '',
    comment: '',
    suggestion: ''
  }
  reviewDialogVisible.value = true
}

// 提交审核
const submitReview = async () => {
  try {
    await api.post('/review/messages', reviewForm.value)
    ElMessage.success('审核已提交')
    reviewDialogVisible.value = false
    loadPendingMessages()
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

// 处理敏感日志
const handleSensitiveLog = async (row) => {
  try {
    await api.post(`/review/sensitive-logs/${row.id}/handle`)
    ElMessage.success('已标记为已处理')
    loadSensitiveLogs()
  } catch (error) {
    ElMessage.error('处理失败')
  }
}

// 获取风险等级类型
const getRiskLevelType = (level) => {
  const map = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return map[level] || 'info'
}

onMounted(() => {
  loadPendingMessages()
  loadQualityReport()
})
</script>

<style scoped>
.review-container {
  padding: 20px;
}

.title {
  font-size: 24px;
  margin-bottom: 20px;
}

.message-content {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  color: #409eff;
}

.chart-card {
  margin-top: 20px;
}
</style>

