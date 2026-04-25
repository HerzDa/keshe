<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <h2>会计审批中心</h2>
      <p>查看全员已提交票据，执行同意或撤回审批。</p>
    </div>

    <el-card class="mt panel">
      <template #header>
        <div class="card-head">
          <span>待审票据列表</span>
          <el-button size="small" @click="loadData">刷新</el-button>
        </div>
      </template>

      <el-table :data="list" border stripe>
        <el-table-column prop="employee_name" label="申请人" width="120" />
        <el-table-column prop="budget_item" label="相关预算项" min-width="200" />
        <el-table-column prop="reason" label="摘要" min-width="220" />
        <el-table-column prop="amount" label="金额" width="110" />
        <el-table-column prop="status_label" label="状态" width="120" />
        <el-table-column prop="created_at" label="创建时间" min-width="170" />
        <el-table-column label="审批操作" width="280">
          <template #default="scope">
            <el-button size="small" @click="openDetail(scope.row)">查看详情</el-button>
            <el-button size="small" type="success" @click="audit(scope.row, 'approve')">同意</el-button>
            <el-button size="small" type="danger" @click="openReject(scope.row)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="mt panel">
      <template #header>
        <div class="card-head">
          <span>历史审批票据</span>
          <el-button size="small" @click="loadHistory">刷新</el-button>
        </div>
      </template>

      <el-table :data="historyList" border stripe>
        <el-table-column prop="employee_name" label="申请人" width="120" />
        <el-table-column prop="budget_item" label="相关预算项" min-width="200" />
        <el-table-column prop="amount" label="金额" width="110" />
        <el-table-column prop="status_label" label="审批结果" width="130" />
        <el-table-column prop="accountant_reply" label="审批回复" min-width="240" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="openDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" title="票据审批详情" width="760px">
      <div v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="申请人">{{ current.employee_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ current.status_label }}</el-descriptions-item>
          <el-descriptions-item label="预算项">{{ current.budget_item || '-' }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ current.amount }}</el-descriptions-item>
          <el-descriptions-item label="摘要" :span="2">{{ current.reason || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审批回复" :span="2">{{ current.accountant_reply || '-' }}</el-descriptions-item>
          <el-descriptions-item label="报销日期">{{ current.reimbursement_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ current.created_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="6位编码">{{ current?.invoice_basic?.code_6 || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发票代码">{{ current?.invoice_basic?.invoice_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发票号码">{{ current?.invoice_basic?.invoice_num || '-' }}</el-descriptions-item>
          <el-descriptions-item label="开票日期">{{ current?.invoice_basic?.invoice_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="购买方">{{ current?.invoice_basic?.buyer_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售方">{{ current?.invoice_basic?.seller_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="价税合计" :span="2">{{ current?.invoice_basic?.total_amount || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="origin-wrap" v-if="current?.invoice_basic?.preview_url">
          <div class="origin-title">发票原件预览</div>
          <el-image
            :src="current.invoice_basic.preview_url"
            :preview-src-list="[current.invoice_basic.preview_url]"
            fit="contain"
            class="origin-image"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="拒绝并回复" width="520px">
      <el-input
        v-model="rejectReply"
        type="textarea"
        :rows="4"
        placeholder="例如：缺少行程单原件、发票抬头不完整等"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const list = ref([])
const historyList = ref([])
const detailVisible = ref(false)
const current = ref(null)
const rejectVisible = ref(false)
const rejectTarget = ref(null)
const rejectReply = ref('')

const loadData = async () => {
  if (user.role !== 'accountant') {
    ElMessage.error('当前账号不是会计员，无法访问审批数据')
    return
  }
  const { data } = await request.get('/accountant/reimbursement/pending/', { params: { employee_id: user.id } })
  list.value = data
}

const loadHistory = async () => {
  const { data } = await request.get('/accountant/reimbursement/history/', { params: { employee_id: user.id } })
  historyList.value = data
}

const audit = async (row, action) => {
  await request.post(`/accountant/reimbursement/${row.id}/audit/`, {
    employee_id: user.id,
    action,
  })
  ElMessage.success(action === 'approve' ? '审批同意成功' : '操作成功')
  await loadData()
  await loadHistory()
}

const openDetail = (row) => {
  current.value = row
  detailVisible.value = true
}

const openReject = (row) => {
  rejectTarget.value = row
  rejectReply.value = ''
  rejectVisible.value = true
}

const confirmReject = async () => {
  if (!rejectReply.value.trim()) {
    ElMessage.error('请填写拒绝原因')
    return
  }
  await request.post(`/accountant/reimbursement/${rejectTarget.value.id}/audit/`, {
    employee_id: user.id,
    action: 'reject',
    reply: rejectReply.value.trim(),
  })
  ElMessage.success('已拒绝并回复申请人')
  rejectVisible.value = false
  await loadData()
  await loadHistory()
}

onMounted(async () => {
  await loadData()
  await loadHistory()
})
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

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.origin-wrap {
  margin-top: 14px;
  padding: 12px;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
}

.origin-title {
  color: #0f172a;
  margin-bottom: 8px;
  font-weight: 700;
}

.origin-image {
  width: 100%;
  height: 300px;
}

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }
}
</style>
