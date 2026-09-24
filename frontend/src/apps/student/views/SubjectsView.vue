<template>
  <div class="page">
    <div class="page-title">我的学科</div>

    <div v-if="loading" style="text-align:center;padding:40px">
      <el-icon class="is-loading" :size="28"><Loading /></el-icon>
    </div>
    <div v-else>
      <!-- 已订阅 -->
      <div v-if="subscribed.length">
        <div class="section-label">已订阅</div>
        <div class="subject-grid">
          <div v-for="s in subscribed" :key="s.subject"
            class="subject-card active" @click="$router.push('/subject/' + s.subject)">
            <div class="subject-icon">{{ s.icon }}</div>
            <div class="subject-name">{{ s.label }}</div>
            <div class="subject-stats">今日 {{ s.today_count }} 题 · 本月 {{ s.month_count }} 题</div>
            <div class="subject-expire">到期 {{ s.end_date }}</div>
          </div>
        </div>
      </div>

      <!-- 未订阅 -->
      <div v-if="unsubscribed.length">
        <div class="section-label">未开通学科</div>
        <div class="subject-grid">
          <div v-for="s in unsubscribed" :key="s.subject" class="subject-card locked">
            <div class="subject-icon">{{ s.icon }}</div>
            <div class="subject-name">{{ s.label }}</div>
            <div class="subject-lock"><el-icon><Lock /></el-icon> 未开通</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { subjectApi } from '@/api/index'
import { ElMessage } from 'element-plus'

const SUBJECT_META = {
  math:      { label: '数学', icon: '📐' },
  chinese:   { label: '语文', icon: '📖' },
  english:   { label: '英语', icon: '🔤' },
  physics:   { label: '物理', icon: '⚡' },
  chemistry: { label: '化学', icon: '🧪' },
  biology:   { label: '生物', icon: '🌱' },
}

const loading = ref(false)
const subscribed = ref([])
const unsubscribed = ref([])

async function load() {
  loading.value = true
  try {
    const data = await subjectApi.mySubjects()
    subscribed.value = (data.subscribed || []).map(s => ({
      ...s, ...SUBJECT_META[s.subject],
    }))
    unsubscribed.value = (data.unsubscribed || []).map(s => ({
      subject: s, ...SUBJECT_META[s],
    }))
  } catch {
    ElMessage.error('加载学科失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 16px 16px 80px; }
.page-title { font-size:20px; font-weight:700; margin-bottom:20px; color:#1a1a2e; }
.section-label { font-size:12px; color:#9CA3AF; margin:16px 0 8px; letter-spacing:1px; text-transform:uppercase; }
.subject-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.subject-card {
  background:white; border-radius:16px; padding:16px;
  box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
.subject-card.active { cursor:pointer; }
.subject-card.active:active { transform:scale(0.97); }
.subject-card.locked { opacity:0.5; }
.subject-icon { font-size:32px; margin-bottom:8px; }
.subject-name { font-size:16px; font-weight:600; margin-bottom:4px; }
.subject-stats { font-size:11px; color:#9CA3AF; margin-bottom:2px; }
.subject-expire { font-size:11px; color:#10B981; }
.subject-lock { font-size:12px; color:#9CA3AF; display:flex; align-items:center; gap:4px; margin-top:4px; }
</style>
