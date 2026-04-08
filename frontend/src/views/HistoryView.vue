<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <h2>我的票据夹</h2>
      <p>查看个人报销历史与单据状态。</p>
    </div>
    <el-card class="mt panel">
      <template #header>
        <span>个人报销历史</span>
      </template>
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 200px" @change="loadData">
        <el-option label="全部" value="" />
        <el-option label="草稿" value="draft" />
        <el-option label="已提交" value="submitted" />
      </el-select>
      <el-table :data="list" border stripe class="mt">
        <el-table-column prop="invoice_basic.code_6" label="6位编码" />
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="status" label="状态" />
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const statusFilter = ref('')
const list = ref([])

const loadData = async () => {
  const { data } = await request.get('/reimbursement/history/', {
    params: { employee_id: user.id, status: statusFilter.value }
  })
  list.value = data
}

onMounted(loadData)
</script>

<style scoped>
.shell {
  padding: 24px;
  margin-left: 220px;
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

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }
}
</style>
