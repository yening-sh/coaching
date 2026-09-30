<template>
  <div>
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button text @click="$router.push('/mgmt/exercise-types')">← 返回</el-button>
        <h2 v-if="exerciseType">{{ exerciseType.name }}</h2>
        <el-tag v-if="exerciseType" size="small" type="warning">{{ SUBJECT_NAMES[exerciseType.subject] || exerciseType.subject }}</el-tag>
        <el-tag v-if="exerciseType" size="small">{{ exerciseType.output_schema }}</el-tag>
      </div>
      <el-button type="primary" @click="openCreate">+ 新增版本</el-button>
    </div>

    <!-- 三类 prompt tab -->
    <el-tabs v-model="activeTab" class="prompt-tabs">
      <el-tab-pane
        v-for="pt in PROMPT_TYPES"
        :key="pt.value"
        :label="pt.label"
        :name="pt.value"
      >
        <el-card v-loading="loading">
          <el-table :data="versionsForTab(pt.value)" stripe>
            <el-table-column label="激活" width="70">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '激活' : '未激活' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="版本名称" width="160" prop="version_name" />
            <el-table-column label="创建时间" min-width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-button size="small" type="success" @click="openEdit(row)">编辑</el-button>
                  <el-button size="small" type="primary" v-if="!row.is_active" @click="activate(row)">激活</el-button>
                  <el-button size="small" disabled v-else>已激活</el-button>
                  <el-button size="small" type="danger" :disabled="row.is_active" @click="remove(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="versionsForTab(pt.value).length === 0" class="empty-hint">
            暂无版本，点击右上角「+ 新增版本」添加
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog" :title="editingId ? '编辑版本' : '新增版本'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="类型">
          <el-select v-model="form.prompt_type" :disabled="!!editingId">
            <el-option v-for="pt in PROMPT_TYPES" :key="pt.value" :label="pt.label" :value="pt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本名称">
          <el-input v-model="form.version_name" placeholder="如：v1 初版、v2 更详细" />
        </el-form-item>
        <el-form-item label="Prompt">
          <el-input
            v-model="form.prompt_template"
            type="textarea"
            :rows="20"
            placeholder="Prompt 模板，可使用 {grade} {subject} 变量"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminApi } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

const SUBJECT_NAMES = { math:'数学', chinese:'语文', english:'英语', physics:'物理', chemistry:'化学', biology:'生物' }
const PROMPT_TYPES = [
  { value: 'ocr',      label: 'OCR识别 Prompt' },
  { value: 'grading',  label: '批改 Prompt' },
  { value: 'coaching', label: '辅导 Prompt' },
]

const route = useRoute()
const typeId = route.params.typeId

const loading = ref(false)
const saving = ref(false)
const exerciseType = ref(null)
const versions = ref([])
const dialog = ref(false)
const editingId = ref(null)
const activeTab = ref('ocr')
const form = ref({ prompt_type: 'ocr', version_name: '', prompt_template: '' })

function versionsForTab(type) {
  return versions.value.filter(v => v.prompt_type === type)
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const bj = new Date(d.getTime() + 8 * 3600 * 1000)
  return bj.toISOString().replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const res = await adminApi.getPromptVersions(typeId)
    exerciseType.value = res.exercise_type
    versions.value = res.prompts
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = { prompt_type: activeTab.value, version_name: '', prompt_template: '' }
  dialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = { prompt_type: row.prompt_type, version_name: row.version_name, prompt_template: row.prompt_template }
  dialog.value = true
}

async function save() {
  if (!form.value.version_name) return ElMessage.warning('请填写版本名称')
  if (!form.value.prompt_template) return ElMessage.warning('请填写 Prompt')
  saving.value = true
  try {
    if (editingId.value) {
      await adminApi.updatePromptVersion(typeId, editingId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await adminApi.createPromptVersion(typeId, form.value)
      ElMessage.success('已创建')
    }
    dialog.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function activate(row) {
  try {
    await adminApi.activatePromptVersion(typeId, row.id)
    ElMessage.success(`已激活「${row.version_name}」`)
    load()
  } catch (e) {
    ElMessage.error(e?.detail || '激活失败')
  }
}

async function remove(row) {
  if (row.is_active) {
    return ElMessage.warning('请先切换到其他版本，再删除此版本')
  }
  await ElMessageBox.confirm(`确认删除版本「${row.version_name}」？`, '确认删除', { type: 'warning' })
  try {
    await adminApi.deletePromptVersion(typeId, row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e?.detail || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }
.action-btns { display:flex; gap:6px; align-items:center; }
.action-btns .el-button { width:64px; margin:0; }
.prompt-tabs { margin-top:0; }
.empty-hint { text-align:center; color:#9CA3AF; padding:32px 0; font-size:14px; }
</style>
