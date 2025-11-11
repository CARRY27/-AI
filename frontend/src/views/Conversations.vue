<template>
  <div class="conversations-container">
    <div class="page-header">
      <h2>💬 历史对话</h2>
    </div>
    
    <el-card class="conversations-list">
      <el-table :data="conversations" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="message_count" label="消息数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_message_at" label="最后活动" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_message_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleViewConversation(row)"
            >
              查看
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDeleteConversation(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadConversations"
        @size-change="loadConversations"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { conversationApi } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const conversations = ref([])
const loading = ref(false)

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadConversations = async () => {
  try {
    loading.value = true
    const response = await conversationApi.getList({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    conversations.value = response
  } catch (error) {
    console.error('加载对话列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleViewConversation = (conversation) => {
  router.push({ name: 'Chat', query: { id: conversation.id } })
}

const handleDeleteConversation = async (conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话 "${conversation.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await conversationApi.delete(conversation.id)
    ElMessage.success('删除成功')
    await loadConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
.conversations-container {
  padding: 32px;
  background: #f8f9fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.conversations-list {
  min-height: 400px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.conversations-list :deep(.el-card__body) {
  padding: 24px;
}

.conversations-list :deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

.conversations-list :deep(.el-table th) {
  background: #f8f9fa;
  color: #6e6e73;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.conversations-list :deep(.el-table td) {
  color: #1a1a1a;
  font-size: 14px;
}

.conversations-list :deep(.el-button--primary) {
  color: #667eea;
  font-weight: 600;
}

.conversations-list :deep(.el-button--danger) {
  color: #f56c6c;
  font-weight: 600;
}

:deep(.el-pagination) {
  font-weight: 500;
}

:deep(.el-pagination .el-pager li) {
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>

