<template>
  <div class="page change-password-page">
    <van-nav-bar title="修改密码" left-text="返回" left-arrow @click-left="$router.back()" />

    <div class="tip-card card">
      <van-icon name="lock" class="tip-icon" />
      <div>
        <div class="tip-title">修改登录密码</div>
        <div class="tip-sub">修改后需用新密码重新登录</div>
      </div>
    </div>

    <van-form @submit="onSubmit" class="form">
      <van-cell-group inset>
        <van-field
          v-model="oldPassword"
          type="password"
          label="旧密码"
          placeholder="请输入旧密码"
          :rules="[{ required: true, message: '请输入旧密码' }]"
        />
        <van-field
          v-model="newPassword"
          type="password"
          label="新密码"
          placeholder="请输入新密码"
          :rules="[{ required: true, message: '请输入新密码' }]"
        />
        <van-field
          v-model="confirmPassword"
          type="password"
          label="确认新密码"
          placeholder="请再次输入新密码"
          :rules="[{ required: true, message: '请确认新密码' }]"
        />
      </van-cell-group>
      <div class="form-actions">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          确认修改
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast } from 'vant'
import { useRouter } from 'vue-router'

const router = useRouter()
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const onSubmit = async () => {
  if (newPassword.value !== confirmPassword.value) {
    showToast('两次输入的新密码不一致')
    return
  }

  loading.value = true
  try {
    const token = localStorage.getItem('token')

    const res = await fetch('/api/users/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value
      })
    })

    if (res.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      showToast('登录已过期，请重新登录')
      setTimeout(() => router.replace('/login'), 800)
      return
    }

    const data = await res.json()
    if (res.ok) {
      showToast('密码修改成功，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      setTimeout(() => {
        router.replace('/login')
      }, 1200)
    } else {
      showToast(data.detail || '修改失败')
    }
  } catch (error) {
    showToast('修改失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.change-password-page {
  padding-bottom: 30px;
}
.tip-card {
  margin: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.tip-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--brand-light);
  color: var(--brand);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tip-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}
.tip-sub {
  margin-top: 3px;
  font-size: 12px;
  color: var(--text-secondary);
}
.form {
  margin-top: 4px;
}
.form-actions {
  margin: 18px 14px 0;
}
</style>
