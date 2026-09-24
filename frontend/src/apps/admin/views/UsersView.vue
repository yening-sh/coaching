<template>
  <div>
    <div class="page-header">
      <h2>账号管理</h2>
      <el-button type="primary" @click="openCreate">+ 新建账号</el-button>
    </div>

    <el-card>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="角色" width="80">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '学生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="年级" width="90">
          <template #default="{ row }">{{ gradeLabel(row.grade_level) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订阅学科" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="sub in (row.subscriptions || [])" :key="sub.id"
              size="small" style="margin:2px">
              {{ subjectLabel(sub.subject) }}
              <span style="color:#999;font-size:10px"> 至{{ sub.end_date }}</span>
            </el-tag>
            <span v-if="!row.subscriptions?.length" style="color:#ccc">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" @click="toggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
            <el-button text size="small" type="primary" @click="openSubscription(row)">订阅</el-button>
            <el-button text size="small" type="success" @click="openUsage(row)">用量</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑账号弹窗 -->
    <el-dialog v-model="userDialog" :title="editingUser ? '编辑账号' : '新建账号'" width="420px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="账号">
          <el-input v-model="userForm.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password"
            :placeholder="editingUser ? '留空不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role">
            <el-option value="student" label="学生" />
            <el-option value="admin" label="管理员" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级" v-if="userForm.role === 'student'">
          <el-select v-model="userForm.grade_level">
            <el-option value="junior" label="初中" />
            <el-option value="senior" label="高中" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 订阅管理弹窗 -->
    <el-dialog v-model="subDialog" :title="`订阅管理 — ${subUser?.name}`" width="480px">
      <div style="margin-bottom:16px">
        <div v-for="sub in (subUser?.subscriptions || [])" :key="sub.id"
          style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <el-tag>{{ subjectLabel(sub.subject) }}</el-tag>
          <span style="font-size:12px;color:#666">{{ sub.start_date }} ~ {{ sub.end_date }}</span>
          <el-button text type="danger" size="small" @click="deleteSub(sub.id)">删除</el-button>
        </div>
        <div v-if="!subUser?.subscriptions?.length" style="color:#ccc;margin-bottom:8px">暂无订阅</div>
      </div>
      <el-divider>新增订阅</el-divider>
      <el-form :model="subForm" label-width="70px" size="small">
        <el-form-item label="学科">
          <el-select v-model="subForm.subject">
            <el-option v-for="s in subjects" :key="s.value" :value="s.value" :label="s.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期日">
          <el-date-picker v-model="subForm.end_date" type="date" value-format="YYYY-MM-DD"
            :disabled-date="d => d < new Date()" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="subForm.note" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subDialog = false">关闭</el-button>
        <el-button type="primary" @click="addSub" :loading="saving">添加订阅</el-button>
      </template>
    </el-dialog>
    <!-- 用量明细弹窗 -->
    <el-dialog v-model="usageDialog" :title="`用量明细 — ${usageUser?.name}`" width="720px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div style="font-size:13px;color:#666">
          共 <strong>{{ usageTotal }}</strong> 条记录 &nbsp;|&nbsp;
          累计输入 <strong>{{ fmtNum(usageSummary.token_input) }}</strong> &nbsp;
          输出 <strong>{{ fmtNum(usageSummary.token_output) }}</strong> token &nbsp;|&nbsp;
          费用 <strong>¥{{ usageSummary.cost_cny }}</strong> / <strong>${{ usageSummary.cost_usd }}</strong>
        </div>
        <el-pagination small :current-page="usagePage" :page-size="20" :total="usageTotal"
          layout="prev, pager, next" @current-change="loadUsage" />
      </div>
      <el-table :data="usageRecords" v-loading="usageLoading" stripe size="small">
        <el-table-column prop="created_at" label="时间" width="140" />
        <el-table-column prop="subject" label="学科" width="70" />
        <el-table-column prop="model" label="模型" min-width="120" show-overflow-tooltip />
        <el-table-column label="输入 Token" align="right" width="100">
          <template #default="{ row }">{{ fmtNum(row.token_input) }}</template>
        </el-table-column>
        <el-table-column label="输出 Token" align="right" width="100">
          <template #default="{ row }">{{ fmtNum(row.token_output) }}</template>
        </el-table-column>
        <el-table-column label="费用" align="right" width="130">
          <template #default="{ row }">
            <span>¥{{ row.cost_cny }}</span>
            <span style="color:#9CA3AF;font-size:11px;margin-left:4px">${{ row.cost_usd }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

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
function gradeLabel(v) { return v === 'junior' ? '初中' : v === 'senior' ? '高中' : '-' }

const loading = ref(false)
const saving = ref(false)
const users = ref([])

const userDialog = ref(false)
const editingUser = ref(null)
const userForm = ref({})

const subDialog = ref(false)
const subUser = ref(null)
const subForm = ref({})

const usageDialog = ref(false)
const usageUser = ref(null)
const usageLoading = ref(false)
const usageRecords = ref([])
const usageTotal = ref(0)
const usagePage = ref(1)
const usageSummary = ref({ token_input: 0, token_output: 0, cost_cny: 0, cost_usd: 0 })

function fmtNum(n) { return (n || 0).toLocaleString() }

async function openUsage(row) {
  usageUser.value = row
  usagePage.value = 1
  usageDialog.value = true
  await loadUsage(1)
}

async function loadUsage(page) {
  usagePage.value = page
  usageLoading.value = true
  try {
    const data = await adminApi.getUserRecords(usageUser.value.id, { page, limit: 20 })
    usageRecords.value = data.items
    usageTotal.value = data.total
    // 计算汇总
    const tin = data.items.reduce((s, r) => s + (r.token_input || 0), 0)
    const tout = data.items.reduce((s, r) => s + (r.token_output || 0), 0)
    const cny = data.items.reduce((s, r) => s + (r.cost_cny || 0), 0)
    const usd = data.items.reduce((s, r) => s + (r.cost_usd || 0), 0)
    usageSummary.value = { token_input: tin, token_output: tout, cost_cny: cny.toFixed(4), cost_usd: usd.toFixed(4) }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    usageLoading.value = false
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const data = await adminApi.getUsers()
    users.value = data.items ?? data
  }
  catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editingUser.value = null
  userForm.value = { role: 'student', grade_level: 'junior' }
  userDialog.value = true
}

function openEdit(row) {
  editingUser.value = row
  userForm.value = { name: row.name, role: row.role, grade_level: row.grade_level, password: '' }
  userDialog.value = true
}

async function saveUser() {
  saving.value = true
  try {
    if (editingUser.value) {
      const payload = { name: userForm.value.name, grade_level: userForm.value.grade_level }
      if (userForm.value.password) payload.password = userForm.value.password
      await adminApi.updateUser(editingUser.value.id, payload)
    } else {
      await adminApi.createUser(userForm.value)
    }
    ElMessage.success('保存成功')
    userDialog.value = false
    loadUsers()
  } catch (e) {
    ElMessage.error(e?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row) {
  await adminApi.updateUser(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已停用' : '已启用')
  loadUsers()
}

function openSubscription(row) {
  subUser.value = row
  subForm.value = { subject: 'math', end_date: '', note: '' }
  subDialog.value = true
}

async function addSub() {
  if (!subForm.value.end_date) return ElMessage.warning('请选择到期日')
  saving.value = true
  try {
    await adminApi.createSubscription({
      student_id: subUser.value.id,
      subject: subForm.value.subject,
      end_date: subForm.value.end_date,
      note: subForm.value.note,
    })
    ElMessage.success('订阅添加成功')
    subForm.value = { subject: 'math', end_date: '', note: '' }
    await loadUsers()
    const updated = users.value.find(u => u.id === subUser.value.id)
    if (updated) subUser.value = updated
  } catch (e) {
    ElMessage.error(e?.detail || '添加失败')
  } finally {
    saving.value = false
  }
}

async function deleteSub(subId) {
  await ElMessageBox.confirm('确认删除此订阅？', '提示', { type: 'warning' })
  await adminApi.deleteSubscription(subId)
  ElMessage.success('已删除')
  await loadUsers()
  const updated = users.value.find(u => u.id === subUser.value.id)
  if (updated) subUser.value = updated
}

onMounted(loadUsers)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }
</style>
