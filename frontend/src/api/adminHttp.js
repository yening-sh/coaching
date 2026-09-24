import axios from 'axios'
import { useAdminAuthStore } from '@/stores/adminAuth'

const adminHttp = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

adminHttp.interceptors.request.use(config => {
  const auth = useAdminAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

adminHttp.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      const auth = useAdminAuthStore()
      auth.logout()
      window.location.href = '/mgmt/login'
    }
    return Promise.reject(err.response?.data || err)
  }
)

export default adminHttp
