<template>
  <div>
    <div class="page-header">
      <h2>模型对比测试</h2>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom:20px"
      description="上传图片，同时调用两个选定的对比模型，左右对比输出结果。在 AI模型配置 页面点击「对比」按钮选择2个模型（最多同时开启2个）。" />

    <!-- 上传区 -->
    <el-card style="margin-bottom:20px">
      <div style="display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap">
        <div style="flex:0 0 260px">
          <div style="margin-bottom:8px;font-size:13px;font-weight:500;color:#374151">上传图片（最多4张）</div>
          <el-upload
            v-model:file-list="fileList"
            action=""
            :auto-upload="false"
            :limit="4"
            accept="image/*"
            list-type="picture-card"
            :on-exceed="() => ElMessage.warning('最多上传4张图片')"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </div>
        <div style="flex:1;min-width:280px">
          <div style="margin-bottom:8px;font-size:13px;font-weight:500;color:#374151">Prompt</div>
          <el-input
            v-model="prompt"
            type="textarea"
            :rows="10"
            placeholder="输入发给模型的指令…"
            style="font-size:13px;font-family:ui-monospace,monospace"
          />
          <el-button
            type="primary"
            style="margin-top:12px;width:100%"
            :loading="running"
            :disabled="!fileList.length || !prompt.trim()"
            @click="runCompare"
          >
            {{ running ? '运行中…' : '开始对比' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 结果对比 -->
    <div v-if="result" class="compare-grid">
      <!-- 模型 A（激活模型） -->
      <el-card class="result-card">
        <template #header>
          <div class="result-header">
            <div>
              <span class="model-label">激活模型</span>
              <span class="model-name">{{ result.model_a.name }}</span>
              <span class="model-id">{{ result.model_a.model_id }}</span>
            </div>
            <div class="meta-badges">
              <el-tag size="small" type="success">{{ result.model_a.elapsed }}s</el-tag>
              <el-tag size="small" type="info">↑{{ result.model_a.tok_in }} ↓{{ result.model_a.tok_out }}</el-tag>
            </div>
          </div>
        </template>
        <div v-if="result.model_a.error" class="error-text">{{ result.model_a.error }}</div>
        <pre v-else class="result-text">{{ result.model_a.text }}</pre>
      </el-card>

      <!-- 模型 B（OCR模型） -->
      <el-card class="result-card">
        <template #header>
          <div class="result-header">
            <div>
              <span class="model-label ocr">OCR模型</span>
              <span class="model-name">{{ result.model_b.name }}</span>
              <span class="model-id">{{ result.model_b.model_id }}</span>
            </div>
            <div class="meta-badges">
              <el-tag size="small" type="success">{{ result.model_b.elapsed }}s</el-tag>
              <el-tag size="small" type="info">↑{{ result.model_b.tok_in }} ↓{{ result.model_b.tok_out }}</el-tag>
            </div>
          </div>
        </template>
        <div v-if="result.model_b.error" class="error-text">{{ result.model_b.error }}</div>
        <pre v-else class="result-text">{{ result.model_b.text }}</pre>
      </el-card>
    </div>

    <!-- 上传的图片预览 -->
    <el-card v-if="result?.image_urls?.length" style="margin-top:16px">
      <div style="font-size:13px;font-weight:500;color:#374151;margin-bottom:10px">上传的图片</div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <img v-for="url in result.image_urls" :key="url" :src="url"
          style="height:120px;border-radius:6px;object-fit:contain;border:1px solid #E5E7EB;cursor:pointer"
          @click="previewUrl = url; showPreview = true" />
      </div>
    </el-card>

    <!-- 图片全屏预览 -->
    <el-dialog v-model="showPreview" width="90%" top="5vh" :show-close="true" @closed="showPreview = false; previewUrl = null">
      <img :src="previewUrl" style="width:100%;max-height:85vh;object-fit:contain" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { adminApi } from '@/api/index'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const fileList = ref([])
const running = ref(false)
const result = ref(null)
const previewUrl = ref(null)
const showPreview = ref(false)

const DEFAULT_PROMPT = `请识别图片中的所有文字，按以下结构输出：

【题目原文】
照录印刷体题目原文。填空题的空格处保留 (1)_____ 格式和括号内提示词，不要填入任何答案。

【学生作答】
照录学生的手写内容（黑色/蓝色笔迹），按题号对齐列出：
(1) xxx  (2) xxx  (3) xxx ...

【教师批改】
仅列出有红笔修改的空，格式：(编号) 学生答案 → 红笔内容
如无红色批注则写"无"。

【按题号对齐】
每空一条，格式如下：
(1) 题干片段: "..." | 学生答案: xxx | 教师批注: xxx或无
(2) 题干片段: "..." | 学生答案: xxx | 教师批注: xxx或无
...`

const prompt = ref(DEFAULT_PROMPT)

async function runCompare() {
  if (!fileList.value.length) return
  running.value = true
  result.value = null
  try {
    const formData = new FormData()
    for (const f of fileList.value) {
      formData.append('files', f.raw)
    }
    formData.append('prompt', prompt.value)
    result.value = await adminApi.compareLLM(formData)
  } catch (e) {
    ElMessage.error(e?.detail || e?.message || '请求失败')
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }

.compare-grid {
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:16px;
}
@media (max-width: 900px) {
  .compare-grid { grid-template-columns: 1fr; }
}

.result-card { height:100%; }

.result-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  flex-wrap:wrap;
  gap:8px;
}
.model-label {
  display:inline-block;
  font-size:11px;
  font-weight:600;
  background:#DCFCE7;
  color:#166534;
  border-radius:4px;
  padding:1px 6px;
  margin-right:6px;
}
.model-label.ocr {
  background:#FFF7ED;
  color:#C2410C;
}
.model-name {
  font-size:14px;
  font-weight:600;
  color:#111827;
  margin-right:6px;
}
.model-id {
  font-size:12px;
  color:#9CA3AF;
}
.meta-badges { display:flex; gap:6px; }

.result-text {
  white-space: pre-wrap;
  word-break: break-all;
  font-size:13px;
  line-height:1.7;
  color:#1F2937;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  margin:0;
  max-height:600px;
  overflow-y:auto;
}
.error-text {
  color:#EF4444;
  font-size:13px;
  line-height:1.6;
}
</style>
