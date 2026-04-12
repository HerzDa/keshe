<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <div>
        <h2>工作台</h2>
        <p>欢迎回来，这里是你的报销概览。</p>
      </div>
      <el-button type="primary" plain @click="$router.push('/invoice')">新建报销</el-button>
    </div>

    <el-row :gutter="16" class="mt">
      <el-col :span="8"><el-card class="kpi"><div class="label">已报销总笔数</div><div class="num">{{ stats.reimbursement_count || 0 }}</div></el-card></el-col>
      <el-col :span="8">
        <el-card class="kpi clickable" @click="openSuccessInvoices">
          <div class="label">验真成功发票</div>
          <div class="num">{{ stats.verify_success_count || 0 }}</div>
          <div class="tip">点击查看明细</div>
        </el-card>
      </el-col>
      <el-col :span="8"><el-card class="kpi"><div class="label">报销总金额</div><div class="num">¥ {{ stats.total_amount || '0.00' }}</div></el-card></el-col>
    </el-row>

    <el-card class="mt panel">
      <template #header>最近报销记录</template>
      <el-table :data="stats.recent_records || []" border stripe>
        <el-table-column prop="invoice_basic.code_6" label="编码" />
        <el-table-column prop="reason" label="事由" />
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="status" label="状态" />
      </el-table>
    </el-card>

    <el-dialog v-model="successDialogVisible" title="已验真成功发票" width="900px">
      <el-table :data="successInvoices" border stripe v-loading="loadingSuccessInvoices">
        <el-table-column prop="code_6" label="6位编码" width="120" />
        <el-table-column label="发票原件" width="120">
          <template #default="scope">
            <el-image
              v-if="scope.row.preview_url"
              :src="scope.row.preview_url"
              :preview-src-list="[scope.row.preview_url]"
              fit="cover"
              style="width: 72px; height: 48px; border-radius: 6px"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="invoice_code" label="发票代码" width="150" />
        <el-table-column prop="invoice_num" label="发票号码" min-width="180" />
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="total_amount" label="价税合计" width="130" />
        <el-table-column prop="buyer_name" label="购买方名称" min-width="180" />
        <el-table-column prop="seller_name" label="销售方名称" min-width="180" />
        <el-table-column prop="verify_msg" label="验真提示" min-width="220" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const stats = ref({})
const successDialogVisible = ref(false)
const successInvoices = ref([])
const loadingSuccessInvoices = ref(false)

onMounted(async () => {
  const { data } = await request.get('/dashboard/stats/', { params: { employee_id: user.id } })
  stats.value = data
})

const openSuccessInvoices = async () => {
  successDialogVisible.value = true
  loadingSuccessInvoices.value = true
  try {
    const { data } = await request.get('/invoice/success-list/', { params: { employee_id: user.id } })
    successInvoices.value = data
  } finally {
    loadingSuccessInvoices.value = false
  }
}
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
  font-size: 36px;
}

.header p {
  margin: 8px 0 0;
  color: #64748b;
}

.mt { margin-top: 16px; }

.kpi {
  border-radius: 14px;
}

.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(30, 64, 175, 0.14);
}

.label {
  color: #64748b;
  font-size: 13px;
}

.num {
  margin-top: 12px;
  color: #0f172a;
  font-size: 36px;
  font-weight: 800;
}

.tip {
  margin-top: 8px;
  color: #0b63ce;
  font-size: 12px;
}

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
