<template>
  <el-container class="main-layout">
    <el-aside width="260px" class="sidebar">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
          </svg>
        </div>
        <div class="logo-text">
          <h2>DocAgent</h2>
          <p>AI 智能助手</p>
        </div>
      </div>
      
      <div class="menu-section">
        <div class="menu-label">工作空间</div>
        <div class="menu-items">
          <div 
            :class="['menu-item', { active: activeMenu === '/' }]"
            @click="$router.push('/')"
          >
            <div class="menu-item-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12,3C6.5,3 2,6.58 2,11C2.05,13.15 3.06,15.17 4.75,16.5C4.75,17.1 4.33,18.67 2,21C4.37,20.89 6.64,20 8.47,18.5C9.61,18.83 10.81,19 12,19C17.5,19 22,15.42 22,11C22,6.58 17.5,3 12,3M12,17C7.58,17 4,14.31 4,11C4,7.69 7.58,5 12,5C16.42,5 20,7.69 20,11C20,14.31 16.42,17 12,17Z" />
              </svg>
            </div>
            <span class="menu-item-text">对话</span>
          </div>
          
          <div 
            :class="['menu-item', { active: activeMenu === '/files' }]"
            @click="$router.push('/files')"
          >
            <div class="menu-item-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z" />
              </svg>
            </div>
            <span class="menu-item-text">文件管理</span>
          </div>
          
          <div 
            :class="['menu-item', { active: activeMenu === '/conversations' }]"
            @click="$router.push('/conversations')"
          >
            <div class="menu-item-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12,3C6.5,3 2,6.58 2,11A7.74,7.74 0 0,0 4.78,16.5C4.68,17.5 4.25,19.03 2,21C4.93,20.84 7.5,19.76 9.46,18.12C10.25,18.29 11.12,18.4 12,18.4C17.5,18.4 22,14.82 22,10.2C22,5.58 17.5,3 12,3M12,16.4C7.58,16.4 4,13.61 4,10.2C4,6.79 7.58,3 12,3C16.42,3 20,6.79 20,10.2C20,13.61 16.42,16.4 12,16.4Z" />
              </svg>
            </div>
            <span class="menu-item-text">历史对话</span>
          </div>
        </div>
      </div>
      
      <div v-if="authStore.user?.role === 'admin'" class="menu-section">
        <div class="menu-label">管理</div>
        <div class="menu-items">
          <div 
            :class="['menu-item', { active: activeMenu === '/dashboard' }]"
            @click="$router.push('/dashboard')"
          >
            <div class="menu-item-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M3,13H11V3H3M3,21H11V15H3M13,21H21V11H13M13,3V9H21V3" />
              </svg>
            </div>
            <span class="menu-item-text">数据仪表盘</span>
          </div>
          
          <div 
            :class="['menu-item', { active: activeMenu === '/admin' }]"
            @click="$router.push('/admin')"
          >
            <div class="menu-item-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" />
              </svg>
            </div>
            <span class="menu-item-text">系统管理</span>
          </div>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="footer-actions">
          <el-tooltip content="帮助文档" placement="top">
            <button class="action-button" @click="handleHelp">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z" />
              </svg>
            </button>
          </el-tooltip>
          
          <el-tooltip content="系统设置" placement="top">
            <button class="action-button" @click="handleSettings">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10M10,22C9.75,22 9.54,21.82 9.5,21.58L9.13,18.93C8.5,18.68 7.96,18.34 7.44,17.94L4.95,18.95C4.73,19.03 4.46,18.95 4.34,18.73L2.34,15.27C2.21,15.05 2.27,14.78 2.46,14.63L4.57,12.97L4.5,12L4.57,11L2.46,9.37C2.27,9.22 2.21,8.95 2.34,8.73L4.34,5.27C4.46,5.05 4.73,4.96 4.95,5.05L7.44,6.05C7.96,5.66 8.5,5.32 9.13,5.07L9.5,2.42C9.54,2.18 9.75,2 10,2H14C14.25,2 14.46,2.18 14.5,2.42L14.87,5.07C15.5,5.32 16.04,5.66 16.56,6.05L19.05,5.05C19.27,4.96 19.54,5.05 19.66,5.27L21.66,8.73C21.79,8.95 21.73,9.22 21.54,9.37L19.43,11L19.5,12L19.43,13L21.54,14.63C21.73,14.78 21.79,15.05 21.66,15.27L19.66,18.73C19.54,18.95 19.27,19.04 19.05,18.95L16.56,17.95C16.04,18.34 15.5,18.68 14.87,18.93L14.5,21.58C14.46,21.82 14.25,22 14,22H10M11.25,4L10.88,6.61C9.68,6.86 8.62,7.5 7.85,8.39L5.44,7.35L4.69,8.65L6.8,10.2C6.4,11.37 6.4,12.64 6.8,13.8L4.68,15.36L5.43,16.66L7.86,15.62C8.63,16.5 9.68,17.14 10.87,17.38L11.24,20H12.76L13.13,17.39C14.32,17.14 15.37,16.5 16.14,15.62L18.57,16.66L19.32,15.36L17.2,13.81C17.6,12.64 17.6,11.37 17.2,10.2L19.31,8.65L18.56,7.35L16.15,8.39C15.38,7.5 14.32,6.86 13.12,6.62L12.75,4H11.25Z" />
              </svg>
            </button>
          </el-tooltip>
        </div>
        
        <el-dropdown trigger="click" placement="top-start" class="user-dropdown">
          <div class="user-profile">
            <el-avatar :size="40" :src="avatarUrl" class="user-avatar">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="user-details">
              <div class="user-name">{{ authStore.user?.username }}</div>
              <div class="user-role">{{ authStore.user?.role === 'admin' ? '管理员' : '用户' }}</div>
            </div>
            <div class="user-action">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z" />
              </svg>
            </div>
          </div>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleProfile">
                <el-icon><User /></el-icon>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-aside>
    
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const avatarUrl = computed(() => null)

const handleLogout = async () => {
  await authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const handleProfile = () => {
  ElMessage.info('个人资料功能开发中')
}

const handleHelp = () => {
  // 可以打开帮助文档或者新窗口
  window.open('/docs', '_blank')
}

const handleSettings = () => {
  ElMessage.info('系统设置功能开发中')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background: #f8f9fa;
}

.sidebar {
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02);
}

.logo {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.logo-text h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: -0.5px;
}

.logo-text p {
  font-size: 11px;
  color: #8e8e93;
  margin: 2px 0 0 0;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.menu-section {
  padding: 20px 16px 12px;
}

.menu-label {
  font-size: 11px;
  font-weight: 600;
  color: #8e8e93;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 12px 8px;
}

.menu-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.menu-item:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: translateX(2px);
}

.menu-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.menu-item.active .menu-item-icon,
.menu-item.active .menu-item-text {
  color: white;
}

.menu-item-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6e6e73;
  transition: color 0.2s;
}

.menu-item-text {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a1a;
  letter-spacing: -0.2px;
  transition: color 0.2s;
}

.menu-item:hover .menu-item-icon,
.menu-item:hover .menu-item-text {
  color: #667eea;
}

.menu-item.active:hover .menu-item-icon,
.menu-item.active:hover .menu-item-text {
  color: white;
}

.sidebar-footer {
  margin-top: auto;
  padding: 12px 16px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.footer-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  padding: 0 4px;
}

.action-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: #6e6e73;
}

.action-button:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
  color: #667eea;
  transform: translateY(-1px);
}

.action-button svg {
  transition: transform 0.2s;
}

.action-button:hover svg {
  transform: scale(1.1);
}

.user-dropdown {
  display: block;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(0, 0, 0, 0.02);
}

.user-profile:hover {
  background: rgba(0, 0, 0, 0.06);
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-size: 12px;
  color: #8e8e93;
  margin-top: 2px;
}

.user-action {
  color: #8e8e93;
  transition: transform 0.2s;
}

.user-profile:hover .user-action {
  transform: translateY(2px);
}

.main-content {
  background: #f8f9fa;
  padding: 0;
}
</style>

