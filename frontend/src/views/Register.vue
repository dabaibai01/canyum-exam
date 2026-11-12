<template>
  <div class="register-page">
    <van-nav-bar left-text="返回" left-arrow @click-left="goBack" />

    <div class="register-hero">
      <div class="brand-mark">
        <img :src="siteLogo()" alt="铁刷客" class="brand-logo" />
      </div>
      <div class="brand-title">{{ site.site_name }}</div>
      <div class="brand-sub">{{ site.site_subtitle }}</div>
    </div>

    <div class="register-card card">
      <div class="form-title">
        <span>学员注册</span>
        <span class="audit-tip">提交后需管理员审核</span>
      </div>

      <van-form @submit="onSubmit">
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          left-icon="user-o"
          maxlength="50"
          :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
          v-model="form.real_name"
          name="real_name"
          label="姓名"
          placeholder="请输入姓名"
          left-icon="contact-o"
          maxlength="50"
          :rules="[{ required: true, message: '请填写姓名' }]"
        />
        <van-field
          v-model="form.phone"
          name="phone"
          type="tel"
          label="手机号"
          placeholder="请输入手机号（选填）"
          left-icon="phone-o"
          maxlength="11"
        />
        <van-field
          v-model="form.department"
          name="department"
          label="部门"
          placeholder="请输入部门（选填）"
          left-icon="building-o"
          maxlength="100"
        />
        <van-field
          v-model="form.position"
          name="position"
          label="岗位"
          placeholder="请输入岗位（选填）"
          left-icon="bag-o"
          maxlength="100"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请设置登录密码（至少 6 位）"
          left-icon="lock"
          maxlength="50"
          :rules="[
            { required: true, message: '请填写密码' },
            { validator: (val) => val.length >= 6, message: '密码至少 6 位' }
          ]"
        />

        <div class="form-actions">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            提交注册申请
          </van-button>
        </div>
      </van-form>

      <div class="login-link" @click="router.replace('/login')">
        已有账号？返回登录
      </div>
    </div>

    <div class="register-note">
      注册信息仅用于账号审核和学习记录管理，请如实填写。
    </div>
    <div class="login-dev">V2.0 · {{ site.developer_name }}</div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { authApi } from '../api'
import { site, siteLogo } from '../utils/site'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  real_name: '',
  phone: '',
  department: '',
  position: '',
  password: ''
})

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.replace('/login')
}

const onSubmit = async () => {
  loading.value = true
  try {
    const res = await authApi.register({
      username: form.username.trim(),
      real_name: form.real_name.trim(),
      phone: form.phone.trim(),
      department: form.department.trim(),
      position: form.position.trim(),
      password: form.password.trim()
    })
    await showDialog({
      title: '注册申请已提交',
      message: res.message || '管理员审核通过后即可登录，请耐心等待。',
      confirmButtonText: '返回登录'
    })
    router.replace('/login')
  } catch (error) {
    showToast(error.response?.data?.detail || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 30px;
}
.register-hero {
  background: var(--hero-gradient);
  padding: 26px 24px 52px;
  border-radius: 0 0 22px 22px;
  text-align: center;
}
.brand-mark {
  width: 66px;
  height: 66px;
  margin: 0 auto;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}
.brand-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.brand-title {
  margin-top: 12px;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}
.brand-sub {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 1px;
}

.register-card {
  margin: -30px 18px 0;
  padding: 18px 4px 12px;
  position: relative;
  box-shadow: var(--shadow-float);
}
.form-title {
  padding: 0 18px 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.audit-tip {
  font-size: 12px;
  font-weight: 400;
  color: #d97706;
}
.form-actions {
  padding: 18px 16px 6px;
}
.login-link {
  padding: 10px 16px 4px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
}
.register-note {
  margin: 18px 26px 0;
  text-align: center;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-tertiary);
}
.login-dev {
  margin-top: 10px;
  text-align: center;
  font-size: 11px;
  color: var(--text-tertiary);
  opacity: 0.8;
  letter-spacing: 0.3px;
}

/* 夜间模式下保证提示文字和输入框清晰可见 */
:global([data-theme='dark']) .register-card,
:global(html.dark) .register-card {
  background: var(--card-bg);
}
:global([data-theme='dark']) .audit-tip,
:global(html.dark) .audit-tip {
  color: #fbbf24;
}
</style>
