<template>
  <div class="page">
    <!-- 顶部标题栏 -->
    <div class="header">
      <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon></el-button>
      <span class="header-title">{{ subjectLabel }} · {{ gradeLabel }}</span>
      <span></span>
    </div>

    <!-- 拍照批改按钮 -->
    <div class="camera-banner" @click="openTypeSelector">
      <el-icon :size="40"><Camera /></el-icon>
      <div style="margin-top:8px;font-size:15px;font-weight:600">拍照批改</div>
      <div style="font-size:12px;opacity:0.8;margin-top:2px">拍下题目，AI 帮你批改</div>
    </div>

    <!-- 最近记录 -->
    <div class="section-label">最近提交</div>
    <div v-if="loadingRecords" style="text-align:center;padding:30px">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
    </div>
    <div v-else-if="!records.length" style="text-align:center;padding:30px;color:#9CA3AF;font-size:13px">
      暂无记录
    </div>
    <div v-else>
      <div v-for="r in records" :key="r.id" class="record-card"
        @click="$router.push('/result/' + r.id)">
        <img v-if="r.image_url" :src="firstImage(r.image_url)" class="record-thumb" />
        <div class="record-body">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="font-size:11px;color:#9CA3AF">{{ fmtTime(r.created_at) }}</span>
            <span v-if="r.llm_model" style="font-size:10px;color:#C4B5FD;background:#F5F3FF;border-radius:4px;padding:1px 5px">{{ r.llm_model }}</span>
          </div>
          <div class="record-preview">点击查看批改详情</div>
        </div>
        <el-button text type="danger" size="small" @click.stop="deleteRecord(r)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 题型选择弹窗 -->
    <el-dialog v-model="typeDialog" title="选择题型" width="320px">
      <div v-if="loadingTypes" style="text-align:center;padding:20px">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      </div>
      <div v-else-if="!exerciseTypes.length" style="color:#9CA3AF;text-align:center;padding:16px">
        暂无题型，请联系管理员配置
      </div>
      <div v-else class="type-list">
        <div v-for="t in exerciseTypes" :key="t.id"
          class="type-item" @click="selectType(t)">
          <span>{{ t.name }}</span>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { recordApi, subjectApi } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const SUBJECT_LABELS = { math:'数学', chinese:'语文', english:'英语', physics:'物理', chemistry:'化学', biology:'生物' }

const route = useRoute()
const router = useRouter()
const subjectId = route.params.subjectId
const subjectLabel = computed(() => SUBJECT_LABELS[subjectId] ?? subjectId)

const auth = useAuthStore()
const gradeLabel = computed(() => auth.user?.grade_level === 'junior' ? '初中' : '高中')

const loadingRecords = ref(false)
const records = ref([])
const typeDialog = ref(false)
const loadingTypes = ref(false)
const exerciseTypes = ref([])

function fmtTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
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

async function loadRecords() {
  loadingRecords.value = true
  try {
    records.value = await recordApi.recent(subjectId)
  } catch {
    ElMessage.error('加载记录失败')
  } finally {
    loadingRecords.value = false
  }
}

async function openTypeSelector() {
  typeDialog.value = true
  if (exerciseTypes.value.length) return
  loadingTypes.value = true
  try {
    exerciseTypes.value = await subjectApi.exerciseTypes(subjectId)
    if (exerciseTypes.value.length === 1) {
      typeDialog.value = false
      selectType(exerciseTypes.value[0])
    }
  } catch {
    ElMessage.error('加载题型失败')
  } finally {
    loadingTypes.value = false
  }
}

function selectType(type) {
  typeDialog.value = false
  router.push(`/camera/${subjectId}?typeId=${type.id}&typeName=${encodeURIComponent(type.name)}`)
}

async function deleteRecord(r) {
  try {
    await ElMessageBox.confirm(
      '该题目和批改结果将永久删除，无法恢复。',
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger' }
    )
  } catch {
    return
  }
  try {
    await recordApi.delete(r.id)
    records.value = records.value.filter(x => x.id !== r.id)
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadRecords)
</script>

<style scoped>
.page { padding: 0 0 80px; background:#F8F9FB; min-height:100vh; }
.header {
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 16px; background:white; border-bottom:1px solid #F3F4F6;
}
.header-title { font-size:16px; font-weight:600; }
.camera-banner {
  margin:16px; border-radius:20px;
  background:linear-gradient(135deg, #4A7CFF 0%, #7C3AED 100%);
  color:white; text-align:center; padding:28px 16px;
  cursor:pointer; transition:transform 0.15s;
}
.camera-banner:active { transform:scale(0.98); }
.section-label { padding:0 16px; font-size:12px; color:#9CA3AF; margin:8px 0 4px; letter-spacing:1px; }
.record-card {
  display:flex; align-items:center; gap:12px;
  background:white; margin:0 16px 10px; border-radius:14px; padding:12px;
  box-shadow:0 1px 4px rgba(0,0,0,0.05); cursor:pointer;
}
.record-card:active { transform:scale(0.99); }
.record-thumb { width:56px; height:56px; object-fit:cover; border-radius:8px; flex-shrink:0; }
.record-body { flex:1; min-width:0; }
.record-preview { font-size:13px; color:#9CA3AF; }
.type-list { display:flex; flex-direction:column; gap:8px; }
.type-item {
  display:flex; justify-content:space-between; align-items:center;
  padding:14px 16px; background:#F8F9FB; border-radius:12px;
  cursor:pointer; font-size:15px; font-weight:500;
  transition:background 0.15s;
}
.type-item:hover { background:#EEF2FF; }
</style>
