<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <h2>报销申请</h2>
      <p>请填写报销基本信息，并选择已认证发票。</p>
    </div>
    <el-card class="mt panel" id="printArea">
      <template #header>请填写报销基本信息</template>
      <div class="origin-wrap" v-if="invoice.preview_url && !isNoInvoiceBusiness">
        <div class="origin-title">发票原件预览</div>
        <el-image :src="invoice.preview_url" :preview-src-list="[invoice.preview_url]" fit="contain" class="origin-image" />
      </div>
      <el-form :model="form" label-width="110px" class="form-grid">
        <el-form-item label="业务大类" class="full-row">
          <el-radio-group v-model="form.expense_type">
            <el-radio label="日常报销业务">日常报销业务</el-radio>
            <el-radio label="国内旅费业务">国内旅费业务</el-radio>
            <el-radio label="暂借款业务">暂借款业务</el-radio>
            <el-radio label="酬金申报物业">酬金申报物业</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="单项目报销"><el-input v-model="form.project_no" placeholder="请输入项目编号" /></el-form-item>
        <el-form-item label="项目负责人"><el-input v-model="form.project_manager" placeholder="请输入项目负责人" /></el-form-item>
        <el-form-item label="申请人工号"><el-input v-model="form.employee_no" readonly /></el-form-item>
        <el-form-item label="申请人姓名"><el-input v-model="form.applicant_name" readonly /></el-form-item>
        <el-form-item label="角色"><el-input v-model="form.role_name" readonly /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" readonly /></el-form-item>

        <el-form-item label="选择已认证发票" class="full-row" v-if="!isNoInvoiceBusiness">
          <el-select v-model="form.code_6" placeholder="请选择已验真成功发票编码" filterable style="width: 100%" @change="onInvoiceChange">
            <el-option
              v-for="item in successInvoiceOptions"
              :key="item.code_6"
              :label="`${item.code_6} | ${item.invoice_num || '-'} | ¥${item.total_amount || '0.00'}`"
              :value="item.code_6"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="OCR识别" class="full-row" v-if="form.code_6 && !isNoInvoiceBusiness">
          <el-button :loading="ocrPending" @click="runOcrFill">调用增值税发票识别并回填</el-button>
          <span class="ocr-tip">已识别：{{ invoice.invoice_code || '-' }} / {{ invoice.invoice_num || '-' }}</span>
        </el-form-item>

        <template v-if="isDomesticTravel">
          <div class="travel-title">国内旅费业务模板</div>
          <el-form-item label="起飞省份/城市" class="travel-item">
            <el-cascader
              v-model="form.departure_region"
              :options="provinceCityOptions"
              placeholder="请选择起飞省份和城市"
              filterable
              clearable
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="出差地点" class="travel-item">
            <el-cascader
              v-model="form.destination_region"
              :options="provinceCityOptions"
              placeholder="请选择出差省份和城市"
              filterable
              clearable
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="起时间" class="travel-item">
            <el-date-picker v-model="form.travel_start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" style="width: 100%" />
          </el-form-item>
          <el-form-item label="止时间" class="travel-item">
            <el-date-picker v-model="form.travel_end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" style="width: 100%" />
          </el-form-item>
          <el-form-item label="天数" class="travel-item"><el-input :model-value="travelDays" readonly /></el-form-item>
          <el-form-item label="飞机" class="travel-item"><el-input v-model="form.flight_fee" placeholder="0.00" /></el-form-item>
          <el-form-item label="高铁" class="travel-item"><el-input v-model="form.high_speed_fee" placeholder="0.00" /></el-form-item>
          <el-form-item label="火车" class="travel-item"><el-input v-model="form.train_fee" placeholder="0.00" /></el-form-item>
          <el-form-item label="长途" class="travel-item"><el-input v-model="form.long_distance_fee" placeholder="0.00" /></el-form-item>
          <el-form-item label="市内交通/天" class="travel-item"><el-input v-model="form.city_traffic_fee_per_day" placeholder="0.00" /></el-form-item>
          <el-form-item label="住宿费/天" class="travel-item"><el-input v-model="form.hotel_fee_per_day" placeholder="0.00" /></el-form-item>
          <el-form-item label="市内交通(合计)" class="travel-item"><el-input :model-value="cityTrafficTotal" readonly /></el-form-item>
          <el-form-item label="住宿费(合计)" class="travel-item"><el-input :model-value="hotelTotal" readonly /></el-form-item>
          <el-form-item label="其他" class="travel-item"><el-input v-model="form.other_travel_fee" placeholder="0.00" /></el-form-item>
        </template>

        <template v-if="isLoanBusiness || isCompensationBusiness">
          <div class="travel-title">{{ isCompensationBusiness ? '酬金申报物业申请单' : '暂借款业务申请单' }}</div>
          <el-form-item :label="isCompensationBusiness ? '酬金申报人' : '实际报销人'"><el-input v-model="form.actual_applicant_name" readonly /></el-form-item>
          <el-form-item label="手机"><el-input v-model="form.phone" readonly /></el-form-item>
          <el-form-item label="电子邮件"><el-input v-model="form.email" placeholder="请输入电子邮件" /></el-form-item>
          <el-form-item label="支付方式"><el-select v-model="form.pay_method" style="width: 100%"><el-option label="综合支付" value="综合支付" /><el-option label="银行转账" value="银行转账" /><el-option label="现金" value="现金" /></el-select></el-form-item>

          <el-form-item label="借款类型" v-if="!isCompensationBusiness"><el-select v-model="form.loan_type" style="width: 100%"><el-option label="借款" value="借款" /><el-option label="预付款" value="预付款" /></el-select></el-form-item>
          <el-form-item :label="isCompensationBusiness ? '申报金额' : '借款金额'"><el-input v-model="form.loan_amount" :placeholder="isCompensationBusiness ? '请输入申报金额' : '请输入借款金额'" /></el-form-item>
          <el-form-item label="摘要" class="full-row"><el-input v-model="form.reason" placeholder="请输入摘要" /></el-form-item>
          <el-form-item label="项目名称" class="full-row" v-if="!isCompensationBusiness"><el-input v-model="form.project_name" placeholder="请输入项目名称" /></el-form-item>
          <el-form-item label="相关预算项" class="full-row">
            <el-select v-model="form.budget_item" filterable style="width: 100%" placeholder="请选择项目预算项">
              <el-option v-for="item in budgetItemOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item :label="isCompensationBusiness ? '酬金申报人工号' : '借款人工号'"><el-input v-model="form.employee_no" readonly /></el-form-item>
          <el-form-item :label="isCompensationBusiness ? '酬金申报人姓名' : '借款人姓名'"><el-input v-model="form.applicant_name" readonly /></el-form-item>
          <el-form-item label="预计还款日期" v-if="!isCompensationBusiness"><el-date-picker v-model="form.expected_repay_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
          <el-form-item label="具体用途" class="full-row"><el-input v-model="form.usage_detail" type="textarea" :rows="4" placeholder="请输入借款具体用途" /></el-form-item>
          <el-form-item :label="isCompensationBusiness ? '酬金申报说明' : '借款说明'" class="full-row"><el-input v-model="form.description" type="textarea" :rows="3" placeholder="可填写制度依据或补充说明" /></el-form-item>
        </template>

        <el-form-item label="摘要" class="full-row" v-if="!isNoInvoiceBusiness"><el-input v-model="form.reason" placeholder="请输入摘要" /></el-form-item>
        <el-form-item label="报销部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="报销日期"><el-date-picker v-model="form.reimbursement_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item :label="isDomesticTravel ? '金额(自动合计)' : '金额'" v-if="!isLoanBusiness"><el-input v-model="form.amount" :readonly="isDomesticTravel" /></el-form-item>
        <el-form-item label="备注" class="full-row"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <el-divider />
      <div class="meta">报销人：{{ form.applicant_name || user.name }}（{{ form.employee_no || user.employee_no }}）</div>
      <div class="meta" v-if="!isNoInvoiceBusiness">发票代码：{{ invoice.invoice_code }}，发票号码：{{ invoice.invoice_num }}</div>
      <div class="meta" v-if="!isNoInvoiceBusiness">开票日期：{{ invoice.invoice_date }}，价税合计：{{ invoice.total_amount }}</div>
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
import { computed, onMounted, ref, watchEffect } from 'vue'
import { jsPDF } from 'jspdf'
import printJS from 'print-js'
import { ElMessage } from 'element-plus'
import chinaAreaData from 'china-area-data'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const invoice = ref(JSON.parse(localStorage.getItem('invoice') || '{}'))
const successInvoiceOptions = ref([])
const lookupPending = ref(false)
const ocrPending = ref(false)
const budgetItemOptions = ref([])

const buildProvinceCityOptions = () => {
  const map = chinaAreaData || {}
  const provinceMap = map['86'] || {}
  const provinces = Object.entries(provinceMap).map(([code, name]) => ({
    code,
    name: String(name || '')
  }))

  return provinces.map((p) => {
    const cityMap = map[p.code] || {}
    const cities = Object.entries(cityMap).map(([, cityName]) => {
      const label = String(cityName || '')
      return { value: label, label }
    })
    return {
      value: p.name,
      label: p.name,
      children: cities
    }
  })
}

const provinceCityOptions = buildProvinceCityOptions()

const form = ref({
  code_6: invoice.value.code_6 || '',
  project_no: '',
  project_manager: '',
  employee_no: user.employee_no || '',
  applicant_name: user.name || '',
  phone: user.phone || '',
  role_name: user.department || '其他人员',
  department: user.department || '行政部',
  departure_region: [],
  destination_region: [],
  travel_start_date: '',
  travel_end_date: '',
  flight_fee: '',
  high_speed_fee: '',
  train_fee: '',
  long_distance_fee: '',
  city_traffic_fee_per_day: '',
  hotel_fee_per_day: '',
  other_travel_fee: '',
  actual_applicant_name: user.name || '',
  email: '',
  pay_method: '综合支付',
  loan_type: '借款',
  loan_amount: '',
  budget_item: '',
  expected_repay_date: '',
  project_name: '',
  usage_detail: '',
  description: '',
  reason: '',
  expense_type: '日常报销业务',
  reimbursement_date: '',
  amount: '',
  remark: '',
  employee_id: user.id
})

const amountUpper = computed(() => {
  if (!form.value.amount) return ''
  return '请以提交后后端返回为准'
})

const isDomesticTravel = computed(() => form.value.expense_type === '国内旅费业务')
const isLoanBusiness = computed(() => form.value.expense_type === '暂借款业务')
const isCompensationBusiness = computed(() => form.value.expense_type === '酬金申报物业')
const isNoInvoiceBusiness = computed(() => isLoanBusiness.value || isCompensationBusiness.value)

const parseMoney = (val) => {
  const n = Number((val || '').toString().replace(/,/g, '').trim())
  return Number.isFinite(n) ? n : 0
}

const travelDays = computed(() => {
  if (!form.value.travel_start_date || !form.value.travel_end_date) return ''
  const start = new Date(form.value.travel_start_date)
  const end = new Date(form.value.travel_end_date)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return ''
  const oneDay = 24 * 60 * 60 * 1000
  return Math.floor((end - start) / oneDay) + 1
})

const cityTrafficTotal = computed(() => {
  const days = Number(travelDays.value || 0)
  return (parseMoney(form.value.city_traffic_fee_per_day) * days).toFixed(2)
})

const hotelTotal = computed(() => {
  const days = Number(travelDays.value || 0)
  return (parseMoney(form.value.hotel_fee_per_day) * days).toFixed(2)
})

const domesticTravelTotal = computed(() => {
  const total =
    parseMoney(form.value.flight_fee) +
    parseMoney(form.value.high_speed_fee) +
    parseMoney(form.value.train_fee) +
    parseMoney(form.value.long_distance_fee) +
    parseMoney(cityTrafficTotal.value) +
    parseMoney(hotelTotal.value) +
    parseMoney(form.value.other_travel_fee)
  return total.toFixed(2)
})

watchEffect(() => {
  if (isDomesticTravel.value) {
    form.value.amount = domesticTravelTotal.value
  }
})

const travelExtraRemark = () => {
  if (!isDomesticTravel.value) return form.value.remark || ''
  const departure = form.value.departure_region?.join(' / ') || '-'
  const destination = form.value.destination_region?.join(' / ') || '-'
  const lines = [
    `【国内旅费】出差人：${form.value.applicant_name}(${form.value.employee_no})`,
    `角色：${form.value.role_name} 电话：${form.value.phone}`,
    `起飞地：${departure}，出差地：${destination}`,
    `起止时间：${form.value.travel_start_date || '-'} ~ ${form.value.travel_end_date || '-'}，天数：${travelDays.value || '-'}`,
    `交通住宿：飞机${form.value.flight_fee || 0} 高铁${form.value.high_speed_fee || 0} 火车${form.value.train_fee || 0} 长途${form.value.long_distance_fee || 0} 市内/天${form.value.city_traffic_fee_per_day || 0}(合计${cityTrafficTotal.value}) 住宿/天${form.value.hotel_fee_per_day || 0}(合计${hotelTotal.value}) 其他${form.value.other_travel_fee || 0}`,
    form.value.remark || ''
  ]
  return lines.filter(Boolean).join('\n')
}

const detectTransportType = (data) => {
  const text = JSON.stringify(data?.ocr_result || {}) +
    ` ${data?.seller_name || ''} ${data?.buyer_name || ''} ${data?.invoice_code || ''}`
  if (/飞机|航空|机票|air/i.test(text)) return 'flight'
  if (/高铁|动车/.test(text)) return 'high_speed'
  if (/火车|铁路|客票|train/i.test(text)) return 'train'
  return ''
}

const save = async (action) => {
  if (!form.value.employee_id || !form.value.employee_no || !form.value.applicant_name) {
    ElMessage.error('请先输入有效工号并完成自动匹配')
    return
  }
  if (!isNoInvoiceBusiness.value && !form.value.code_6) {
    ElMessage.error('请选择已认证发票')
    return
  }
  let api = '/reimbursement/save/'
  let payload = { ...form.value, remark: travelExtraRemark(), action }

  if (isDomesticTravel.value) {
    form.value.amount = domesticTravelTotal.value
    payload.amount = domesticTravelTotal.value
  }

  if (isLoanBusiness.value || isCompensationBusiness.value) {
    if (!form.value.loan_amount || !form.value.usage_detail || !form.value.budget_item) {
      ElMessage.error('请完善金额、具体用途和相关预算项')
      return
    }
    if (isLoanBusiness.value && !form.value.project_name) {
      ElMessage.error('请填写项目名称')
      return
    }
    api = '/loan/save/'
    payload = {
      employee_id: form.value.employee_id,
      applicant_name: form.value.applicant_name,
      phone: form.value.phone,
      summary: form.value.reason,
      project_name: isCompensationBusiness.value ? '酬金申报物业' : form.value.project_name,
      budget_item: form.value.budget_item,
      usage_detail: form.value.usage_detail,
      loan_type: isCompensationBusiness.value ? '酬金申报物业' : form.value.loan_type,
      loan_amount: form.value.loan_amount,
      expected_repay_date: isCompensationBusiness.value ? null : form.value.expected_repay_date,
      description: form.value.description || form.value.remark,
      action
    }
    form.value.amount = form.value.loan_amount
  }

  const { data } = await request.post(api, payload)
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
    form.value.role_name = data.department || '其他人员'
    form.value.department = data.department || form.value.department
    form.value.phone = data.phone
    await loadSuccessInvoices()
  } catch (error) {
    form.value.employee_id = ''
    form.value.applicant_name = ''
    form.value.role_name = ''
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
  if (isDomesticTravel.value && selected.total_amount) {
    const t = detectTransportType(selected)
    if (t === 'flight') form.value.flight_fee = String(selected.total_amount)
    if (t === 'high_speed') form.value.high_speed_fee = String(selected.total_amount)
    if (t === 'train') form.value.train_fee = String(selected.total_amount)
    form.value.amount = domesticTravelTotal.value
  } else if (!form.value.amount && selected.total_amount) {
    form.value.amount = selected.total_amount
  }
}

const runOcrFill = async () => {
  if (!form.value.code_6) {
    ElMessage.error('请先选择发票编码')
    return
  }
  ocrPending.value = true
  try {
    const { data } = await request.post('/invoice/ocr-by-code/', { employee_id: form.value.employee_id, code_6: form.value.code_6 })
    invoice.value = data
    localStorage.setItem('invoice', JSON.stringify(data))
    if (isDomesticTravel.value && data.total_amount) {
      const t = detectTransportType(data)
      if (t === 'flight') form.value.flight_fee = String(data.total_amount)
      if (t === 'high_speed') form.value.high_speed_fee = String(data.total_amount)
      if (t === 'train') form.value.train_fee = String(data.total_amount)
      form.value.amount = domesticTravelTotal.value
    } else if (!form.value.amount && data.total_amount) {
      form.value.amount = data.total_amount
    }
    if (!form.value.reason) {
      form.value.reason = `报销-${data.seller_name || '商户'}-${data.invoice_num || ''}`
    }
    ElMessage.success('增值税发票识别成功，已回填信息')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || 'OCR识别失败')
  } finally {
    ocrPending.value = false
  }
}

const loadBudgetItems = async () => {
  try {
    const { data } = await request.get('/budget/template/')
    budgetItemOptions.value = (data.rows || [])
      .filter((item) => item.type === 'item' && item.subject)
      .map((item) => item.subject)
  } catch (error) {
    budgetItemOptions.value = []
    ElMessage.warning('预算项加载失败，请稍后重试')
  }
}

onMounted(async () => {
  await loadBudgetItems()
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

.travel-title {
  grid-column: 1 / -1;
  margin: 6px 0 8px;
  padding: 10px 12px;
  border-left: 4px solid #2d7be8;
  background: #eff6ff;
  color: #1e3a8a;
  font-weight: 700;
}

.travel-item {
  margin-bottom: 8px;
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

.ocr-tip {
  margin-left: 10px;
  color: #64748b;
  font-size: 13px;
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
