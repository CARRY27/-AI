/**
 * 流式输出Hook
 * 支持SSE流式接收AI回答
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useStreaming() {
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const eventSource = ref(null)
  
  /**
   * 开始流式聊天
   * @param {number} conversationId - 对话ID
   * @param {string} question - 用户问题
   * @param {Function} onChunk - 接收到chunk时的回调
   * @param {Function} onComplete - 完成时的回调
   * @param {Function} onError - 错误时的回调
   */
  const startStreaming = (conversationId, question, { onChunk, onComplete, onError }) => {
    isStreaming.value = true
    streamingContent.value = ''
    
    // 构建SSE URL
    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/streaming/chat`
    
    // 创建EventSource（但SSE不支持POST，需要使用fetch）
    // 使用fetch + ReadableStream代替
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        question: question
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      // 读取流
      const readStream = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            isStreaming.value = false
            return
          }
          
          // 解码数据
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n\n')
          
          lines.forEach(line => {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.substring(6)
                const data = JSON.parse(jsonStr)
                
                if (data.type === 'start') {
                  streamingContent.value = ''
                } else if (data.type === 'chunk') {
                  streamingContent.value += data.content
                  if (onChunk) onChunk(data.content, streamingContent.value)
                } else if (data.type === 'complete') {
                  isStreaming.value = false
                  if (onComplete) onComplete(data)
                } else if (data.type === 'error') {
                  isStreaming.value = false
                  if (onError) onError(data.message)
                  ElMessage.error(data.message)
                }
              } catch (e) {
                console.error('Parse SSE data error:', e)
              }
            }
          })
          
          // 继续读取
          readStream()
        })
        .catch(error => {
          isStreaming.value = false
          if (onError) onError(error.message)
          ElMessage.error('连接中断')
        })
      }
      
      readStream()
    })
    .catch(error => {
      isStreaming.value = false
      if (onError) onError(error.message)
      ElMessage.error('连接失败: ' + error.message)
    })
  }
  
  /**
   * 停止流式输出
   */
  const stopStreaming = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isStreaming.value = false
  }
  
  return {
    isStreaming,
    streamingContent,
    startStreaming,
    stopStreaming
  }
}

