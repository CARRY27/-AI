<template>
  <div class="files-container">
    <div class="page-header">
      <h2>📁 文件管理</h2>
      <el-button type="primary" :icon="Upload" @click="showUploadDialog = true">
        上传文件
      </el-button>
    </div>
    
    <el-card class="files-list">
      <el-table :data="files" v-loading="loading" style="width: 100%">
        <el-table-column prop="original_filename" label="文件名" min-width="200" />
        <el-table-column prop="file_type" label="类型" width="80" />
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="切片数" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleViewFile(row)"
            >
              查看
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDeleteFile(row)"
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
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadFiles"
        @size-change="loadFiles"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>
    
    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文件"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".pdf,.docx,.txt,.html,.xlsx,.pptx,.md"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到这里 或 <em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOCX、TXT、HTML、XLSX、PPTX、MD 格式，文件大小不超过 50MB
          </div>
        </template>
      </el-upload>
      
      <el-progress
        v-if="uploadProgress > 0"
        :percentage="uploadProgress"
        :status="uploadProgress === 100 ? 'success' : undefined"
        style="margin-top: 16px"
      />
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!selectedFile"
          @click="handleUpload"
        >
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'

const files = ref([])
const loading = ref(false)
const showUploadDialog = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadFiles = async () => {
  try {
    loading.value = true
    const response = await fileApi.getFiles({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    
    files.value = response.files
    pagination.value.total = response.total
  } catch (error) {
    console.error('加载文件列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleUpload = async () => {
  if (!selectedFile.value) return
  
  try {
    uploading.value = true
    uploadProgress.value = 0
    
    await fileApi.upload(selectedFile.value, (progress) => {
      uploadProgress.value = progress
    })
    
    ElMessage.success('文件上传成功，正在处理中...')
    showUploadDialog.value = false
    selectedFile.value = null
    uploadProgress.value = 0
    
    await loadFiles()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

const handleViewFile = (file) => {
  ElMessage.info('查看文件详情功能开发中')
}

const handleDeleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.original_filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await fileApi.deleteFile(file.id)
    ElMessage.success('删除成功')
    await loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const getStatusType = (status) => {
  const typeMap = {
    'indexed': 'success',
    'parsing': 'warning',
    'chunking': 'warning',
    'embedding': 'warning',
    'failed': 'danger',
    'uploading': 'info',
    'uploaded': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'indexed': '已索引',
    'parsing': '解析中',
    'chunking': '切片中',
    'embedding': '向量化中',
    'failed': '失败',
    'uploading': '上传中',
    'uploaded': '已上传'
  }
  return textMap[status] || status
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.files-container {
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

.page-header :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  padding: 12px 24px;
  transition: all 0.2s;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.page-header :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.35);
}

.files-list {
  min-height: 400px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.files-list :deep(.el-card__body) {
  padding: 24px;
}

.files-list :deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

.files-list :deep(.el-table th) {
  background: #f8f9fa;
  color: #6e6e73;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.files-list :deep(.el-table td) {
  color: #1a1a1a;
  font-size: 14px;
}

.files-list :deep(.el-button--primary) {
  color: #667eea;
  font-weight: 600;
}

.files-list :deep(.el-button--danger) {
  color: #f56c6c;
  font-weight: 600;
}

.files-list :deep(.el-tag) {
  border-radius: 8px;
  padding: 4px 12px;
  font-weight: 500;
  font-size: 12px;
}

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
}

:deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-upload-dragger) {
  border-radius: 12px;
  border: 2px dashed rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}
</style>

