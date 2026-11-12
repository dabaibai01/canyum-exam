<template>
  <div class="login-page">
    <van-nav-bar left-text="返回" left-arrow @click-left="$router.back()" />

    <div class="login-hero">
      <div class="brand-mark">
        <img :src="siteLogo()" alt="铁刷客" class="brand-logo" />
      </div>
      <div class="brand-title">{{ site.site_name }}</div>
      <div class="brand-sub">{{ site.site_subtitle }}</div>
    </div>

    <div class="login-form card">
      <div class="form-title">账号登录</div>
      <van-form @submit="onLogin">
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          left-icon="user-o"
          :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          left-icon="lock"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
        <div class="form-actions">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            登录
          </van-button>
        </div>
      </van-form>
      <div class="register-link" @click="router.push('/register')">
        还没有账号？申请注册
      </div>
    </div>

    <div class="login-tip">如忘记密码或账号异常，请联系管理员</div>
    <div class="login-dev">V2.0 · {{ site.developer_name }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '../api'
import { site, siteLogo } from '../utils/site'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const loading = ref(false)

const onLogin = async () => {
  loading.value = true
  try {
    const res = await authApi.login({
      username: username.value,
      password: password.value
    })
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('userInfo', JSON.stringify(res.user))
    showToast('登录成功！')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
    router.replace(redirect.startsWith('/') ? redirect : '/home')
  } catch (error) {
    showToast(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 30px;
}

.login-hero {
  background: var(--hero-gradient);
  padding: 34px 24px 56px;
  border-radius: 0 0 22px 22px;
  text-align: center;
}
.brand-mark {
  width: 76px;
  height: 76px;
  margin: 0 auto;
  border-radius: 22px;
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
  margin-top: 14px;
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

.login-form {
  margin: -30px 18px 0;
  padding: 18px 4px 8px;
  position: relative;
  box-shadow: var(--shadow-float);
}
.form-title {
  padding: 0 18px 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
}
.form-actions {
  padding: 18px 16px 10px;
}
.register-link {
  padding: 0 16px 10px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
}
.login-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
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
</style>
