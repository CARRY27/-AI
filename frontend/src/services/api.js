import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        ElMessage.error(data.detail || data.message || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// ========== API 接口 ==========

// 认证相关
export const authApi = {
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    return apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  register(userData) {
    return apiClient.post('/auth/register', userData)
  },
  
  getUserInfo() {
    return apiClient.get('/auth/me')
  },
  
  logout() {
    return apiClient.post('/auth/logout')
  }
}

// 文件相关
export const fileApi = {
  upload(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post('/files/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })
  },
  
  getFiles(params) {
    return apiClient.get('/files/', { params })
  },
  
  getFile(fileId) {
    return apiClient.get(`/files/${fileId}`)
  },
  
  deleteFile(fileId) {
    return apiClient.delete(`/files/${fileId}`)
  },
  
  getFileStatus(fileId) {
    return apiClient.get(`/files/${fileId}/status`)
  }
}

// 对话相关
export const conversationApi = {
  create(data) {
    return apiClient.post('/conversations/', data)
  },
  
  getList(params) {
    return apiClient.get('/conversations/', { params })
  },
  
  getDetail(conversationId) {
    return apiClient.get(`/conversations/${conversationId}`)
  },
  
  getMessages(conversationId) {
    return apiClient.get(`/conversations/${conversationId}/messages`)
  },
  
  sendMessage(conversationId, content) {
    return apiClient.post(`/conversations/${conversationId}/messages`, { content })
  },
  
  delete(conversationId) {
    return apiClient.delete(`/conversations/${conversationId}`)
  },
  
  feedback(conversationId, messageId, rating, feedback) {
    return apiClient.post(
      `/conversations/${conversationId}/messages/${messageId}/feedback`,
      { rating, feedback }
    )
  },
  
  export(conversationId, format = 'markdown') {
    return apiClient.get(`/conversations/${conversationId}/export`, {
      params: { format },
      responseType: 'blob'
    })
  }
}

// 反馈相关
export const feedbackApi = {
  create(messageId, data) {
    return apiClient.post(`/feedback/messages/${messageId}`, data)
  },
  
  get(messageId) {
    return apiClient.get(`/feedback/messages/${messageId}`)
  },
  
  delete(messageId) {
    return apiClient.delete(`/feedback/messages/${messageId}`)
  },
  
  getOrgStats(days = 30) {
    return apiClient.get('/feedback/stats/org', { params: { days } })
  },
  
  getDailyStats(days = 7) {
    return apiClient.get('/feedback/stats/daily', { params: { days } })
  },
  
  getRecentNegative(limit = 20) {
    return apiClient.get('/feedback/negative/recent', { params: { limit } })
  },
  
  resolveNegative(feedbackId, resolutionNote) {
    return apiClient.patch(`/feedback/negative/${feedbackId}/resolve`, {
      resolution_note: resolutionNote
    })
  }
}

// 管理相关
export const adminApi = {
  getStats() {
    return apiClient.get('/admin/stats')
  },
  
  reindex(fileId) {
    return apiClient.post('/admin/reindex', { file_id: fileId })
  }
}

export default apiClient

