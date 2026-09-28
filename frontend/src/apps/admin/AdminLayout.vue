<template>
  <el-container style="height:100vh">
    <el-aside width="220px" style="background:#1e1e2e">
      <div class="logo">⚙️ 管理后台</div>
      <el-menu router background-color="#1e1e2e" text-color="#ccc" active-text-color="#4A7CFF"
        :default-active="$route.path">
        <el-menu-item index="/mgmt/dashboard"><el-icon><DataLine /></el-icon>数据概览</el-menu-item>
        <el-menu-item index="/mgmt/users"><el-icon><User /></el-icon>账号管理</el-menu-item>
        <el-menu-item index="/mgmt/llm"><el-icon><Setting /></el-icon>AI模型配置</el-menu-item>
        <el-menu-item index="/mgmt/exercise-types"><el-icon><EditPen /></el-icon>题型管理</el-menu-item>
        <el-menu-item index="/mgmt/general-prompts"><el-icon><Document /></el-icon>通用模版</el-menu-item>
        <el-menu-item index="/mgmt/ocr-test"><el-icon><ScaleToOriginal /></el-icon>模型对比</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:white;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:flex-end;padding:0 20px">
        <span style="margin-right:12px;color:#666">{{ auth.user?.name }}</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <el-main style="background:#f5f7fa">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '@/stores/adminAuth'
import { EditPen, Document, ScaleToOriginal } from '@element-plus/icons-vue'

const auth = useAdminAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/mgmt/login')
}
</script>

<style scoped>
.logo {
  color: white;
  font-size: 18px;
  font-weight: 700;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
</style>
