<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <router-view />
    <van-tabbar v-if="showTabbar" route safe-area-inset-bottom>
      <van-tabbar-item to="/home" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/practice" icon="records">刷题</van-tabbar-item>
      <van-tabbar-item to="/wrong" icon="warning-o">错题本</van-tabbar-item>
      <van-tabbar-item to="/video" icon="video-o">学习</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'

const route = useRoute()
const showTabbar = ref(true)
const isDarkMode = ref(false)

const HIDE_TABBAR = ['/login', '/practice/start', '/exam/start', '/change-password']

watch(
  () => route.path,
  (path) => {
    showTabbar.value = !HIDE_TABBAR.includes(path)
  },
  { immediate: true }
)

// 夜间模式切换
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('darkMode', isDarkMode.value)
  document.documentElement.classList.toggle('dark-mode', isDarkMode.value)
  showToast(isDarkMode.value ? '夜间模式已开启' : '夜间模式已关闭')
}

onMounted(() => {
  // 读取用户偏好
  const saved = localStorage.getItem('darkMode')
  if (saved === 'true') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark-mode')
  }
  // 暴露全局方法供其他页面调用
  window.toggleDarkMode = toggleDarkMode
})
</script>

<style>
/* ============ 设计变量（亮色） ============ */
:root {
  --brand-900: #0b2c55;
  --brand-700: #103c78;
  --brand: #17579c;
  --brand-light: #e9f1fb;
  --accent: #d98600;
  --success: #12a150;
  --danger: #e5484d;

  --bg-color: #f2f4f8;
  --card-bg: #ffffff;
  --card-bg-sub: #f7f9fc;
  --text-color: #1a2433;
  --text-secondary: #7a8798;
  --text-tertiary: #a3adbb;
  --border-color: #e7ebf2;
  --primary-color: var(--brand);
  --shadow-card: 0 6px 18px rgba(16, 44, 85, 0.06);
  --shadow-float: 0 10px 24px rgba(16, 44, 85, 0.12);
  --radius-lg: 14px;
  --radius-md: 10px;
  --hero-gradient: linear-gradient(135deg, #0f3568 0%, #17579c 55%, #2f7ac4 100%);

  /* Vant 主题变量 */
  --van-primary-color: #17579c;
  --van-success-color: #12a150;
  --van-danger-color: #e5484d;
  --van-warning-color: #d98600;
  --van-background: #f2f4f8;
  --van-background-2: #ffffff;
  --van-text-color: #1a2433;
  --van-text-color-2: #7a8798;
  --van-border-color: #e7ebf2;
  --van-nav-bar-title-font-size: 16px;
  --van-cell-group-inset-radius: 14px;
  --van-tabbar-height: 54px;
  --van-tabbar-background: #ffffff;
  --van-tabbar-item-active-color: #17579c;
  --van-tabbar-item-text-color: #7a8798;
}

/* ============ 暗色模式 ============ */
:root.dark-mode {
  --brand: #4f9bf0;
  --brand-light: #1e2f45;
  --accent: #f0ad4e;

  --bg-color: #12161c;
  --card-bg: #1c222b;
  --card-bg-sub: #232a35;
  --text-color: #eef1f5;
  --text-secondary: #97a3b4;
  --text-tertiary: #6b7787;
  --border-color: #2c3542;
  --shadow-card: 0 6px 18px rgba(0, 0, 0, 0.35);
  --shadow-float: 0 10px 24px rgba(0, 0, 0, 0.45);
  --hero-gradient: linear-gradient(135deg, #0a1f3d 0%, #13315c 55%, #1c4b82 100%);

  --van-primary-color: #4f9bf0;
  --van-background: #12161c;
  --van-background-2: #1c222b;
  --van-text-color: #eef1f5;
  --van-text-color-2: #97a3b4;
  --van-border-color: #2c3542;
  --van-tabbar-background: #1c222b;
  --van-tabbar-item-active-color: #4f9bf0;
  --van-tabbar-item-text-color: #97a3b4;
}

html, body {
  margin: 0;
  padding: 0;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  transition: background-color 0.25s, color 0.25s;
}

/* ============ 通用页面与卡片 ============ */
.page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 24px;
  box-sizing: border-box;
}

.section {
  padding: 0 14px;
  margin-top: 16px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 0 2px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  letter-spacing: 0.2px;
}

.section-more {
  font-size: 12px;
  color: var(--text-secondary);
}

.card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* ============ Vant 统一风格 ============ */
.van-nav-bar {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}
.van-nav-bar__title {
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: 0.5px;
}
.van-nav-bar__text,
.van-nav-bar .van-icon {
  color: var(--text-secondary);
}
.van-hairline--bottom::after {
  border-bottom-width: 0;
}

.van-cell {
  background: var(--card-bg);
  color: var(--text-color);
}
.van-cell__title > span {
  color: var(--text-color);
}
.van-cell__label {
  color: var(--text-secondary);
}
.van-cell-group__title {
  color: var(--text-secondary);
  font-size: 13px;
}
.van-cell-group--inset {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  margin: 0 14px;
}

.van-tabbar {
  box-shadow: 0 -4px 16px rgba(16, 44, 85, 0.06);
  border-top: 1px solid var(--border-color);
}
.van-tabbar-item {
  font-size: 12px;
}
.van-tabbar-item__icon {
  font-size: 20px;
  margin-bottom: 3px;
}
.van-tabbar-item--active .van-tabbar-item__icon {
  transform: translateY(-1px);
}

.van-button--primary:not(.van-button--plain) {
  background: var(--brand);
  border-color: var(--brand);
}
.van-button--round {
  font-weight: 500;
}

.van-empty__description {
  color: var(--text-secondary);
}

/* 暗色下的通用修正 */
.dark-mode .van-nav-bar,
.dark-mode .van-cell,
.dark-mode .van-cell-group,
.dark-mode .van-tabbar,
.dark-mode .van-tabs__wrap,
.dark-mode .van-tabs__nav,
.dark-mode .van-tabs__content {
  background-color: var(--card-bg);
}
.dark-mode .van-hairline--top-bottom::after,
.dark-mode .van-hairline-unset--top-bottom::after {
  border-color: var(--border-color);
}
.dark-mode .van-popup,
.dark-mode .van-dialog {
  background: var(--card-bg);
  color: var(--text-color);
}
.dark-mode .van-button--plain {
  background: transparent;
  border-color: var(--border-color);
  color: var(--text-color);
}
.dark-mode .van-button--plain.van-button--primary {
  color: var(--brand);
  border-color: var(--brand);
}
.dark-mode .van-button--plain.van-button--danger {
  color: var(--danger);
  border-color: rgba(229, 72, 77, 0.5);
}
.dark-mode .van-search {
  background: var(--card-bg);
}
.dark-mode .van-search__content {
  background: var(--card-bg-sub);
}
</style>
