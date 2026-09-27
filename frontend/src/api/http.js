import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 180000,  // AI 调用可能慢，最长 3 分钟
})

// 请求拦截：自动加 Token
http.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截：统一处理 401
http.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
      window.location.href = '/login'
    }
    return Promise.reject(err.response?.data || err)
  }
)

export default http
