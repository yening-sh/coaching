import http from './http'
import adminHttp from './adminHttp'

export const authApi = {
  login: (username, password) => http.post('/auth/login', { username, password }),
  logout: () => http.post('/auth/logout'),
  me: () => http.get('/auth/me'),
}

export const subjectApi = {
  mySubjects: () => http.get('/subjects/my'),
  exerciseTypes: (subject) => http.get('/subjects/exercise-types', { params: { subject } }),
}

export const recordApi = {
  submit: (formData) => http.post('/records/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getThinking: (recordId) => http.post(`/records/${recordId}/thinking`),
  get: (recordId) => http.get(`/records/${recordId}`),
  delete: (recordId) => http.delete(`/records/${recordId}`),
  recent: (subject, limit = 100) => http.get('/records/recent', { params: { subject, limit } }),
}

export const mistakeApi = {
  add: (recordId) => http.post('/mistakes', { record_id: recordId }),
  list: (params) => http.get('/mistakes', { params }),
  update: (id, status) => http.patch(`/mistakes/${id}`, null, { params: { status } }),
}

export const adminApi = {
  // 账号
  getUsers: (params) => adminHttp.get('/admin/users', { params }),
  createUser: (data) => adminHttp.post('/admin/users', data),
  updateUser: (id, data) => adminHttp.patch(`/admin/users/${id}`, data),
  getUserRecords: (userId, params) => adminHttp.get(`/admin/users/${userId}/records`, { params }),

  // 订阅
  createSubscription: (data) => adminHttp.post('/admin/subscriptions', data),
  deleteSubscription: (id) => adminHttp.delete(`/admin/subscriptions/${id}`),

  // LLM 配置
  getLLMConfigs: () => adminHttp.get('/admin/llm-configs'),
  createLLMConfig: (data) => adminHttp.post('/admin/llm-configs', data),
  updateLLMConfig: (id, data) => adminHttp.patch(`/admin/llm-configs/${id}`, data),
  activateLLMConfig: (id) => adminHttp.post(`/admin/llm-configs/${id}/activate`),
  testLLMConfig: (id) => adminHttp.post(`/admin/llm-configs/${id}/test`),
  deleteLLMConfig: (id) => adminHttp.delete(`/admin/llm-configs/${id}`),

  // 统计
  getStatsOverview: () => adminHttp.get('/admin/stats/overview'),
  getStatsByUser: (days) => adminHttp.get('/admin/stats/by-user', { params: { days } }),
  getStatsDaily: (days) => adminHttp.get('/admin/stats/daily', { params: { days } }),

  // 题型管理
  getExerciseTypes: () => adminHttp.get('/admin/exercise-types'),
  createExerciseType: (data) => adminHttp.post('/admin/exercise-types', data),
  updateExerciseType: (id, data) => adminHttp.patch(`/admin/exercise-types/${id}`, data),
  deleteExerciseType: (id) => adminHttp.delete(`/admin/exercise-types/${id}`),

  // Prompt 版本管理
  getPromptVersions: (typeId) => adminHttp.get(`/admin/exercise-types/${typeId}/prompts`),
  createPromptVersion: (typeId, data) => adminHttp.post(`/admin/exercise-types/${typeId}/prompts`, data),
  updatePromptVersion: (typeId, promptId, data) => adminHttp.patch(`/admin/exercise-types/${typeId}/prompts/${promptId}`, data),
  activatePromptVersion: (typeId, promptId) => adminHttp.post(`/admin/exercise-types/${typeId}/prompts/${promptId}/activate`),
  deletePromptVersion: (typeId, promptId) => adminHttp.delete(`/admin/exercise-types/${typeId}/prompts/${promptId}`),

  // 通用 Prompt 模版
  getGeneralPrompts: () => adminHttp.get('/admin/general-prompts'),
  createGeneralPrompt: (data) => adminHttp.post('/admin/general-prompts', data),
  updateGeneralPrompt: (id, data) => adminHttp.patch(`/admin/general-prompts/${id}`, data),

  // OCR 对比测试
  setOcrLLMConfig: (id) => adminHttp.post(`/admin/llm-configs/${id}/set-ocr`),
  compareLLM: (formData) => adminHttp.post('/admin/llm-configs/compare', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
}
