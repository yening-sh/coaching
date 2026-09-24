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
        {{ submitting ? '批改中，请稍候…' : '提交批改' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { recordApi } from '@/api/index'
import { ElMessage } from 'element-plus'

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
  try {
    const fd = new FormData()
    for (const item of images.value) fd.append('files', item.file)
    fd.append('subject', subjectId)
    if (typeId) fd.append('exercise_type_id', typeId)
    const result = await recordApi.submit(fd)
    sessionStorage.setItem('last_record', JSON.stringify(result))
    router.push('/result/' + result.id)
  } catch (e) {
    ElMessage.error(e?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
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
