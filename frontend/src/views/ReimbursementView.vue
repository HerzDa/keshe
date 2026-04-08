<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <h2>标准报销单</h2>
      <p>请核对OCR字段并补充报销信息。</p>
    </div>
    <el-card class="mt panel" id="printArea">
      <template #header>通用标准报销单</template>
      <el-form :model="form" label-width="110px" class="form-grid">
        <el-form-item label="6位编码"><el-input v-model="form.code_6" /></el-form-item>
        <el-form-item label="报销部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="报销事由"><el-input v-model="form.reason" /></el-form-item>
        <el-form-item label="费用类型">
          <el-select v-model="form.expense_type" placeholder="请选择">
            <el-option label="办公" value="办公" />
            <el-option label="差旅" value="差旅" />
            <el-option label="招待" value="招待" />
          </el-select>
        </el-form-item>
        <el-form-item label="报销日期"><el-date-picker v-model="form.reimbursement_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="金额"><el-input v-model="form.amount" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <el-divider />
      <div class="meta">报销人：{{ user.name }}（{{ user.employee_no }}）</div>
      <div class="meta">发票代码：{{ invoice.invoice_code }}，发票号码：{{ invoice.invoice_num }}</div>
      <div class="meta">开票日期：{{ invoice.invoice_date }}，价税合计：{{ invoice.total_amount }}</div>
      <div class="meta">金额大写：{{ amountUpper || '-' }}</div>
      <div class="sign">签字区域：经办人________  财务________</div>
    </el-card>

    <div class="mt toolbar">
      <el-button @click="save('draft')">保存草稿</el-button>
      <el-button type="primary" @click="save('submit')">提交报销</el-button>
      <el-button type="success" @click="printBill">打印</el-button>
      <el-button type="warning" @click="exportPdf">导出PDF</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { jsPDF } from 'jspdf'
import printJS from 'print-js'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const invoice = JSON.parse(localStorage.getItem('invoice') || '{}')

const form = ref({
  code_6: invoice.code_6 || '',
  department: '',
  reason: '',
  expense_type: '',
  reimbursement_date: '',
  amount: invoice.total_amount || '',
  remark: '',
  employee_id: user.id
})

const amountUpper = computed(() => {
  if (!form.value.amount) return ''
  return '请以提交后后端返回为准'
})

const save = async (action) => {
  const payload = { ...form.value, action }
  const { data } = await request.post('/reimbursement/save/', payload)
  ElMessage.success(action === 'submit' ? '提交成功' : '草稿保存成功')
  if (data.amount_upper) {
    ElMessage.info(`金额大写：${data.amount_upper}`)
  }
}

const printBill = () => {
  printJS({ printable: 'printArea', type: 'html', scanStyles: true })
}

const exportPdf = () => {
  const doc = new jsPDF('p', 'pt', 'a4')
  doc.setFont('helvetica')
  doc.setFontSize(14)
  doc.text('Reimbursement Form', 40, 50)
  doc.setFontSize(12)
  doc.text(`Employee: ${user.name} (${user.employee_no})`, 40, 80)
  doc.text(`Code6: ${form.value.code_6}`, 40, 105)
  doc.text(`Department: ${form.value.department}`, 40, 130)
  doc.text(`Reason: ${form.value.reason}`, 40, 155)
  doc.text(`Amount: ${form.value.amount}`, 40, 180)
  doc.save(`reimbursement-${form.value.code_6 || 'draft'}.pdf`)
}
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.meta {
  margin-top: 8px;
  color: #334155;
}

.sign {
  margin-top: 20px;
  color: #0f172a;
}

.toolbar {
  display: flex;
  gap: 10px;
}

@media (max-width: 900px) {
  .shell {
    margin-left: 0;
    padding: 12px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
