<template>
  <div class="chat-container">
    <div class="chat-header">
      <h3>💬 {{ currentConversation?.title || '新对话' }}</h3>
      <el-space>
        <el-button
          v-if="currentConversation"
          :icon="Download"
          @click="handleExport"
        >
          导出
        </el-button>
        <el-button
          type="primary"
          :icon="Plus"
          @click="createNewConversation"
        >
          新对话
        </el-button>
      </el-space>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <el-empty v-if="messages.length === 0" description="开始您的第一个问题吧" />
      
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', message.role]"
      >
        <div class="message-avatar">
          <el-avatar v-if="message.role === 'user'" :size="36">
            {{ authStore.user?.username?.charAt(0).toUpperCase() }}
          </el-avatar>
          <el-avatar v-else :size="36" style="background: #409eff">
            🤖
          </el-avatar>
        </div>
        
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>
          
          <!-- 置信度显示 -->
          <div v-if="message.confidence !== undefined" class="message-confidence">
            <el-progress 
              :percentage="Math.round(message.confidence * 100)" 
              :color="getConfidenceColor(message.confidence)"
              :stroke-width="6"
              :show-text="true"
            />
            <span class="confidence-label">置信度: {{ (message.confidence * 100).toFixed(1) }}%</span>
          </div>
          
          <!-- AI消息反馈按钮 -->
          <div v-if="message.role === 'assistant' && message.id" class="message-feedback">
            <div class="feedback-buttons">
              <el-tooltip content="有帮助" placement="top">
                <button 
                  :class="['feedback-btn', { active: message.feedback === 'positive' }]"
                  @click="handleFeedback(message, 'positive')"
                >
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M23,10C23,8.89 22.1,8 21,8H14.68L15.64,3.43C15.66,3.33 15.67,3.22 15.67,3.11C15.67,2.7 15.5,2.32 15.23,2.05L14.17,1L7.59,7.58C7.22,7.95 7,8.45 7,9V19A2,2 0 0,0 9,21H18C18.83,21 19.54,20.5 19.84,19.78L22.86,12.73C22.95,12.5 23,12.26 23,12V10M1,21H5V9H1V21Z" />
                  </svg>
                </button>
              </el-tooltip>
              
              <el-tooltip content="没有帮助" placement="top">
                <button 
                  :class="['feedback-btn', { active: message.feedback === 'negative' }]"
                  @click="handleFeedback(message, 'negative')"
                >
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M19,15H23V3H19M15,3H6C5.17,3 4.46,3.5 4.16,4.22L1.14,11.27C1.05,11.5 1,11.74 1,12V14A2,2 0 0,0 3,16H9.31L8.36,20.57C8.34,20.67 8.33,20.77 8.33,20.88C8.33,21.3 8.5,21.67 8.77,21.94L9.83,23L16.41,16.41C16.78,16.05 17,15.55 17,15V5C17,3.89 16.1,3 15,3Z" />
                  </svg>
                </button>
              </el-tooltip>
            </div>
          </div>
          
          <div v-if="message.source_refs && message.source_refs.length > 0" class="message-sources">
            <el-divider />
            <div class="sources-title">📎 参考来源：</div>
            <el-tag
              v-for="(source, index) in message.source_refs"
              :key="index"
              class="source-tag"
              size="small"
            >
              {{ source.file_name }} - 第{{ source.page }}页
            </el-tag>
          </div>
        </div>
      </div>
      
      <div v-if="loading" class="message assistant">
        <div class="message-avatar">
          <el-avatar :size="36" style="background: #409eff">🤖</el-avatar>
        </div>
        <div class="message-content">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在思考中...
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入您的问题..."
        @keyup.ctrl.enter="sendMessage"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="loading"
        :disabled="!inputMessage.trim()"
        @click="sendMessage"
      >
        发送 (Ctrl+Enter)
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { conversationApi, feedbackApi } from '@/services/api'
import { ElMessage } from 'element-plus'
import { Plus, Promotion, Loading, Download } from '@element-plus/icons-vue'
import { useExport } from '@/composables/useExport'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { showExportDialog } = useExport()

const currentConversation = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

const createNewConversation = async () => {
  try {
    const conversation = await conversationApi.create({ title: '新对话' })
    currentConversation.value = conversation
    messages.value = []
    
    // 更新 URL 但不刷新页面
    router.replace({ query: { id: conversation.id } })
    
    ElMessage.success('已创建新对话')
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('创建对话失败')
  }
}

const loadConversation = async (conversationId) => {
  try {
    loading.value = true
    
    // 获取对话详情
    const conversation = await conversationApi.getDetail(conversationId)
    currentConversation.value = conversation
    
    // 获取对话消息
    const messagesData = await conversationApi.getMessages(conversationId)
    messages.value = messagesData.map(msg => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      source_refs: msg.source_refs || [],
      confidence: msg.confidence
    }))
    
    scrollToBottom()
  } catch (error) {
    console.error('加载对话失败:', error)
    ElMessage.error('加载对话失败')
    // 如果加载失败，清除错误的 ID
    router.replace({ query: {} })
  } finally {
    loading.value = false
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  if (!currentConversation.value) {
    await createNewConversation()
  }
  
  const userMessage = inputMessage.value
  inputMessage.value = ''
  
  // 添加用户消息到界面
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    source_refs: []
  })
  
  scrollToBottom()
  
  try {
    loading.value = true
    
    const response = await conversationApi.sendMessage(
      currentConversation.value.id,
      userMessage
    )
    
    messages.value.push({
      id: response.message_id,
      role: 'assistant',
      content: response.answer,
      source_refs: response.sources || []
    })
    
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')
  } finally {
    loading.value = false
  }
}

const formatMessage = (content) => {
  // 简单的 Markdown 格式化
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// 导出对话
const handleExport = async () => {
  if (!currentConversation.value) return
  await showExportDialog(
    currentConversation.value.id,
    currentConversation.value.title
  )
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67c23a'  // 高置信度 - 绿色
  if (confidence >= 0.6) return '#e6a23c'  // 中等置信度 - 橙色
  return '#f56c6c'  // 低置信度 - 红色
}

// 处理反馈
const handleFeedback = async (message, feedbackType) => {
  try {
    // 如果点击的是相同类型，则取消反馈
    if (message.feedback === feedbackType) {
      await feedbackApi.delete(message.id)
      message.feedback = null
      ElMessage.success('已取消反馈')
    } else {
      // 创建或更新反馈
      await feedbackApi.create(message.id, {
        feedback_type: feedbackType,
        rating: feedbackType === 'positive' ? 5 : 1
      })
      message.feedback = feedbackType
      ElMessage.success(feedbackType === 'positive' ? '感谢您的反馈！' : '我们会改进的！')
    }
  } catch (error) {
    console.error('反馈失败:', error)
    ElMessage.error('反馈失败，请重试')
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 初始化对话
const initConversation = async () => {
  const conversationId = route.query.id
  
  if (conversationId) {
    // 如果 URL 有对话 ID，加载该对话
    await loadConversation(conversationId)
  }
  // 如果没有 ID，等待用户发送消息时再创建（或点击新建按钮）
}

onMounted(async () => {
  await initConversation()
})

// 监听路由变化，支持从历史对话页面跳转
watch(() => route.query.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadConversation(newId)
  }
})

watch(() => messages.value.length, scrollToBottom)
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.chat-header {
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.chat-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.chat-header :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.2s;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.chat-header :deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.chat-header :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.chat-header :deep(.el-button--primary:hover) {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.35);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background: #f8f9fa;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.15);
}

.message {
  display: flex;
  gap: 16px;
  margin-bottom: 28px;
  animation: messageSlideIn 0.3s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-avatar :deep(.el-avatar) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-weight: 600;
}

.message-content {
  flex: 1;
  background: white;
  padding: 16px 20px;
  border-radius: 16px;
  max-width: 80%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.message.user .message-text {
  color: white;
}

.message-text {
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: #1a1a1a;
  font-size: 15px;
}

.message-confidence {
  margin-top: 16px;
  padding: 14px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.confidence-label {
  font-size: 13px;
  color: #6e6e73;
  margin-left: 10px;
  font-weight: 500;
}

.message-feedback {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.feedback-buttons {
  display: flex;
  gap: 8px;
}

.feedback-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: white;
  color: #8e8e93;
  cursor: pointer;
  transition: all 0.2s;
}

.feedback-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
}

.feedback-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
}

.feedback-btn.active:hover {
  background: linear-gradient(135deg, #7688f0 0%, #8558ac 100%);
}

.message-sources {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.sources-title {
  font-size: 13px;
  color: #6e6e73;
  margin-bottom: 10px;
  font-weight: 600;
}

.source-tag {
  margin-right: 8px;
  margin-bottom: 6px;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 500;
}

.chat-input {
  padding: 20px 32px 24px;
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  gap: 12px;
  align-items: flex-end;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.02);
}

.chat-input :deep(.el-textarea) {
  flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  border-radius: 14px;
  padding: 14px 18px;
  font-size: 15px;
  line-height: 1.6;
  transition: all 0.2s;
  resize: none;
  background: #f8f9fa;
}

.chat-input :deep(.el-textarea__inner:hover) {
  border-color: rgba(102, 126, 234, 0.3);
  background: white;
}

.chat-input :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.chat-input :deep(.el-button) {
  border-radius: 12px;
  padding: 14px 24px;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.chat-input :deep(.el-button:hover:not(:disabled)) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.35);
}

.chat-input :deep(.el-button:active:not(:disabled)) {
  transform: translateY(0);
}

.chat-input :deep(.el-button.is-disabled) {
  background: #e8e8e8;
  color: #a8a8a8;
  box-shadow: none;
}

:deep(.el-empty) {
  padding: 60px 0;
}

:deep(.el-empty__description) {
  color: #8e8e93;
  font-size: 15px;
  font-weight: 500;
}
</style>

