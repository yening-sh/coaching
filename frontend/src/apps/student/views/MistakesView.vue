<template>
  <div class="page">
    <div class="page-title">错题集</div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filterSubject" size="small" clearable placeholder="全部学科" @change="load">
        <el-option v-for="s in subjects" :key="s.value" :value="s.value" :label="s.label" />
      </el-select>
      <el-select v-model="filterStatus" size="small" clearable placeholder="全部状态" @change="load">
        <el-option value="pending" label="待复习" />
        <el-option value="mastered" label="已掌握" />
      </el-select>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
    </div>
    <div v-else-if="!mistakes.length" style="text-align:center;padding:40px;color:#9CA3AF;font-size:13px">
      暂无错题
    </div>
    <div v-else>
      <div v-for="m in mistakes" :key="m.id" class="mistake-card" @click="openDetail(m)">
        <div class="mistake-row">
          <img v-if="m.image_url" :src="firstImage(m.image_url)" class="mistake-thumb" />
          <div class="mistake-body">
            <div style="display:flex;gap:6px;margin-bottom:6px">
              <el-tag size="small">{{ subjectLabel(m.subject) }}</el-tag>
              <el-tag size="small" :type="m.status === 'mastered' ? 'success' : 'warning'">
                {{ m.status === 'mastered' ? '已掌握' : '待复习' }}
              </el-tag>
            </div>
            <div class="mistake-summary">{{ m.ai_feedback?.summary || '查看详情' }}</div>
            <div style="font-size:11px;color:#9CA3AF;margin-top:4px">{{ fmtDate(m.created_at) }}</div>
          </div>
        </div>
        <div v-if="m.status === 'pending'" style="margin-top:10px">
          <el-button size="small" type="success" @click.stop="markMastered(m)">标记已掌握</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mistakeApi } from '@/api/index'
import { ElMessage } from 'element-plus'

const router = useRouter()

const SUBJECTS = [
  { value: 'math', label: '数学' },
  { value: 'chinese', label: '语文' },
  { value: 'english', label: '英语' },
  { value: 'physics', label: '物理' },
  { value: 'chemistry', label: '化学' },
  { value: 'biology', label: '生物' },
]
const subjects = SUBJECTS
function subjectLabel(v) { return SUBJECTS.find(s => s.value === v)?.label ?? v }
function fmtDate(t) {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN')
}
function firstImage(url) {
  if (!url) return ''
  try {
    const arr = JSON.parse(url)
    return Array.isArray(arr) ? arr[0] : url
  } catch {
    return url
  }
}

const loading = ref(false)
const mistakes = ref([])
const filterSubject = ref(null)
const filterStatus = ref(null)

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filterSubject.value) params.subject = filterSubject.value
    if (filterStatus.value) params.status = filterStatus.value
    mistakes.value = (await mistakeApi.list(params)).items ?? []
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function openDetail(m) {
  // 把 mistake 自身的数据存入 sessionStorage，ResultView 可独立渲染
  const recordData = {
    id: m.record_id || m.id,
    is_correct: false,
    output_schema: m.output_schema || 'simple',
    result: m.ai_feedback ? JSON.parse(m.ai_feedback) : {},
    subject: m.subject,
    image_url: m.image_url,
  }
  sessionStorage.setItem('last_record', JSON.stringify(recordData))
  router.push(`/result/${recordData.id}?from=mistakes`)
}

async function markMastered(m) {
  await mistakeApi.update(m.id, 'mastered')
  m.status = 'mastered'
  ElMessage.success('已标记为掌握')
}

onMounted(load)
</script>

<style scoped>
.page { padding:16px 16px 80px; }
.page-title { font-size:20px; font-weight:700; margin-bottom:16px; }
.filter-bar { display:flex; gap:8px; margin-bottom:16px; }
.mistake-card {
  background:white; border-radius:14px; padding:14px;
  box-shadow:0 1px 4px rgba(0,0,0,0.05); margin-bottom:10px;
  cursor:pointer;
}
.mistake-row { display:flex; gap:12px; }
.mistake-thumb { width:60px; height:60px; object-fit:cover; border-radius:8px; flex-shrink:0; }
.mistake-body { flex:1; min-width:0; }
.mistake-summary { font-size:13px; color:#4B5563; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
</style>
