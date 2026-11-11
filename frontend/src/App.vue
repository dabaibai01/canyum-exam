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
  color-scheme: dark;
  --brand: #6cb2ff;
  --brand-light: #1e3550;
  --accent: #ffc15c;
  --success: #42d392;
  --danger: #ff7b80;

  --bg-color: #12161c;
  --card-bg: #1c222b;
  --card-bg-sub: #26303d;
  --text-color: #f2f5f9;
  --text-secondary: #c2ccda;
  --text-tertiary: #a3b0c1;
  --border-color: #364252;
  --shadow-card: 0 6px 18px rgba(0, 0, 0, 0.35);
  --shadow-float: 0 10px 24px rgba(0, 0, 0, 0.45);
  --hero-gradient: linear-gradient(135deg, #0a1f3d 0%, #13315c 55%, #1c4b82 100%);

  --van-primary-color: #6cb2ff;
  --van-success-color: #42d392;
  --van-danger-color: #ff7b80;
  --van-warning-color: #ffc15c;
  --van-background: #12161c;
  --van-background-2: #1c222b;
  --van-background-3: #26303d;
  --van-text-color: #f2f5f9;
  --van-text-color-2: #c2ccda;
  --van-text-color-3: #a3b0c1;
  --van-border-color: #364252;
  --van-active-color: #26303d;
  --van-tab-text-color: #c2ccda;
  --van-tab-active-text-color: #6cb2ff;
  --van-tabs-bottom-bar-color: #6cb2ff;
  --van-search-background: #1c222b;
  --van-search-content-background: #26303d;
  --van-field-input-text-color: #f2f5f9;
  --van-field-placeholder-text-color: #a3b0c1;
  --van-cell-text-color: #f2f5f9;
  --van-cell-background: #1c222b;
  --van-popup-background: #1c222b;
  --van-stepper-background: #26303d;
  --van-stepper-input-background: #26303d;
  --van-stepper-input-text-color: #f2f5f9;
  --van-stepper-button-icon-color: #f2f5f9;
  --van-stepper-border-color: #364252;
  --van-tabbar-background: #1c222b;
  --van-tabbar-item-active-color: #6cb2ff;
  --van-tabbar-item-text-color: #c2ccda;
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
.dark-mode .van-search__content .van-field__control {
  color: var(--text-color);
}
.dark-mode .van-search__content .van-field__control::placeholder {
  color: var(--text-tertiary);
}
.dark-mode .van-search .van-icon,
.dark-mode .van-nav-bar .van-icon,
.dark-mode .van-nav-bar__text {
  color: var(--text-secondary);
}
.dark-mode .van-popup .van-icon,
.dark-mode .van-dialog .van-icon {
  color: var(--text-color);
}
.dark-mode .van-tabs__nav .van-tab {
  color: var(--text-secondary);
}
.dark-mode .van-tabs__nav .van-tab--active {
  color: var(--brand);
}
.dark-mode .van-stepper__minus,
.dark-mode .van-stepper__plus,
.dark-mode .van-stepper__input {
  background: var(--card-bg-sub);
  color: var(--text-color);
  border-color: var(--border-color);
}
.dark-mode .van-stepper__minus::before,
.dark-mode .van-stepper__plus::before,
.dark-mode .van-stepper__plus::after {
  background-color: var(--text-color);
}
.dark-mode .van-radio__label,
.dark-mode .van-checkbox__label {
  color: var(--text-color);
}
.dark-mode .van-tag--plain.van-tag--primary {
  color: var(--brand);
  border-color: rgba(108, 178, 255, 0.55);
}
.dark-mode .van-tag--plain.van-tag--danger {
  color: var(--danger);
  border-color: rgba(255, 123, 128, 0.55);
}
.dark-mode .van-tag--plain.van-tag--success {
  color: var(--success);
  border-color: rgba(66, 211, 146, 0.55);
}
.dark-mode .van-tag--plain.van-tag--warning {
  color: var(--accent);
  border-color: rgba(255, 193, 92, 0.55);
}
</style>
