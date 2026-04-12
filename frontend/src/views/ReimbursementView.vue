<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <h2>报销申请</h2>
      <p>请填写报销基本信息，并选择已认证发票。</p>
    </div>
    <el-card class="mt panel" id="printArea">
      <template #header>请填写报销基本信息</template>
      <div class="origin-wrap" v-if="invoice.preview_url">
        <div class="origin-title">发票原件预览</div>
        <el-image :src="invoice.preview_url" :preview-src-list="[invoice.preview_url]" fit="contain" class="origin-image" />
      </div>
      <el-form :model="form" label-width="110px" class="form-grid">
        <el-form-item label="业务大类" class="full-row">
          <el-radio-group v-model="form.expense_type">
            <el-radio label="日常报销业务">日常报销业务</el-radio>
            <el-radio label="国内旅费业务">国内旅费业务</el-radio>
            <el-radio label="暂借款业务">暂借款业务</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="单项目报销"><el-input v-model="form.project_no" placeholder="请输入项目编号" /></el-form-item>
        <el-form-item label="项目负责人"><el-input v-model="form.project_manager" placeholder="请输入项目负责人" /></el-form-item>
        <el-form-item label="申请人工号">
          <el-input v-model="form.employee_no" placeholder="输入工号后回车" @keyup.enter="lookupEmployeeByNo" @blur="lookupEmployeeByNo" />
        </el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" readonly /></el-form-item>
        <el-form-item label="申请人姓名"><el-input v-model="form.applicant_name" readonly /></el-form-item>
        <el-form-item label="手机"><el-input v-model="form.phone" readonly /></el-form-item>
        <el-form-item label="摘要" class="full-row"><el-input v-model="form.reason" placeholder="请输入摘要" /></el-form-item>
        <el-form-item label="选择已认证发票" class="full-row">
          <el-select v-model="form.code_6" placeholder="请选择已验真成功发票编码" filterable style="width: 100%" @change="onInvoiceChange">
            <el-option
              v-for="item in successInvoiceOptions"
              :key="item.code_6"
              :label="`${item.code_6} | ${item.invoice_num || '-'} | ¥${item.total_amount || '0.00'}`"
              :value="item.code_6"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="报销部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="报销日期"><el-date-picker v-model="form.reimbursement_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="金额"><el-input v-model="form.amount" /></el-form-item>
        <el-form-item label="备注" class="full-row"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <el-divider />
      <div class="meta">报销人：{{ form.applicant_name || user.name }}（{{ form.employee_no || user.employee_no }}）</div>
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
import { computed, onMounted, ref } from 'vue'
import { jsPDF } from 'jspdf'
import printJS from 'print-js'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const invoice = ref(JSON.parse(localStorage.getItem('invoice') || '{}'))
const successInvoiceOptions = ref([])
const lookupPending = ref(false)

const form = ref({
  code_6: invoice.value.code_6 || '',
  project_no: '',
  project_manager: '',
  employee_no: user.employee_no || '',
  applicant_name: user.name || '',
  phone: user.phone || '',
  department: '',
  reason: '',
  expense_type: '日常报销业务',
  reimbursement_date: '',
  amount: invoice.value.total_amount || '',
  remark: '',
  employee_id: user.id
})

const amountUpper = computed(() => {
  if (!form.value.amount) return ''
  return '请以提交后后端返回为准'
})

const save = async (action) => {
  if (!form.value.employee_id || !form.value.employee_no || !form.value.applicant_name) {
    ElMessage.error('请先输入有效工号并完成自动匹配')
    return
  }
  if (!form.value.code_6) {
    ElMessage.error('请选择已认证发票')
    return
  }
  const payload = { ...form.value, action }
  const { data } = await request.post('/reimbursement/save/', payload)
  ElMessage.success(action === 'submit' ? '提交成功' : '草稿保存成功')
  if (data.amount_upper) {
    ElMessage.info(`金额大写：${data.amount_upper}`)
  }
}

const lookupEmployeeByNo = async () => {
  const employeeNo = (form.value.employee_no || '').trim()
  if (!employeeNo || lookupPending.value) return
  lookupPending.value = true
  try {
    const { data } = await request.get('/auth/employee-by-no/', { params: { employee_no: employeeNo } })
    form.value.employee_id = data.id
    form.value.employee_no = data.employee_no
    form.value.applicant_name = data.name
    form.value.phone = data.phone
    await loadSuccessInvoices()
  } catch (error) {
    form.value.employee_id = ''
    form.value.applicant_name = ''
    form.value.phone = ''
    successInvoiceOptions.value = []
    form.value.code_6 = ''
    const msg = error?.response?.data?.detail || '工号查询失败'
    ElMessage.error(msg)
  } finally {
    lookupPending.value = false
  }
}

const loadSuccessInvoices = async () => {
  if (!form.value.employee_id) return
  const { data } = await request.get('/invoice/success-list/', { params: { employee_id: form.value.employee_id } })
  successInvoiceOptions.value = data
  if (form.value.code_6) {
    onInvoiceChange(form.value.code_6)
  }
}

const onInvoiceChange = (code6) => {
  const selected = successInvoiceOptions.value.find((item) => item.code_6 === code6)
  if (!selected) return
  invoice.value = selected
  localStorage.setItem('invoice', JSON.stringify(selected))
  if (!form.value.amount && selected.total_amount) {
    form.value.amount = selected.total_amount
  }
}

onMounted(async () => {
  if (form.value.employee_no) {
    await lookupEmployeeByNo()
  }
})

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

.origin-wrap {
  margin-bottom: 14px;
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
  height: 260px;
}

.full-row {
  grid-column: 1 / -1;
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
