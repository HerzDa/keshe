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
        <el-option label="历史功能票据" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-table :data="list" border stripe class="mt">
        <el-table-column prop="invoice_basic.code_6" label="6位编码" />
        <el-table-column prop="budget_item" label="相关预算项" min-width="180" />
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="status_label" label="状态" />
        <el-table-column prop="accountant_reply" label="审批回复" min-width="220" />
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="340">
          <template #default="scope">
            <el-button size="small" type="primary" :disabled="!canEdit(scope.row.status)" @click="openEdit(scope.row)">修改</el-button>
            <el-button size="small" type="success" :disabled="!canEdit(scope.row.status)" @click="submitRow(scope.row)">提交申请</el-button>
            <el-button size="small" type="danger" :disabled="!canEdit(scope.row.status)" @click="removeRow(scope.row)">删除</el-button>
            <el-button size="small" type="warning" :disabled="!canRevoke(scope.row.status)" @click="revokeRow(scope.row)">撤销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editVisible" title="修改草稿票据" width="620px">
      <el-form :model="editForm" label-width="110px">
        <el-form-item label="摘要"><el-input v-model="editForm.reason" /></el-form-item>
        <el-form-item label="报销部门"><el-input v-model="editForm.department" /></el-form-item>
        <el-form-item label="相关预算项">
          <el-select v-model="editForm.budget_item" filterable style="width: 100%">
            <el-option v-for="item in budgetItemOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="报销日期"><el-date-picker v-model="editForm.reimbursement_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="金额"><el-input v-model="editForm.amount" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.remark" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const statusFilter = ref('')
const list = ref([])
const editVisible = ref(false)
const editForm = ref({
  id: null,
  reason: '',
  department: '',
  budget_item: '',
  reimbursement_date: '',
  amount: '',
  remark: ''
})
const budgetItemOptions = ref([])

const canEdit = (status) => ['draft', 'rejected'].includes(status)
const canRevoke = (status) => ['submitted', 'rejected'].includes(status)

const loadData = async () => {
  const { data } = await request.get('/reimbursement/history/', {
    params: { employee_id: user.id, status: statusFilter.value }
  })
  list.value = data
}

const loadBudgetItems = async () => {
  const { data } = await request.get('/budget/template/')
  budgetItemOptions.value = (data.rows || [])
    .filter((item) => item.type === 'item' && item.subject)
    .map((item) => item.subject)
}

const openEdit = (row) => {
  editForm.value = {
    id: row.id,
    reason: row.reason || '',
    department: row.department || '',
    budget_item: row.budget_item || '',
    reimbursement_date: row.reimbursement_date || '',
    amount: row.amount || '',
    remark: row.remark || ''
  }
  editVisible.value = true
}

const saveEdit = async () => {
  if (!editForm.value.budget_item) {
    ElMessage.error('请选择相关预算项')
    return
  }
  await request.put(`/reimbursement/${editForm.value.id}/manage/`, {
    ...editForm.value,
    employee_id: user.id
  })
  ElMessage.success('草稿修改成功')
  editVisible.value = false
  await loadData()
}

const removeRow = async (row) => {
  await ElMessageBox.confirm('确认删除该草稿票据吗？', '提示', { type: 'warning' })
  await request.delete(`/reimbursement/${row.id}/manage/`, { params: { employee_id: user.id } })
  ElMessage.success('删除成功')
  await loadData()
}

const revokeRow = async (row) => {
  await request.post(`/reimbursement/${row.id}/manage/`, { employee_id: user.id, action: 'revoke' })
  ElMessage.success('已撤销为草稿')
  await loadData()
}

const submitRow = async (row) => {
  await request.post(`/reimbursement/${row.id}/manage/`, { employee_id: user.id, action: 'submit' })
  ElMessage.success('草稿提交成功')
  await loadData()
}

onMounted(async () => {
  await loadBudgetItems()
  await loadData()
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

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }
}
</style>
