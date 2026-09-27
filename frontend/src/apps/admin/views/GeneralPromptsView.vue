<template>
  <div>
    <div class="page-header">
      <h2>通用模版</h2>
      <el-button type="primary" @click="openCreate">+ 新增模版</el-button>
    </div>

    <el-card>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="年级" width="80">
          <template #default="{ row }">
            <el-tag size="small" type="warning">{{ row.grade_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="科目" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.subject_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模版预览" min-width="200">
          <template #default="{ row }">
            <span class="prompt-preview">{{ row.prompt_template.slice(0, 60) }}…</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="140">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :type="row.is_active ? 'warning' : 'success'"
                @click="toggleActive(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑通用模版' : '新增通用模版'" width="700px">
      <el-form :model="form" label-width="80px">
        <template v-if="!editingId">
          <el-form-item label="年级">
            <el-select v-model="form.grade_level" placeholder="选择年级">
              <el-option label="高中" value="senior" />
              <el-option label="初中" value="junior" />
              <el-option label="全部" value="all" />
            </el-select>
          </el-form-item>
          <el-form-item label="科目">
            <el-select v-model="form.subject" placeholder="选择科目">
              <el-option label="英语" value="english" />
              <el-option label="数学" value="math" />
              <el-option label="语文" value="chinese" />
              <el-option label="物理" value="physics" />
              <el-option label="化学" value="chemistry" />
              <el-option label="生物" value="biology" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="Prompt">
          <el-input v-model="form.prompt_template" type="textarea" :rows="20"
            placeholder="输入通用 prompt 模版内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api/index'

const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const form = ref({ subject: '', grade_level: '', prompt_template: '' })

async function load() {
  loading.value = true
  try {
    items.value = await adminApi.getGeneralPrompts()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = { subject: 'english', grade_level: 'senior', prompt_template: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = { subject: row.subject, grade_level: row.grade_level, prompt_template: row.prompt_template }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.prompt_template.trim()) {
    ElMessage.warning('请填写 Prompt 内容')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await adminApi.updateGeneralPrompt(editingId.value, { prompt_template: form.value.prompt_template })
    } else {
      await adminApi.createGeneralPrompt(form.value)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row) {
  await adminApi.updateGeneralPrompt(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已停用' : '已启用')
  load()
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const bj = new Date(d.getTime() + 8 * 3600 * 1000)
  return bj.toISOString().replace('T', ' ').slice(0, 16)
}

onMounted(load)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px }
.page-header h2 { margin:0; font-size:20px }
.action-btns { display:flex; gap:8px }
.prompt-preview { color:#666; font-size:12px }
</style>
