<template>
  <div class="login-wrap">
    <div class="login-shell">
      <section class="hero">
        <h1>自动化您的费用报销流程</h1>
        <p>基于OCR识别与规则校验，打造更轻量、更规范的企业报销体验。</p>
        <div class="hero-card">SME</div>
      </section>

      <section class="panel">
        <h2>欢迎回来</h2>
        <p class="sub">请输入账号信息继续登录</p>
        <el-tabs v-model="tab">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" label-position="top">
              <el-form-item label="工号">
                <el-input v-model="loginForm.employee_no" placeholder="请输入工号" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
              </el-form-item>
              <el-button class="btn-block" type="primary" @click="handleLogin">登录</el-button>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" label-position="top">
              <el-form-item label="工号"><el-input v-model="registerForm.employee_no" /></el-form-item>
              <el-form-item label="姓名"><el-input v-model="registerForm.name" /></el-form-item>
              <el-form-item label="手机"><el-input v-model="registerForm.phone" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="registerForm.password" type="password" show-password /></el-form-item>
              <el-button class="btn-block" type="success" @click="handleRegister">注册</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const router = useRouter()
const tab = ref('login')
const loginForm = ref({ employee_no: '', password: '' })
const registerForm = ref({ employee_no: '', name: '', phone: '', password: '' })

const handleRegister = async () => {
  const payload = {
    employee_no: registerForm.value.employee_no.trim(),
    name: registerForm.value.name.trim(),
    phone: registerForm.value.phone.trim(),
    password: registerForm.value.password
  }
  if (!payload.employee_no || !payload.name || !payload.password) {
    ElMessage.error('请完整填写工号、姓名和密码')
    return
  }
  try {
    await request.post('/auth/register/', payload)
    ElMessage.success('注册成功，请登录')
    loginForm.value.employee_no = payload.employee_no
    loginForm.value.password = payload.password
    tab.value = 'login'
  } catch (error) {
    const msg = error?.response?.data?.employee_no?.[0] || error?.response?.data?.detail || '注册失败，请重试'
    ElMessage.error(msg)
  }
}

const handleLogin = async () => {
  const payload = {
    employee_no: loginForm.value.employee_no.trim(),
    password: loginForm.value.password
  }
  if (!payload.employee_no || !payload.password) {
    ElMessage.error('请输入工号和密码')
    return
  }
  try {
    const { data } = await request.post('/auth/login/', payload)
    localStorage.setItem('user', JSON.stringify(data.user))
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    const data = error?.response?.data
    const msg = data?.non_field_errors?.[0] || data?.detail || '登录失败，请检查工号或密码'
    ElMessage.error(msg)
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100vh;
  padding: 30px;
  box-sizing: border-box;
  background: linear-gradient(160deg, #e8f2ff 0%, #f8fafc 45%, #eef3fb 100%);
}

.login-shell {
  max-width: 980px;
  margin: 0 auto;
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid #d8e1ed;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
}

.hero {
  padding: 54px 46px;
  background: linear-gradient(160deg, #dce9fb, #cbdff9);
  color: #0f172a;
}

.hero h1 {
  margin: 0;
  font-size: 46px;
  line-height: 1.12;
  color: #1672e6;
}

.hero p {
  margin-top: 16px;
  max-width: 360px;
  line-height: 1.7;
}

.hero-card {
  margin-top: 34px;
  width: 180px;
  height: 180px;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.08);
  display: grid;
  place-items: center;
  font-size: 44px;
  font-weight: 800;
  letter-spacing: 3px;
  color: #fff;
}

.panel {
  background: #ffffff;
  padding: 42px 44px;
}

.panel h2 {
  margin: 8px 0 6px;
  color: #0f172a;
  font-size: 38px;
}

.sub {
  color: #64748b;
  margin: 0 0 14px;
}

.btn-block {
  width: 100%;
  margin-top: 6px;
}

@media (max-width: 900px) {
  .login-wrap {
    padding: 12px;
  }

  .login-shell {
    grid-template-columns: 1fr;
  }

  .hero {
    padding: 24px;
  }

  .hero h1 {
    font-size: 34px;
  }

  .hero-card {
    width: 120px;
    height: 120px;
    font-size: 30px;
  }

  .panel {
    padding: 24px;
  }
}
</style>
