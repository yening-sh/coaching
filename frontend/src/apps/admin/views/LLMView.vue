<template>
  <div>
    <div class="page-header">
      <h2>AI 模型配置</h2>
      <el-button type="primary" @click="openCreate">+ 新增配置</el-button>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom:16px"
      description="同一时间只有一个配置处于激活状态。激活新配置后，所有后续 AI 请求立即切换，无需重启服务。" />

    <el-card>
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column label="提供商" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="warning">{{ row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_id" label="模型 ID" min-width="80" />
        <el-table-column label="Key" width="110">
          <template #default="{ row }">
            <span style="font-size:12px;color:#9CA3AF">{{ row.api_key_hint }}</span>
          </template>
        </el-table-column>
        <el-table-column label="价格 ($/M)" width="160">
          <template #default="{ row }">
            <span style="font-size:12px">
              {{ row.price_currency || 'CNY' }} {{ row.price_input }} / {{ row.price_output }} per M
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="80" />
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" type="success" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="warning" @click="test(row)" :loading="testingId === row.id">测试</el-button>
              <el-button v-if="!row.is_active" size="small" type="primary" @click="activate(row)">激活</el-button>
              <el-button v-else size="small" disabled>已激活</el-button>
              <el-button size="small" type="danger" :disabled="row.is_active" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog" :title="editingId ? '编辑配置' : '新增 AI 模型配置'" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="配置名称">
          <el-input v-model="form.name" placeholder="如：GPT-4o Mini" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.provider">
            <el-option value="anthropic" label="Anthropic" />
            <el-option value="openai" label="OpenAI 兼容" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型 ID">
          <el-input v-model="form.model_id" placeholder="如：gpt-4o-mini" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password
            :placeholder="editingId ? '留空则不修改' : ''" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="form.api_base_url" placeholder="如：https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="价格货币">
          <el-select v-model="form.price_currency" style="width:120px">
            <el-option value="CNY" label="CNY (人民币)" />
            <el-option value="USD" label="USD (美元)" />
          </el-select>
        </el-form-item>
        <el-form-item label="输入价格 /M">
          <el-input-number v-model="form.price_input" :precision="4" :step="0.1" :min="0" />
        </el-form-item>
        <el-form-item label="输出价格 /M">
          <el-input-number v-model="form.price_output" :precision="4" :step="0.1" :min="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="立即激活">
          <el-switch v-model="form.activate_now" />
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
import { adminApi } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const configs = ref([])
const dialog = ref(false)
const form = ref({})
const editingId = ref(null)
const testingId = ref(null)

async function loadConfigs() {
  loading.value = true
  try { configs.value = await adminApi.getLLMConfigs() }
  catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  form.value = { provider: 'openai', price_currency: 'CNY', price_input: 0, price_output: 0, activate_now: false }
  dialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    provider: row.provider,
    model_id: row.model_id,
    api_key: '',
    api_base_url: row.api_base_url || '',
    price_currency: row.price_currency || 'CNY',
    price_input: row.price_input,
    price_output: row.price_output,
    note: row.note || '',
  }
  dialog.value = true
}

async function save() {
  if (!form.value.name || !form.value.model_id) {
    return ElMessage.warning('请填写名称和模型 ID')
  }
  if (!editingId.value && !form.value.api_key) {
    return ElMessage.warning('请填写 API Key')
  }
  saving.value = true
  try {
    if (editingId.value) {
      const payload = { ...form.value }
      if (!payload.api_key) delete payload.api_key
      await adminApi.updateLLMConfig(editingId.value, payload)
    } else {
      const config = await adminApi.createLLMConfig(form.value)
      if (form.value.activate_now) {
        await adminApi.activateLLMConfig(config.id)
      }
    }
    ElMessage.success('保存成功')
    dialog.value = false
    loadConfigs()
  } catch (e) {
    ElMessage.error(e?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function test(row) {
  testingId.value = row.id
  try {
    const res = await adminApi.testLLMConfig(row.id)
    ElMessageBox.alert(
      `<div style="font-size:14px">
        <p>✅ <strong>连接成功</strong></p>
        <p style="color:#6B7280;margin-top:8px">模型回复：${res.reply}</p>
      </div>`,
      '测试结果',
      { dangerouslyUseHTMLString: true, confirmButtonText: '确定' }
    )
  } catch (e) {
    ElMessageBox.alert(
      `<div style="font-size:14px">
        <p>❌ <strong>连接失败</strong></p>
        <p style="color:#EF4444;margin-top:8px;word-break:break-all">${e?.detail || e?.message || '未知错误'}</p>
      </div>`,
      '测试结果',
      { dangerouslyUseHTMLString: true, confirmButtonText: '确定', type: 'error' }
    )
  } finally {
    testingId.value = null
  }
}

async function activate(row) {
  await ElMessageBox.confirm(`确认激活「${row.name}」？当前激活配置将被停用。`, '确认激活', { type: 'warning' })
  await adminApi.activateLLMConfig(row.id)
  ElMessage.success('已激活')
  loadConfigs()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '确认删除', { type: 'danger' })
  await adminApi.deleteLLMConfig(row.id)
  ElMessage.success('已删除')
  loadConfigs()
}

onMounted(loadConfigs)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }
.action-btns { display:flex; gap:6px; align-items:center; }
.action-btns .el-button { width:64px; margin:0; }
</style>
