<template>
  <aside class="side-nav">
    <div class="brand">
      <div class="brand-mark">E</div>
      <div class="brand-text">
        <h1>智汇报销</h1>
        <p>{{ isAccountant ? '会计端' : '员工端' }}</p>
      </div>
    </div>

    <el-menu class="menu" :default-active="active" @select="go">
      <el-menu-item index="/dashboard" v-if="!isAccountant">工作台</el-menu-item>
      <el-menu-item index="/invoice" v-if="!isAccountant">发票验真</el-menu-item>
      <el-menu-item index="/reimbursement" v-if="!isAccountant">报销申请</el-menu-item>
      <el-menu-item index="/budget" v-if="!isAccountant">项目预算</el-menu-item>
      <el-menu-item index="/history" v-if="!isAccountant">票据夹</el-menu-item>
      <el-menu-item index="/statistics" v-if="!isAccountant">报销统计</el-menu-item>
      <el-menu-item index="/accountant" v-if="isAccountant">审批中心</el-menu-item>
      <el-menu-item index="logout">退出登录</el-menu-item>
    </el-menu>

    <div class="profile" @click="openProfileDialog">
      <div class="avatar">{{ initials }}</div>
      <div class="meta">
        <div class="name">{{ user.name || '员工' }}</div>
        <div class="id">{{ user.employee_no || '-' }}</div>
      </div>
    </div>

    <el-dialog v-model="profileDialogVisible" title="个人信息设置" width="520px">
      <el-form :model="profileForm" label-width="90px">
        <el-form-item label="工号">
          <el-input v-model="profileForm.employee_no" readonly />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="profileForm.name" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="profileForm.department" placeholder="请选择部门" style="width: 100%">
            <el-option v-for="item in departmentOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="profileForm.phone" />
        </el-form-item>
        <el-divider>修改密码（可选）</el-divider>
        <el-form-item label="旧密码">
          <el-input v-model="profileForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="profileForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存修改</el-button>
      </template>
    </el-dialog>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const router = useRouter()
const route = useRoute()
const active = computed(() => route.path)
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const isAccountant = computed(() => user.value.role === 'accountant')
const initials = computed(() => (user.value.name || '员').slice(0, 1))
const profileDialogVisible = ref(false)
const saving = ref(false)
const departmentOptions = ['行政部', '人事部', '财务部', '市场部', '销售部', '产品部', '技术部']
const profileForm = ref({
  employee_id: '',
  employee_no: '',
  name: '',
  department: '行政部',
  phone: '',
  old_password: '',
  new_password: '',
})

const go = (key) => {
  if (key === 'logout') {
    localStorage.removeItem('user')
    localStorage.removeItem('invoice')
    router.push('/login')
  } else {
    router.push(key)
  }
}

const openProfileDialog = async () => {
  profileDialogVisible.value = true
  const { data } = await request.get('/auth/profile/', { params: { employee_id: user.value.id } })
  profileForm.value.employee_id = data.id
  profileForm.value.employee_no = data.employee_no
  profileForm.value.name = data.name
  profileForm.value.department = data.department || '行政部'
  profileForm.value.phone = data.phone
  profileForm.value.old_password = ''
  profileForm.value.new_password = ''
}

const saveProfile = async () => {
  saving.value = true
  try {
    const payload = {
      employee_id: profileForm.value.employee_id,
      name: profileForm.value.name,
      department: profileForm.value.department,
      phone: profileForm.value.phone,
      old_password: profileForm.value.old_password,
      new_password: profileForm.value.new_password,
    }
    const { data } = await request.put('/auth/profile/', payload)
    user.value = { ...user.value, ...data.user }
    localStorage.setItem('user', JSON.stringify(user.value))
    ElMessage.success('个人信息已更新')
    profileDialogVisible.value = false
  } catch (error) {
    const msg = error?.response?.data?.detail || '保存失败，请重试'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.side-nav {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 220px;
  background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
  border-right: 1px solid #dbe5f0;
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
}

.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #2d7be8, #1761c7);
}

.brand-text h1 {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.brand-text p {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 12px;
}

.menu {
  border-right: none;
  background: transparent;
  flex: 1;
}

:deep(.el-menu-item) {
  margin: 4px 10px;
  border-radius: 10px;
  color: #334155;
}

:deep(.el-menu-item.is-active) {
  color: #0b63ce;
  background: #dbeafe;
  font-weight: 700;
}

.profile {
  margin: 12px;
  padding: 10px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #dbe5f0;
  display: flex;
  gap: 10px;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.profile:hover {
  border-color: #bfdbfe;
  box-shadow: 0 8px 18px rgba(59, 130, 246, 0.12);
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #1d4ed8;
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
}

.name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.id {
  font-size: 12px;
  color: #64748b;
}
</style>
