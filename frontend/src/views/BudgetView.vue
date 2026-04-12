<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <div>
        <h2>项目报销预算</h2>
        <p>用于查看各科目可用预算，防止项目报销超预算。</p>
      </div>
      <div class="project-box">
        <span>项目编号</span>
        <el-input v-model="projectNo" placeholder="例如 PROJ-2026-001" style="width: 240px" />
      </div>
    </div>

    <el-card class="mt panel">
      <template #header>
        <div class="panel-title">
          <span>预算明细</span>
          <span class="sum">总预算：¥{{ totalBudget.toLocaleString() }}，可用：¥{{ totalAvailable.toLocaleString() }}</span>
        </div>
      </template>

      <el-table :data="budgetRows" border stripe :row-class-name="tableRowClassName">
        <el-table-column prop="subject" label="预算项 / 报销项" min-width="280">
          <template #default="scope">
            <span v-if="scope.row.type === 'heading'" class="heading-cell">{{ scope.row.subject }}</span>
            <span v-else>{{ scope.row.subject }}</span>
          </template>
        </el-table-column>
        <el-table-column label="预算 / 可用金额" min-width="320">
          <template #default="scope">
            <div v-if="scope.row.type === 'heading'" class="heading-placeholder">-</div>
            <template v-else>
              <div class="money-line">
                <span>¥{{ scope.row.budget.toLocaleString() }}</span>
                <span class="available">可用 ¥{{ scope.row.available.toLocaleString() }}</span>
              </div>
              <div class="progress-wrap">
                <div class="used" :style="{ width: `${scope.row.usedPercent}%` }"></div>
                <div class="left" :style="{ width: `${100 - scope.row.usedPercent}%` }"></div>
              </div>
              <div class="progress-text">
                <span>已用 {{ scope.row.usedPercent.toFixed(0) }}%</span>
                <span>剩余 {{ (100 - scope.row.usedPercent).toFixed(0) }}%</span>
              </div>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="360">
          <template #default="scope">
            <span v-if="scope.row.type === 'heading'" class="heading-placeholder">-</span>
            <span v-else>{{ scope.row.description || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import TopNav from './TopNav.vue'
import request from '../api/request'

const projectNo = ref('PROJ-2026-001')
const budgetRows = ref([])

const totalBudget = computed(() => budgetRows.value.reduce((sum, row) => sum + (row.type === 'item' ? row.budget : 0), 0))
const totalAvailable = computed(() => budgetRows.value.reduce((sum, row) => sum + (row.type === 'item' ? row.available : 0), 0))

const tableRowClassName = ({ row }) => {
  return row.type === 'heading' ? 'heading-row' : ''
}

onMounted(async () => {
  const { data } = await request.get('/budget/template/', { params: { project_no: projectNo.value } })
  budgetRows.value = (data.rows || []).map((row) => ({
    ...row,
    usedPercent: row.usedPercent ?? row.used_percent ?? 0,
  }))
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
  gap: 16px;
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

.project-box {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334155;
}

.mt { margin-top: 16px; }

.panel {
  border-radius: 14px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sum {
  color: #64748b;
  font-size: 13px;
}

.heading-cell {
  font-weight: 700;
  color: #0f172a;
}

.heading-placeholder {
  color: #94a3b8;
}

.money-line {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}

.available {
  color: #0b63ce;
  font-weight: 700;
}

.progress-wrap {
  width: 100%;
  height: 10px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  background: #e2e8f0;
}

.used {
  height: 100%;
  background: #94a3b8;
}

.left {
  height: 100%;
  background: #22c55e;
}

.progress-text {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 12px;
}

:deep(.heading-row) {
  background: #f8fafc !important;
}

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
