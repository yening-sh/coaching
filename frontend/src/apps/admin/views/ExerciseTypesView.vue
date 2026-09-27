<template>
  <div>
    <div class="page-header">
      <h2>题型管理</h2>
      <el-button type="primary" @click="openCreate">+ 新增题型</el-button>
    </div>

    <el-card>
      <el-table :data="types" v-loading="loading" stripe>
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="科目" width="80">
          <template #default="{ row }">
            <el-tag size="small" type="warning">{{ SUBJECT_NAMES[row.subject] || row.subject }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="题型名称" prop="name" min-width="140">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/mgmt/exercise-types/${row.id}`)">
              {{ row.name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="输出格式" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.output_schema === 'items' ? 'primary' : row.output_schema === 'essay' ? 'success' : ''">
              {{ row.output_schema }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" type="primary"
                @click="$router.push(`/mgmt/exercise-types/${row.id}`)">Prompt 版本</el-button>
              <el-button size="small" :type="row.is_active ? 'warning' : 'success'"
                @click="toggleActive(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增题型弹窗 -->
    <el-dialog v-model="dialog" title="新增题型" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="科目">
          <el-select v-model="form.subject" style="width:140px">
            <el-option v-for="(name, key) in SUBJECT_NAMES" :key="key" :value="key" :label="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型名称">
          <el-input v-model="form.name" placeholder="如：翻译题、解答题" />
        </el-form-item>
        <el-form-item label="输出格式">
          <el-select v-model="form.output_schema" style="width:160px">
            <el-option value="math" label="math（数学解答题）" />
            <el-option value="translation" label="translation（英语翻译）" />
            <el-option value="essay" label="essay（作文）" />
            <el-option value="summary" label="summary（概要写作）" />
            <el-option value="grammar" label="grammar（语法填空）" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input v-model="form.sort_order" style="width:80px" placeholder="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

const SUBJECT_NAMES = { math:'数学', chinese:'语文', english:'英语', physics:'物理', chemistry:'化学', biology:'生物' }
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const types = ref([])
const dialog = ref(false)
const form = ref({})

async function loadTypes() {
  loading.value = true
  try { types.value = await adminApi.getExerciseTypes() }
  catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  form.value = { subject: 'english', name: '', output_schema: 'math', sort_order: '0' }
  dialog.value = true
}

async function save() {
  if (!form.value.name) return ElMessage.warning('请填写题型名称')
  saving.value = true
  try {
    // 新建时 prompt_template 先给空字符串占位，后续在详情页管理
    const res = await adminApi.createExerciseType({ ...form.value, prompt_template: '待配置' })
    ElMessage.success('题型已创建，请进入详情页添加 Prompt 版本')
    dialog.value = false
    loadTypes()
    router.push(`/mgmt/exercise-types/${res.id}`)
  } catch (e) {
    ElMessage.error(e?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row) {
  await adminApi.updateExerciseType(row.id, { is_active: !row.is_active })
  loadTypes()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '确认删除', { type: 'warning' })
  await adminApi.deleteExerciseType(row.id)
  ElMessage.success('已删除')
  loadTypes()
}

onMounted(loadTypes)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }
.action-btns { display:flex; gap:6px; align-items:center; }
.action-btns .el-button { margin:0; }
</style>
