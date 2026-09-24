<template>
  <div class="login-page">
    <div class="login-logo">
      <div class="logo-icon">🎓</div>
      <h1>AI学习助手</h1>
      <p>专注初高中学科辅导</p>
    </div>
    <div class="login-card">
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="请输入账号" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large"
            prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = ref({ username: '', password: '' })

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    return ElMessage.warning('请输入账号和密码')
  }
  loading.value = true
  try {
    const user = await auth.login(form.value.username, form.value.password)
    router.push(user.role === 'admin' ? '/admin' : '/subjects')
  } catch (e) {
    ElMessage.error(e?.detail || '账号或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #4A7CFF 0%, #7C3AED 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}
.login-logo { text-align: center; margin-bottom: 36px; color: white; }
.logo-icon { font-size: 56px; margin-bottom: 12px; }
.login-logo h1 { font-size: 24px; font-weight: 700; }
.login-logo p { font-size: 13px; opacity: 0.8; margin-top: 4px; }
.login-card {
  background: white;
  border-radius: 24px;
  padding: 28px 24px;
  width: 100%;
  max-width: 360px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
</style>
