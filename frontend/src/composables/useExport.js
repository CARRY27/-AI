/**
 * 导出功能Hook
 * 支持导出对话为Markdown/HTML/PDF
 */

import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/services/api'

export function useExport() {
  /**
   * 导出对话
   * @param {number} conversationId - 对话ID
   * @param {string} format - 导出格式：markdown, html, pdf
   * @param {string} filename - 文件名
   */
  const exportConversation = async (conversationId, format = 'markdown', filename = '对话导出') => {
    try {
      const response = await api.post('/export/conversation', {
        conversation_id: conversationId,
        format: format
      }, {
        responseType: 'blob'
      })
      
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // 根据格式设置文件扩展名
      const ext = {
        markdown: 'md',
        html: 'html',
        pdf: 'pdf'
      }[format] || 'txt'
      
      link.setAttribute('download', `${filename}.${ext}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      // 释放URL对象
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('导出成功')
    } catch (error) {
      console.error('Export error:', error)
      ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  /**
   * 显示导出选项对话框
   * @param {number} conversationId - 对话ID
   * @param {string} conversationTitle - 对话标题
   */
  const showExportDialog = async (conversationId, conversationTitle) => {
    try {
      const { value: format } = await ElMessageBox.prompt('选择导出格式', '导出对话', {
        confirmButtonText: '导出',
        cancelButtonText: '取消',
        inputType: 'select',
        inputOptions: {
          markdown: 'Markdown (.md)',
          html: 'HTML (.html)',
          pdf: 'PDF (.pdf)'
        },
        inputValue: 'markdown'
      })
      
      if (format) {
        await exportConversation(conversationId, format, conversationTitle)
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Export dialog error:', error)
      }
    }
  }
  
  return {
    exportConversation,
    showExportDialog
  }
}

