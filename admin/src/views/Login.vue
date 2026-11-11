<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <div class="login-brand">
        <img :src="siteLogo()" alt="可以云码" class="login-logo" />
        <div>
          <div class="login-title">{{ site.site_name }}</div>
          <div class="login-sub">{{ site.site_subtitle }} · 管理后台</div>
        </div>
      </div>
      <el-form :model="form" label-width="0" @submit.prevent>
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="login"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%;" :loading="loading" @click="login">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-tip">仅管理员账号可登录，学员请使用学员端</div>
      <div class="login-dev">V1.1 · {{ site.developer_name }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { authApi } from '../api'
import { site, siteLogo } from '../utils/site'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const login = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await authApi.login(form.value)
    if (res.user?.role !== 'admin') {
      ElMessage.error('该账号没有管理员权限')
      return
    }
    localStorage.setItem('adminToken', res.access_token)
    localStorage.setItem('adminInfo', JSON.stringify(res.user))
    ElMessage.success('登录成功')
    router.replace('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 20% 20%, #e8efff, #f4f6fb 60%);
}
.login-card {
  width: 400px;
  padding: 12px 8px 4px;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(31, 60, 110, 0.12);
}
.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 18px 4px;
}
.login-logo {
  width: 52px;
  height: 52px;
  border-radius: 13px;
  object-fit: cover;
  flex: none;
}
.login-title {
  text-align: left;
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
  line-height: 1.3;
}
.login-sub {
  text-align: left;
  margin: 4px 0 0;
  font-size: 11px;
  color: #8a94a6;
  letter-spacing: 0.3px;
}
.login-tip {
  text-align: center;
  font-size: 12px;
  color: #a3adbb;
  margin-top: 6px;
}
.login-dev {
  text-align: center;
  font-size: 11px;
  color: #b0b9c6;
  margin: 8px 0 2px;
}
</style>
