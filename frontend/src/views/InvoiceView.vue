<template>
  <div class="page shell">
    <TopNav />
    <div class="header">
      <div>
        <h2>新建报销申请</h2>
        <p>上传发票并进行识别，系统会自动生成可报销编码。</p>
      </div>
    </div>

    <el-card class="mt panel">
      <template #header>步骤1：上传发票并验真</template>
      <div class="hint">上传后系统会自动调用识别API，并回填发票代码、号码、日期与金额信息。</div>
      <el-form :model="verifyForm" label-width="120px" class="form-grid">
        <el-form-item label="发票文件"><input class="native-file" type="file" @change="onFileChange" /></el-form-item>
        <el-form-item label="发票代码"><el-input v-model="verifyForm.invoice_code" readonly /></el-form-item>
        <el-form-item label="发票号码"><el-input v-model="verifyForm.invoice_num" readonly /></el-form-item>
        <el-form-item label="开票日期"><el-input v-model="verifyForm.invoice_date" placeholder="自动识别" readonly /></el-form-item>
        <el-form-item label="校验码后6位"><el-input v-model="verifyForm.check_code" placeholder="自动识别" readonly /></el-form-item>
        <el-form-item label="价税合计"><el-input v-model="verifyForm.total_amount" readonly /></el-form-item>
        <el-form-item label="购买方名称"><el-input v-model="verifyForm.buyer_name" placeholder="自动识别" readonly /></el-form-item>
        <el-form-item label="销售方名称"><el-input v-model="verifyForm.seller_name" placeholder="自动识别" readonly /></el-form-item>
      </el-form>
      <el-button type="primary" :loading="uploading" @click="uploadVerify">上传并验真</el-button>
      <div v-if="invoice.id" class="result">
        验真状态：{{ invoice.verify_status }} | 提示：{{ invoice.verify_msg }} | 6位编码：{{ invoice.code_6 || '未生成' }}
      </div>
    </el-card>

    <el-card class="mt panel">
      <template #header>步骤2：输入6位编码OCR回填</template>
      <el-input v-model="code6" style="width: 240px" placeholder="例如 260001" />
      <el-button type="success" @click="runOcr" style="margin-left: 10px">OCR识别并回填</el-button>
      <pre class="json" v-if="invoice.ocr_result">{{ JSON.stringify(invoice.ocr_result, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import TopNav from './TopNav.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const fileRef = ref(null)
const uploading = ref(false)
const code6 = ref('')
const invoice = ref({})
const verifyForm = ref({
  invoice_code: '',
  invoice_num: '',
  invoice_date: '',
  check_code: '',
  total_amount: '',
  buyer_name: '',
  seller_name: ''
})

const onFileChange = (e) => {
  fileRef.value = e.target.files[0]
  invoice.value = {}
  verifyForm.value = {
    invoice_code: '',
    invoice_num: '',
    invoice_date: '',
    check_code: '',
    total_amount: '',
    buyer_name: '',
    seller_name: ''
  }
}

const syncFieldsFromInvoice = (data) => {
  verifyForm.value.invoice_code = data.invoice_code || ''
  verifyForm.value.invoice_num = data.invoice_num || ''
  verifyForm.value.invoice_date = data.invoice_date || ''
  verifyForm.value.check_code = data.check_code || ''
  verifyForm.value.total_amount = data.total_amount || ''
  verifyForm.value.buyer_name = data.buyer_name || ''
  verifyForm.value.seller_name = data.seller_name || ''
}

const uploadVerify = async () => {
  if (!fileRef.value) return ElMessage.error('请先选择文件')
  uploading.value = true
  try {
    const form = new FormData()
    form.append('employee_id', user.id)
    form.append('file', fileRef.value)
    const { data } = await request.post('/invoice/upload-verify/', form)
    invoice.value = data
    syncFieldsFromInvoice(data)
    if (data.verify_status === 'success') {
      localStorage.setItem('invoice', JSON.stringify(data))
      code6.value = data.code_6
      ElMessage.success('验真通过，已自动识别并回填发票信息')
    } else {
      ElMessage.error(data.verify_msg || '验真失败，不能进入报销流程')
    }
  } catch (error) {
    const msg = error?.response?.data?.detail || '上传或识别失败，请重试'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

const runOcr = async () => {
  const { data } = await request.post('/invoice/ocr-by-code/', { employee_id: user.id, code_6: code6.value })
  invoice.value = data
  localStorage.setItem('invoice', JSON.stringify(data))
  ElMessage.success('OCR成功，已回填发票结构化信息')
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

.hint {
  color: #64748b;
  font-size: 13px;
  margin-bottom: 10px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 18px;
}

.native-file {
  width: 100%;
}

.result {
  margin-top: 14px;
  color: #0b63ce;
  font-weight: 600;
}

.json { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; }

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
