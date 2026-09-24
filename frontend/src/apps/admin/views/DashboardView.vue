<template>
  <div>
    <div class="page-header">
      <h2>数据概览</h2>
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:13px;color:#999">当前模型：{{ stats.active_llm }}</span>
        <el-button @click="loadStats" :loading="loading" size="small">刷新</el-button>
      </div>
    </div>

    <!-- 今日 / 本月 概览 -->
    <el-row :gutter="16" style="margin-bottom:24px">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日提交</div>
          <div class="stat-value">{{ fmtNum(stats.today?.records) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日 Token</div>
          <div class="stat-value">{{ fmtNum((stats.today?.token_input ?? 0) + (stats.today?.token_output ?? 0)) }}</div>
          <div class="stat-sub">输入 {{ fmtNum(stats.today?.token_input) }} / 输出 {{ fmtNum(stats.today?.token_output) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">本月提交</div>
          <div class="stat-value">{{ fmtNum(stats.month?.records) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">本月费用</div>
          <div class="stat-value cost">¥{{ fmtCost(stats.month?.cost_rmb) }}</div>
          <div class="stat-sub">今日 ¥{{ fmtCost(stats.today?.cost_rmb) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 本月 Token 明细 -->
    <el-row :gutter="16" style="margin-bottom:24px">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-label">本月 Token 合计</div>
          <div class="stat-value">{{ fmtNum((stats.month?.token_input ?? 0) + (stats.month?.token_output ?? 0)) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-label">本月输入 Token</div>
          <div class="stat-value">{{ fmtNum(stats.month?.token_input) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-label">本月输出 Token</div>
          <div class="stat-value">{{ fmtNum(stats.month?.token_output) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 近30天趋势 -->
    <el-card style="margin-bottom:24px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>近30天趋势</span>
          <el-radio-group v-model="trendMode" size="small">
            <el-radio-button value="submissions">提交次数</el-radio-button>
            <el-radio-button value="tokens">Token 消耗</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div v-if="dailyData.length === 0" style="text-align:center;color:#999;padding:40px">暂无数据</div>
      <div v-else>
        <div v-for="item in dailyData.slice(-14)" :key="item.date" class="daily-row">
          <span class="daily-date">{{ item.date.slice(5) }}</span>
          <el-progress
            :percentage="trendMode === 'submissions'
              ? (maxSubmissions ? Math.round((item.records / maxSubmissions) * 100) : 0)
              : (maxTokens ? Math.round((item.tokens / maxTokens) * 100) : 0)"
            :stroke-width="14"
            :format="() => trendMode === 'submissions' ? item.records : fmtNum(item.tokens)"
            style="flex:1;margin:0 16px"
          />
          <span class="daily-cost">¥{{ fmtCost(item.cost_rmb) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 用户 Token 排行 -->
    <el-card>
      <template #header>Token 消耗排行（近30天 Top 50）</template>
      <el-table :data="userStats" stripe size="small">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="username" label="账号" />
        <el-table-column prop="records" label="提交次数" align="right" width="90" />
        <el-table-column label="输入 Token" align="right" width="110">
          <template #default="{ row }">{{ fmtNum(row.token_input) }}</template>
        </el-table-column>
        <el-table-column label="输出 Token" align="right" width="110">
          <template #default="{ row }">{{ fmtNum(row.token_output) }}</template>
        </el-table-column>
        <el-table-column label="合计 Token" align="right" width="110">
          <template #default="{ row }">{{ fmtNum((row.token_input ?? 0) + (row.token_output ?? 0)) }}</template>
        </el-table-column>
        <el-table-column label="费用 (¥)" align="right" width="90">
          <template #default="{ row }">{{ fmtCost(row.cost_rmb) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api/index'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const stats = ref({})
const dailyData = ref([])
const userStats = ref([])
const trendMode = ref('submissions')

const maxSubmissions = computed(() => Math.max(...dailyData.value.map(d => d.records), 1))
const maxTokens = computed(() => Math.max(...dailyData.value.map(d => d.tokens), 1))

function fmtNum(n) {
  if (n == null) return '-'
  return n.toLocaleString()
}
function fmtCost(n) {
  if (n == null) return '-'
  return n.toFixed(4)
}

async function loadStats() {
  loading.value = true
  try {
    const [overview, daily, users] = await Promise.all([
      adminApi.getStatsOverview(),
      adminApi.getStatsDaily(30),
      adminApi.getStatsByUser(30),
    ])
    stats.value = overview
    dailyData.value = daily
    userStats.value = users
  } catch (e) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
.page-header h2 { margin:0; font-size:20px; }
.stat-card { text-align:center; }
.stat-label { font-size:12px; color:#666; margin-bottom:8px; }
.stat-value { font-size:28px; font-weight:700; color:#4A7CFF; }
.stat-value.cost { color:#10B981; }
.stat-sub { font-size:11px; color:#9CA3AF; margin-top:4px; }
.daily-row { display:flex; align-items:center; margin-bottom:8px; font-size:13px; }
.daily-date { width:50px; color:#666; flex-shrink:0; }
.daily-cost { width:70px; text-align:right; color:#999; flex-shrink:0; font-size:12px; }
</style>
