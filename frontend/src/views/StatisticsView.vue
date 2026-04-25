<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <div>
        <h2>报销统计</h2>
        <p>支持个人报销统计与部门报销统计可视化分析。</p>
      </div>
      <el-segmented v-model="mode" :options="modeOptions" />
    </div>

    <el-card class="mt panel">
      <template #header>{{ mode === 'personal' ? '个人报销统计' : '部门报销统计' }}</template>
      <div class="chart-grid">
        <div ref="barRef" class="chart-box"></div>
        <div ref="pieRef" class="chart-box"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import TopNav from './TopNav.vue'
import request from '../api/request'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const mode = ref('personal')
const modeOptions = [
  { label: '个人报销统计', value: 'personal' },
  { label: '部门报销统计', value: 'department' },
]

const rawStats = ref({
  personal: { labels: [], values: [] },
  department: { labels: [], values: [] },
})

const barRef = ref(null)
const pieRef = ref(null)
let barChart = null
let pieChart = null

const getCurrentSeries = () => rawStats.value[mode.value] || { labels: [], values: [] }

const renderCharts = () => {
  const cur = getCurrentSeries()
  if (!barRef.value || !pieRef.value) return

  if (!barChart) barChart = echarts.init(barRef.value)
  if (!pieChart) pieChart = echarts.init(pieRef.value)

  barChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 40, bottom: 70 },
    xAxis: {
      type: 'category',
      data: cur.labels,
      axisLabel: { rotate: 30, color: '#475569' },
    },
    yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
    series: [
      {
        type: 'bar',
        data: cur.values,
        barWidth: 24,
        itemStyle: { color: '#2d7be8', borderRadius: [6, 6, 0, 0] },
      },
    ],
  })

  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: mode.value === 'personal' ? '个人报销' : '部门报销',
        type: 'pie',
        radius: ['35%', '68%'],
        center: ['50%', '45%'],
        data: cur.labels.map((name, idx) => ({ name, value: cur.values[idx] || 0 })),
      },
    ],
  })
}

const loadStats = async () => {
  try {
    const { data } = await request.get('/stats/reimbursement/', { params: { employee_id: user.id } })
    rawStats.value = data
    await nextTick()
    renderCharts()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '统计数据加载失败，请稍后重试')
  }
}

watch(mode, () => {
  renderCharts()
})

onMounted(() => {
  loadStats()
  window.addEventListener('resize', renderCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderCharts)
  if (barChart) barChart.dispose()
  if (pieChart) pieChart.dispose()
})
</script>

<style scoped>
.shell {
  padding: 24px;
  margin-left: 220px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header h2 {
  margin: 0;
  color: #0f172a;
  font-size: 34px;
}

.header p {
  margin: 8px 0 0;
  color: #64748b;
}

.mt { margin-top: 16px; }

.panel {
  border-radius: 14px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-box {
  height: 420px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
