<template>
  <div class="dashboard-container">
    <div class="page-header">
      <h2>📊 管理仪表盘</h2>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 概览卡片 -->
    <el-row :gutter="16" class="overview-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic 
            title="总用户数" 
            :value="overview.total_users"
            :value-style="{ color: '#409EFF' }"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
          <div class="stat-footer">
            今日活跃: {{ overview.active_users_today }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic 
            title="总对话数" 
            :value="overview.total_conversations"
            :value-style="{ color: '#67C23A' }"
          >
            <template #prefix>
              <el-icon><ChatDotRound /></el-icon>
            </template>
          </el-statistic>
          <div class="stat-footer">
            今日新增: {{ overview.conversations_today }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic 
            title="总消息数" 
            :value="overview.total_messages"
            :value-style="{ color: '#E6A23C' }"
          >
            <template #prefix>
              <el-icon><ChatLineRound /></el-icon>
            </template>
          </el-statistic>
          <div class="stat-footer">
            今日新增: {{ overview.messages_today }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic 
            title="满意度" 
            :value="(overview.satisfaction_rate * 100).toFixed(1)"
            suffix="%"
            :value-style="{ color: '#F56C6C' }"
          >
            <template #prefix>
              <el-icon><Star /></el-icon>
            </template>
          </el-statistic>
          <div class="stat-footer">
            平均评分: {{ overview.average_rating.toFixed(1) }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能指标 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>📈 调用统计趋势</span>
          </template>
          <div id="call-stats-chart" style="height: 300px"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🔥 热门问题榜单</span>
          </template>
          <el-table :data="topQuestions" style="width: 100%" max-height="300">
            <el-table-column type="index" width="50" />
            <el-table-column prop="question" label="问题" show-overflow-tooltip />
            <el-table-column prop="count" label="次数" width="80" />
            <el-table-column prop="satisfaction_rate" label="满意度" width="100">
              <template #default="scope">
                {{ (scope.row.satisfaction_rate * 100).toFixed(0) }}%
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 模型使用统计 & 用户活跃度 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>💰 模型调用花费</span>
          </template>
          <el-table :data="modelUsage" style="width: 100%">
            <el-table-column prop="model_name" label="模型" />
            <el-table-column prop="total_calls" label="调用次数" />
            <el-table-column prop="total_input_tokens" label="输入Tokens">
              <template #default="scope">
                {{ formatNumber(scope.row.total_input_tokens) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_output_tokens" label="输出Tokens">
              <template #default="scope">
                {{ formatNumber(scope.row.total_output_tokens) }}
              </template>
            </el-table-column>
            <el-table-column prop="estimated_cost" label="估算成本">
              <template #default="scope">
                ${{ scope.row.estimated_cost.toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>👥 用户活跃度</span>
          </template>
          <el-table :data="userActivity" style="width: 100%" max-height="300">
            <el-table-column type="index" width="50" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="conversation_count" label="对话数" width="80" />
            <el-table-column prop="message_count" label="消息数" width="80" />
            <el-table-column prop="last_active" label="最后活跃" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.last_active) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统性能 & 敏感内容检测 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>⚡ 系统性能</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="平均响应时间">
              {{ overview.average_response_time_ms.toFixed(0) }} ms
            </el-descriptions-item>
            <el-descriptions-item label="成功率">
              {{ (overview.success_rate * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="已索引文件">
              {{ overview.indexed_files }} / {{ overview.total_files }}
            </el-descriptions-item>
            <el-descriptions-item label="存储使用">
              {{ formatStorage(overview.total_storage_bytes) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🛡️ 敏感内容检测率</span>
          </template>
          <div id="sensitive-chart" style="height: 200px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统健康状态 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>💚 系统健康状态</span>
          </template>
          <el-row :gutter="16">
            <el-col :span="6" v-for="(status, component) in systemHealth.components" :key="component">
              <div class="health-item">
                <el-tag :type="status === 'up' ? 'success' : 'danger'">
                  {{ component }}
                </el-tag>
                <span style="margin-left: 8px">{{ status === 'up' ? '正常' : '异常' }}</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  User, 
  ChatDotRound, 
  ChatLineRound, 
  Star, 
  Refresh 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/services/api'

// 数据
const overview = ref({
  total_users: 0,
  active_users_today: 0,
  total_conversations: 0,
  conversations_today: 0,
  total_messages: 0,
  messages_today: 0,
  total_files: 0,
  total_storage_bytes: 0,
  indexed_files: 0,
  average_response_time_ms: 0,
  success_rate: 0,
  satisfaction_rate: 0,
  average_rating: 0
})

const callStatistics = ref([])
const topQuestions = ref([])
const modelUsage = ref([])
const userActivity = ref([])
const sensitiveStats = ref([])
const systemHealth = ref({
  status: 'healthy',
  components: {
    database: 'up',
    redis: 'up',
    vector_db: 'up',
    storage: 'up'
  }
})

// 图表实例
let callStatsChart = null
let sensitiveChart = null

// 加载数据
const loadDashboardData = async () => {
  try {
    // 加载概览数据
    const overviewData = await api.get('/dashboard/overview')
    overview.value = overviewData

    // 加载调用统计
    const callStatsData = await api.get('/dashboard/call-statistics?days=7')
    callStatistics.value = callStatsData
    renderCallStatsChart(callStatsData)

    // 加载热门问题
    const questionsData = await api.get('/dashboard/top-questions?limit=10')
    topQuestions.value = questionsData

    // 加载模型使用统计
    const modelData = await api.get('/dashboard/model-usage?days=7')
    modelUsage.value = modelData

    // 加载用户活跃度
    const activityData = await api.get('/dashboard/user-activity?limit=10')
    userActivity.value = activityData

    // 加载敏感内容统计
    const sensitiveData = await api.get('/dashboard/sensitive-content-stats?days=7')
    sensitiveStats.value = sensitiveData
    renderSensitiveChart(sensitiveData)

    // 加载系统健康状态
    const healthData = await api.get('/dashboard/system-health')
    systemHealth.value = healthData

    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
    ElMessage.error('加载数据失败: ' + error.message)
  }
}

// 渲染调用统计图表
const renderCallStatsChart = (data) => {
  if (!callStatsChart) {
    callStatsChart = echarts.init(document.getElementById('call-stats-chart'))
  }

  const dates = data.map(d => d.date)
  const totalCalls = data.map(d => d.total_calls)
  const successCalls = data.map(d => d.success_calls)
  const failedCalls = data.map(d => d.failed_calls)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['总调用', '成功', '失败']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总调用',
        type: 'line',
        data: totalCalls,
        smooth: true
      },
      {
        name: '成功',
        type: 'line',
        data: successCalls,
        smooth: true
      },
      {
        name: '失败',
        type: 'line',
        data: failedCalls,
        smooth: true
      }
    ]
  }

  callStatsChart.setOption(option)
}

// 渲染敏感内容图表
const renderSensitiveChart = (data) => {
  if (!sensitiveChart) {
    sensitiveChart = echarts.init(document.getElementById('sensitive-chart'))
  }

  const dates = data.map(d => d.date)
  const detections = data.map(d => d.total_detections)
  const blocked = data.map(d => d.blocked_count)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['检测到', '已屏蔽']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '检测到',
        type: 'bar',
        data: detections
      },
      {
        name: '已屏蔽',
        type: 'bar',
        data: blocked
      }
    ]
  }

  sensitiveChart.setOption(option)
}

// 刷新数据
const refreshData = () => {
  loadDashboardData()
}

// 工具函数
const formatStorage = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

const formatNumber = (num) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  loadDashboardData()
  
  // 自动刷新（每5分钟）
  setInterval(() => {
    loadDashboardData()
  }, 5 * 60 * 1000)
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.overview-cards {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.stat-card :deep(.el-statistic) {
  text-align: center;
}

.stat-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #909399;
}

.health-item {
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 4px;
  text-align: center;
}

:deep(.el-card) {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-card__header) {
  background-color: #fafafa;
  font-weight: 600;
}
</style>

