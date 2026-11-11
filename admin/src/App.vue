<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // 读取夜间模式偏好
  const saved = localStorage.getItem('adminDarkMode')
  if (saved === 'true') {
    document.documentElement.classList.add('dark')
  }
  
  // 暴露全局切换方法
  window.toggleAdminDarkMode = () => {
    const isDark = document.documentElement.classList.toggle('dark')
    localStorage.setItem('adminDarkMode', isDark)
  }
})
</script>

<style>
@import 'element-plus/theme-chalk/dark/css-vars.css';

body {
  margin: 0;
  padding: 0;
  background-color: #f0f2f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.dark body {
  background-color: #141414;
}
</style>
