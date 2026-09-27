<template>
  <div class="page">
    <!-- 顶部 -->
    <div class="header">
      <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon></el-button>
      <span class="header-title">{{ subjectLabel }} · {{ typeName }}</span>
      <span></span>
    </div>

    <!-- 图片区 -->
    <div class="thumb-row">
      <div v-for="(item, i) in images" :key="i" class="thumb-wrap">
        <img :src="item.dataUrl" class="thumb-img" />
        <button class="thumb-remove" @click="removeImage(i)">×</button>
      </div>
      <div v-for="n in emptySlots" :key="'empty'+n" class="thumb-add" @click="triggerAdd">
        <el-icon :size="28" style="color:#9CA3AF"><Plus /></el-icon>
        <span>添加</span>
      </div>
    </div>

    <input ref="fileInput" type="file" accept="image/*"
      style="display:none" @change="onFileChange" />

    <!-- 提示 -->
    <p style="text-align:center;font-size:12px;color:#9CA3AF;margin:8px 16px">
      至少上传一张图片，AI 会自动判断题目和作答
    </p>

    <!-- 提交按钮 -->
    <div style="padding:16px">
      <el-button type="primary" size="large" style="width:100%" :loading="submitting"
        :disabled="totalCount === 0" @click="submit">
        {{ submitLabel }}
      </el-button>
    </div>

    <!-- 进度状态 -->
    <div v-if="submitting || errorInfo" style="margin:0 16px 16px">
      <div v-if="submitting" style="background:#EFF6FF;border-radius:12px;padding:12px 14px">
        <div v-for="(step, i) in steps" :key="i"
          style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:13px">
          <span v-if="step.status === 'done'" style="color:#10B981">✓</span>
          <span v-else-if="step.status === 'active'" style="color:#4A7CFF">⋯</span>
          <span v-else style="color:#D1D5DB">○</span>
          <span :style="step.status === 'active' ? 'color:#1D4ED8;font-weight:600' : step.status === 'done' ? 'color:#374151' : 'color:#9CA3AF'">
            {{ step.label }}
          </span>
        </div>
      </div>

      <div v-if="errorInfo" style="background:#FEF2F2;border-radius:12px;padding:12px 14px;margin-top:8px">
        <div style="font-size:13px;font-weight:600;color:#B91C1C;margin-bottom:6px">❌ {{ errorInfo.title }}</div>
        <div style="font-size:12px;color:#6B7280;line-height:1.6">{{ errorInfo.message }}</div>
        <div v-if="errorInfo.recordId" style="margin-top:8px;background:#FFF;border-radius:8px;padding:8px 10px">
          <div style="font-size:11px;color:#9CA3AF;margin-bottom:2px">提交 ID（截图发给老师）</div>
          <div style="font-size:13px;font-family:monospace;color:#374151;word-break:break-all">{{ errorInfo.recordId }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { recordApi } from '@/api/index'

const SUBJECT_LABELS = { math:'数学', chinese:'语文', english:'英语', physics:'物理', chemistry:'化学', biology:'生物' }

const route = useRoute()
const router = useRouter()

const subjectId = route.params.subjectId
const subjectLabel = computed(() => SUBJECT_LABELS[subjectId] ?? subjectId)
const typeId = route.query.typeId || null
const typeName = route.query.typeName ? decodeURIComponent(route.query.typeName) : '通用批改'

const fileInput = ref(null)
const images = ref([])  // [{dataUrl, file}]
const submitting = ref(false)
const errorInfo = ref(null)

const STEP_DEFS = [
  { key: 'upload', label: '上传图片' },
  { key: 'llm',    label: 'AI 批改中' },
  { key: 'save',   label: '保存结果' },
]
const currentStep = ref('')
const steps = computed(() => STEP_DEFS.map(s => ({
  ...s,
  status: currentStep.value === s.key ? 'active'
        : STEP_DEFS.findIndex(x => x.key === s.key) < STEP_DEFS.findIndex(x => x.key === currentStep.value) ? 'done'
        : 'pending'
})))

const submitLabel = computed(() => {
  if (!submitting.value) return '提交批改'
  const active = STEP_DEFS.find(s => s.key === currentStep.value)
  return active ? active.label + '…' : '处理中…'
})

const totalCount = computed(() => images.value.length)
const emptySlots = computed(() => Math.max(0, 4 - images.value.length))

function triggerAdd() {
  if (fileInput.value) fileInput.value.value = ''
  fileInput.value?.click()
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = ev => {
    images.value.push({ dataUrl: ev.target.result, file })
  }
  reader.readAsDataURL(file)
}

function removeImage(index) {
  images.value.splice(index, 1)
}

async function submit() {
  if (totalCount.value === 0) return
  submitting.value = true
  errorInfo.value = null
  currentStep.value = 'upload'
  try {
    const fd = new FormData()
    for (const item of images.value) fd.append('files', item.file)
    fd.append('subject', subjectId)
    if (typeId) fd.append('exercise_type_id', typeId)

    currentStep.value = 'llm'
    let result
    try {
      result = await recordApi.submit(fd)
    } catch (e) {
      // 后端返回了 record_id（LLM 阶段失败）
      const detail = e?.detail
      if (detail?.record_id) {
        errorInfo.value = {
          title: 'AI 批改失败',
          message: detail.message || '请联系老师',
          recordId: detail.record_id,
        }
      } else {
        errorInfo.value = {
          title: '提交失败',
          message: typeof detail === 'string' ? detail : '网络错误或服务器异常，请重试',
          recordId: null,
        }
      }
      return
    }

    currentStep.value = 'save'
    sessionStorage.setItem('last_record', JSON.stringify(result))
    router.push('/result/' + result.id)
  } catch (e) {
    errorInfo.value = {
      title: '未知错误',
      message: String(e),
      recordId: null,
    }
  } finally {
    submitting.value = false
    currentStep.value = ''
  }
}
</script>

<style scoped>
.page { background:#F8F9FB; min-height:100vh; padding-bottom:24px; }
.header {
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 16px; background:white; border-bottom:1px solid #F3F4F6;
}
.header-title { font-size:16px; font-weight:600; }
.thumb-row {
  display:flex; gap:10px; padding:16px 16px 8px; flex-wrap:wrap;
}
.thumb-wrap {
  position:relative; width:96px; height:96px;
}
.thumb-img {
  width:96px; height:96px; object-fit:cover; border-radius:12px;
  border:1px solid #E5E7EB; display:block;
}
.thumb-remove {
  position:absolute; top:-6px; right:-6px;
  width:20px; height:20px; border-radius:50%;
  background:#EF4444; color:white; border:none;
  font-size:14px; line-height:1; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  padding:0;
}
.thumb-add {
  width:96px; height:96px; border:2px dashed #D1D5DB;
  border-radius:12px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; cursor:pointer;
  background:white; gap:4px; color:#9CA3AF; font-size:12px;
}
.thumb-add:hover { border-color:#4A7CFF; color:#4A7CFF; }
</style>
