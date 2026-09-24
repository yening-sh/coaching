<template>
  <div class="page">
    <!-- 顶部 -->
    <div class="header">
      <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon></el-button>
      <span class="header-title">批改结果</span>
      <span></span>
    </div>

    <div v-if="loading" style="text-align:center;padding:60px">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <div v-else-if="record">
      <!-- 图片 -->
      <div style="margin:16px">
        <template v-if="imageList.length > 1">
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <img v-for="(url, i) in imageList" :key="i" :src="url"
              style="width:calc(50% - 4px);border-radius:12px;display:block;object-fit:contain;background:#f0f0f0;max-height:220px" />
          </div>
        </template>
        <template v-else-if="imageList.length === 1">
          <img :src="imageList[0]" style="width:100%;border-radius:16px;display:block" />
        </template>
      </div>

      <!-- ── 作文题 ── -->
      <template v-if="isEssay">
        <!-- 分数卡 -->
        <div class="card essay-score-card">
          <div style="display:flex;align-items:center;gap:16px">
            <div class="score-circle">
              <span class="score-num">{{ record.result.score }}</span>
              <span class="score-total">/{{ record.result.score_breakdown ? 10 : 25 }}</span>
            </div>
            <div style="flex:1">
              <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:6px">
                {{ record.result.score_comment }}
              </div>
              <el-tag v-if="record.result.on_topic" type="success" size="small">切题 ✓</el-tag>
              <el-tag v-else type="danger" size="small">偏题 ✗</el-tag>
              <!-- 概要写作四维分项 -->
              <div v-if="record.result.score_breakdown" style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px">
                <span class="score-dim">内容 {{ record.result.score_breakdown.content }}/6</span>
                <span class="score-dim">语言 {{ record.result.score_breakdown.accuracy }}/2</span>
                <span class="score-dim">流畅 {{ record.result.score_breakdown.fluency }}/1</span>
                <span class="score-dim">改写 {{ record.result.score_breakdown.paraphrase }}/1</span>
              </div>
            </div>
          </div>
          <div class="essay-overall">{{ record.result.overall }}</div>
        </div>

        <!-- 逐句批注 -->
        <div class="card">
          <div class="card-title">📝 逐句批注</div>
          <div v-for="(s, si) in record.result.sentences" :key="si" class="sentence-block">
            <div class="sentence-text">
              <template v-if="s.errors && s.errors.length">
                <span v-for="(seg, idx) in buildSegments(s.original, s.errors)" :key="idx"
                  :class="seg.type === 'error' ? 'mark-error' : seg.type === 'suggestion' ? 'mark-suggestion' : ''">{{ seg.text }}</span>
              </template>
              <template v-else>
                <span class="mark-ok">{{ s.original }}</span>
              </template>
            </div>
            <div v-if="s.errors && s.errors.length" class="error-list">
              <div v-for="(err, ei) in s.errors" :key="ei" class="error-item"
                :class="err.type === 'error' ? 'error-item-red' : 'error-item-blue'">
                <span class="error-badge" :class="err.type === 'error' ? 'badge-red' : 'badge-blue'">
                  {{ err.type === 'error' ? '错误' : '建议' }}
                </span>
                <span class="error-original">{{ err.text }}</span>
                <span style="color:#9CA3AF;margin:0 4px">→</span>
                <span class="error-correction">{{ err.correction }}</span>
                <div class="error-explain">{{ err.explanation }}</div>
              </div>
            </div>
          </div>
          <!-- 图例 -->
          <div class="legend">
            <span class="mark-error">红色</span> 扣分错误 &nbsp;&nbsp;
            <span class="mark-suggestion">蓝色</span> 建议优化
          </div>
        </div>

        <!-- 修改版 -->
        <div class="card">
          <div class="card-title">✏️ 修改版</div>
          <div class="revised-text">{{ record.result.revised }}</div>
        </div>

        <!-- 整体建议 -->
        <div class="card">
          <div class="card-title">💡 整体建议</div>
          <div v-for="(line, i) in (record.result.suggestions || '').split('\n').filter(l => l.trim())" :key="i"
            class="suggestion-line">{{ line }}</div>
        </div>

        <!-- 范文 -->
        <div class="card">
          <div class="card-title">🏆 参考范文</div>
          <div class="model-essay-text">{{ record.result.model_essay }}</div>
        </div>
      </template>

      <!-- ── 翻译题：逐题渲染 ── -->
      <template v-else-if="isItems">
        <div v-for="item in record.result" :key="item.number" class="item-card">
          <div class="item-header">
            <span class="item-num">第 {{ item.number }} 题</span>
            <el-tag :type="item.is_correct ? 'success' : 'danger'" size="small">
              {{ item.is_correct ? '✓ 正确' : '✗ 有误' }}
            </el-tag>
          </div>
          <div class="row-label">题目</div>
          <div class="row-content original">{{ item.original }}</div>
          <div class="row-label">你的回答</div>
          <div class="row-content student" :class="{ wrong: !item.is_correct }">{{ item.student_answer }}</div>
          <template v-if="!item.is_correct">
            <div class="row-label">批改意见</div>
            <div class="row-content feedback">
              <div v-for="(line, i) in item.feedback.split('\n').filter(l => l.trim())" :key="i"
                :style="i > 0 ? 'margin-top:6px' : ''">{{ line }}</div>
            </div>
            <div class="row-label">参考答案</div>
            <div class="row-content corrected">{{ item.corrected }}</div>
          </template>
          <template v-else>
            <div class="row-content feedback correct-tip">
              <div v-for="(line, i) in item.feedback.split('\n').filter(l => l.trim())" :key="i"
                :style="i > 0 ? 'margin-top:6px' : ''">{{ line }}</div>
            </div>
          </template>
          <template v-if="item.key_point">
            <div class="row-label">考点</div>
            <div class="row-content key-point">💡 {{ item.key_point }}</div>
          </template>
        </div>
      </template>

      <!-- ── 通用题型：Markdown 渲染 ── -->
      <template v-else>
        <div class="card" v-if="record.result?.feedback">
          <div class="markdown-body" v-html="renderMarkdown(record.result.feedback)"></div>
        </div>
        <div class="card" v-else-if="record.result?.hint">
          <div class="card-title">AI 批改意见</div>
          <p class="feedback-text">{{ record.result.hint }}</p>
        </div>
        <!-- 解题思路（懒加载） -->
        <div class="card">
          <div class="card-title">解题思路</div>
          <div v-if="thinking">
            <div v-if="thinking.steps?.length">
              <div v-for="(step, i) in thinking.steps" :key="i" style="margin-bottom:12px">
                <div style="font-size:13px;font-weight:700;color:#3B82F6;margin-bottom:4px">{{ step.title }}</div>
                <p class="feedback-text">{{ step.content }}</p>
              </div>
            </div>
            <p v-if="thinking.encouragement" class="feedback-text" style="color:#10B981;margin-top:8px">
              💪 {{ thinking.encouragement }}
            </p>
          </div>
          <div v-else>
            <p style="font-size:13px;color:#9CA3AF;margin-bottom:12px">AI 会引导你思考，但不会直接给出答案</p>
            <el-button @click="loadThinking" :loading="thinkingLoading" size="small">
              查看解题思路
            </el-button>
          </div>
        </div>
      </template>

      <!-- 操作 -->
      <div v-if="!fromMistakes" style="padding:16px;display:flex;gap:12px">
        <el-button v-if="!record.is_correct && !inMistakes" @click="addToMistakes" style="flex:1">
          加入错题集
        </el-button>
        <el-tag v-if="inMistakes" type="warning">已加入错题集</el-tag>
        <el-button type="primary" @click="$router.push('/subject/' + record.subject)" style="flex:1">
          继续练习
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { recordApi, mistakeApi } from '@/api/index'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const route = useRoute()
const recordId = route.params.recordId
const fromMistakes = route.query.from === 'mistakes'

const loading = ref(true)
const record = ref(null)
const thinkingLoading = ref(false)
const thinking = ref(null)
const inMistakes = ref(false)

const isItems = computed(() => Array.isArray(record.value?.result))
const isEssay = computed(() => record.value?.output_schema === 'essay')

function renderMarkdown(text) {
  return marked.parse(text || '')
}

const imageList = computed(() => {
  const url = record.value?.image_url
  if (!url) return []
  try {
    const arr = JSON.parse(url)
    return Array.isArray(arr) ? arr : [url]
  } catch {
    return [url]
  }
})

// 将原句和 errors 合并成带标记的文字段
function buildSegments(original, errors) {
  if (!errors || !errors.length) return [{ type: 'plain', text: original }]
  const segments = []
  let pos = 0
  // 按出现顺序在原文中定位每个 error.text
  const sorted = [...errors]
    .map(e => ({ ...e, idx: original.indexOf(e.text, pos) }))
    .filter(e => e.idx >= 0)
    .sort((a, b) => a.idx - b.idx)

  for (const e of sorted) {
    if (e.idx > pos) segments.push({ type: 'plain', text: original.slice(pos, e.idx) })
    segments.push({ type: e.type, text: e.text })
    pos = e.idx + e.text.length
  }
  if (pos < original.length) segments.push({ type: 'plain', text: original.slice(pos) })
  return segments.length ? segments : [{ type: 'plain', text: original }]
}

async function loadRecord() {
  loading.value = true
  try {
    const cached = sessionStorage.getItem('last_record')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (parsed.id === recordId) {
        record.value = parsed
        return
      }
    }
    record.value = await recordApi.get(recordId)
  } catch {
    ElMessage.warning('无法加载结果，请重新提交')
  } finally {
    loading.value = false
  }
}

async function loadThinking() {
  thinkingLoading.value = true
  try {
    const data = await recordApi.getThinking(recordId)
    thinking.value = data.thinking
  } catch (e) {
    ElMessage.error(e?.detail || '加载思路失败')
  } finally {
    thinkingLoading.value = false
  }
}

async function addToMistakes() {
  try {
    await mistakeApi.add(recordId)
    inMistakes.value = true
    ElMessage.success('已加入错题集')
  } catch (e) {
    ElMessage.error(e?.detail || '操作失败')
  }
}

onMounted(loadRecord)
</script>

<style scoped>
.page { background:#F8F9FB; min-height:100vh; padding-bottom:24px; }
.header {
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 16px; background:white; border-bottom:1px solid #F3F4F6;
}
.header-title { font-size:16px; font-weight:600; }
.result-banner {
  margin:0 16px 16px; border-radius:16px; padding:16px 20px;
  display:flex; align-items:center;
}
.result-banner.correct { background:#D1FAE5; }
.result-banner.wrong { background:#FEE2E2; }

/* ── 作文 ── */
.essay-score-card { }
.score-circle {
  width:64px; height:64px; border-radius:50%;
  background:linear-gradient(135deg,#4A7CFF,#7C3AED);
  display:flex; align-items:baseline; justify-content:center;
  flex-shrink:0; padding-top:14px;
}
.score-num { font-size:26px; font-weight:800; color:white; line-height:1; }
.score-total { font-size:12px; color:rgba(255,255,255,0.8); margin-left:1px; }
.essay-overall {
  margin-top:12px; font-size:13px; line-height:1.7; color:#374151;
  background:#F8F9FB; border-radius:8px; padding:10px 12px;
}

.sentence-block { margin-bottom:14px; border-bottom:1px solid #F3F4F6; padding-bottom:14px; }
.sentence-block:last-child { border-bottom:none; padding-bottom:0; margin-bottom:0; }
.sentence-text { font-size:14px; line-height:1.8; color:#1F2937; margin-bottom:6px; }

.mark-error {
  background:#FEE2E2; color:#B91C1C;
  border-radius:3px; padding:1px 2px;
}
.mark-suggestion {
  background:#DBEAFE; color:#1D4ED8;
  border-radius:3px; padding:1px 2px;
}
.mark-ok { color:#374151; }

.error-list { display:flex; flex-direction:column; gap:6px; }
.error-item {
  font-size:12px; border-radius:8px; padding:6px 10px;
}
.error-item-red { background:#FFF5F5; border-left:3px solid #EF4444; }
.error-item-blue { background:#EFF6FF; border-left:3px solid #3B82F6; }
.error-badge {
  display:inline-block; font-size:10px; font-weight:700;
  border-radius:4px; padding:1px 5px; margin-right:6px;
}
.badge-red { background:#FEE2E2; color:#B91C1C; }
.badge-blue { background:#DBEAFE; color:#1D4ED8; }
.error-original { color:#6B7280; text-decoration:line-through; }
.error-correction { color:#059669; font-weight:600; }
.error-explain { color:#6B7280; margin-top:3px; line-height:1.5; }

.legend {
  margin-top:12px; font-size:12px; color:#9CA3AF;
  border-top:1px solid #F3F4F6; padding-top:10px;
}

.revised-text {
  font-size:14px; line-height:1.9; color:#1F2937;
  background:#F0FDF4; border-radius:10px; padding:12px 14px;
  white-space:pre-wrap;
}
.suggestion-line {
  font-size:13px; line-height:1.7; color:#374151;
  padding:6px 0; border-bottom:1px dashed #F3F4F6;
}
.suggestion-line:last-child { border-bottom:none; }
.model-essay-text {
  font-size:14px; line-height:1.9; color:#1F2937;
  background:#FFFBEB; border-radius:10px; padding:12px 14px;
  white-space:pre-wrap;
}

/* 翻译题逐题卡片 */
.item-card {
  background:white; margin:0 16px 12px; border-radius:16px; padding:16px;
  box-shadow:0 1px 4px rgba(0,0,0,0.05);
}
.item-header {
  display:flex; justify-content:space-between; align-items:center;
  margin-bottom:12px;
}
.item-num { font-size:15px; font-weight:700; color:#1F2937; }
.row-label {
  font-size:11px; font-weight:600; color:#9CA3AF; letter-spacing:0.5px;
  text-transform:uppercase; margin-bottom:4px; margin-top:10px;
}
.row-content { font-size:14px; line-height:1.6; padding:8px 10px; border-radius:8px; }
.row-content.original { background:#F3F4F6; color:#374151; }
.row-content.student { background:#EFF6FF; color:#1D4ED8; }
.row-content.student.wrong { background:#FEF2F2; color:#B91C1C; }
.row-content.feedback { background:#FFFBEB; color:#92400E; font-size:13px; }
.row-content.corrected { background:#ECFDF5; color:#065F46; font-weight:500; }
.row-content.correct-tip { background:#F0FDF4; color:#166534; font-size:13px; margin-top:6px; }
.row-content.key-point { background:#FFF7ED; color:#9A3412; font-size:13px; }

.score-dim {
  font-size:11px; font-weight:600; color:#6B7280;
  background:#F3F4F6; border-radius:4px; padding:2px 6px;
}
/* markdown 报告 */
.markdown-body { font-size:14px; line-height:1.8; color:#1F2937; }
.markdown-body h1 { font-size:17px; font-weight:700; margin:16px 0 8px; color:#111827; }
.markdown-body h2 { font-size:15px; font-weight:700; margin:14px 0 6px; color:#1F2937; border-bottom:1px solid #F3F4F6; padding-bottom:4px; }
.markdown-body h3 { font-size:14px; font-weight:600; margin:10px 0 4px; color:#374151; }
.markdown-body p { margin:0 0 8px; }
.markdown-body ul, .markdown-body ol { padding-left:20px; margin:4px 0 8px; }
.markdown-body li { margin-bottom:4px; }
.markdown-body code { background:#F3F4F6; border-radius:4px; padding:1px 5px; font-size:13px; font-family:monospace; }
.markdown-body blockquote { border-left:3px solid #D1D5DB; margin:8px 0; padding:6px 12px; color:#6B7280; background:#F9FAFB; border-radius:0 6px 6px 0; }
.markdown-body table { width:100%; border-collapse:collapse; margin:8px 0; font-size:13px; }
.markdown-body th { background:#F3F4F6; padding:6px 10px; text-align:left; font-weight:600; border:1px solid #E5E7EB; }
.markdown-body td { padding:6px 10px; border:1px solid #E5E7EB; }
.markdown-body hr { border:none; border-top:1px solid #E5E7EB; margin:12px 0; }
.markdown-body strong { font-weight:700; color:#111827; }
/* 通用卡片 */
.card {
  background:white; margin:0 16px 12px; border-radius:16px; padding:16px;
  box-shadow:0 1px 4px rgba(0,0,0,0.05);
}
.card-title { font-size:14px; font-weight:700; margin-bottom:10px; }
.card-subtitle { font-size:12px; color:#6B7280; margin:8px 0 4px; font-weight:600; }
.feedback-text { font-size:14px; line-height:1.6; color:#374151; margin:0 0 8px; }
</style>
