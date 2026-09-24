<template>
  <div class="page">
    <div class="page-title">我的</div>

    <div class="profile-card">
      <div class="avatar">{{ auth.user?.name?.[0] ?? '学' }}</div>
      <div class="profile-info">
        <div class="profile-name">{{ auth.user?.name }}</div>
        <div class="profile-sub">{{ auth.user?.username }} · {{ gradeLabel }}</div>
      </div>
    </div>

    <div class="menu-section">
      <div class="menu-item" @click="$router.push('/mistakes')">
        <el-icon><Collection /></el-icon>
        <span>错题集</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>

    <div class="menu-section">
      <div class="menu-item danger" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        <span>退出登录</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const gradeLabel = computed(() => auth.user?.grade_level === 'junior' ? '初中' : '高中')

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.page { padding:16px 16px 80px; }
.page-title { font-size:20px; font-weight:700; margin-bottom:20px; }
.profile-card {
  background:white; border-radius:16px; padding:20px;
  display:flex; align-items:center; gap:16px;
  box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:20px;
}
.avatar {
  width:56px; height:56px; border-radius:50%;
  background:linear-gradient(135deg, #4A7CFF, #7C3AED);
  color:white; font-size:22px; font-weight:700;
  display:flex; align-items:center; justify-content:center;
}
.profile-name { font-size:18px; font-weight:700; margin-bottom:4px; }
.profile-sub { font-size:13px; color:#9CA3AF; }
.menu-section {
  background:white; border-radius:16px; margin-bottom:16px;
  box-shadow:0 1px 4px rgba(0,0,0,0.05); overflow:hidden;
}
.menu-item {
  display:flex; align-items:center; gap:12px;
  padding:16px; cursor:pointer; transition:background 0.15s; font-size:15px;
}
.menu-item:hover { background:#F9FAFB; }
.menu-item .arrow { margin-left:auto; color:#D1D5DB; }
.menu-item.danger { color:#EF4444; }
</style>
