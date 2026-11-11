<template>
  <div class="page home-page">
    <!-- 顶部渐变头部 -->
    <div class="hero">
      <div class="hero-top">
        <div class="hero-brand-row">
          <img :src="siteLogo()" alt="可以云码" class="hero-logo" />
          <div>
            <div class="hero-brand-name">{{ site.site_name }}</div>
            <div class="hero-hello">你好，{{ userName }}</div>
            <div class="hero-sub">{{ site.site_subtitle }}</div>
          </div>
        </div>
        <div class="hero-right">
          <div class="theme-pill" @click="toggleDarkMode">
            {{ isDarkMode ? '白天' : '夜间' }}
          </div>
          <div class="hero-date">{{ todayText }}</div>
        </div>
      </div>

      <div class="hero-stats">
        <div class="stat">
          <b>{{ totalCount }}</b>
          <span>题库题目</span>
        </div>
        <div class="stat">
          <b>{{ pendingWrong }}</b>
          <span>待复习错题</span>
        </div>
        <div class="stat">
          <b>{{ masteredWrong }}</b>
          <span>已掌握</span>
        </div>
      </div>
    </div>

    <!-- 公告 -->
    <div v-if="notices.length" class="notice-card card">
      <van-swipe
        vertical
        :autoplay="notices.length > 1 ? 4500 : 0"
        :show-indicators="false"
        :touchable="notices.length > 1"
        class="notice-swipe"
      >
        <van-swipe-item v-for="item in notices" :key="item.id" @click="openNotice(item)">
          <div class="notice-row">
            <van-icon name="volume-o" class="notice-icon" />
            <span class="notice-text">{{ item.title }}</span>
            <van-icon name="arrow" class="notice-arrow" />
          </div>
        </van-swipe-item>
      </van-swipe>
    </div>

    <!-- 功能入口 -->
    <div class="section">
      <div class="section-head">
        <span class="section-title">开始学习</span>
      </div>
      <div class="tile-grid">
        <div v-for="item in tiles" :key="item.text" class="tile" @click="onTile(item)">
          <div class="tile-icon" :style="{ background: item.bg, color: item.color }">
            <van-icon :name="item.icon" size="20" />
          </div>
          <div class="tile-text">{{ item.text }}</div>
          <div class="tile-desc">{{ item.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 快速入口 -->
    <div class="section">
      <div class="section-head">
        <span class="section-title">按分类刷题</span>
        <span class="section-more" @click="router.push('/practice')">全部分类</span>
      </div>
      <div class="card cat-card">
        <div
          v-for="(cat, index) in categories"
          :key="cat.id"
          class="cat-row"
          :class="{ 'no-line': index === categories.length - 1 }"
          @click="goPractice(cat.id)"
        >
          <div class="cat-name">{{ cat.name }}</div>
          <div class="cat-count">{{ cat.question_count }} 题</div>
          <van-icon name="arrow" class="cat-arrow" />
        </div>
        <div v-if="!categories.length" class="cat-empty">暂无题库分类</div>
      </div>
    </div>

    <!-- 公告详情 -->
    <van-popup v-model:show="showNotice" position="bottom" round>
      <div class="notice-popup">
        <div class="notice-head">
          <span>公告详情</span>
          <van-icon name="cross" size="18" @click="showNotice = false" />
        </div>
        <div v-if="currentNotice" class="notice-body">
          <div class="notice-title">{{ currentNotice.title }}</div>
          <div class="notice-time">{{ formatTime(currentNotice.updated_at) }}</div>
          <div class="notice-content">{{ currentNotice.content }}</div>
        </div>
      </div>
    </van-popup>

    <!-- 个人中心 -->
    <van-popup v-model:show="showProfile" position="bottom" round>
      <div class="profile">
        <div class="profile-head">
          <span>个人中心</span>
          <van-icon name="cross" size="18" @click="showProfile = false" />
        </div>
        <div class="profile-body">
          <div class="avatar">{{ (userInfo.real_name || userInfo.username || '学').slice(0, 1) }}</div>
          <div class="profile-name">{{ userInfo.real_name || userInfo.username || '学员' }}</div>
          <div class="profile-meta">
            <div class="meta-row"><span>用户名</span><span>{{ userInfo.username || '未设置' }}</span></div>
            <div class="meta-row"><span>部门</span><span>{{ userInfo.department || '未设置' }}</span></div>
            <div class="meta-row"><span>岗位</span><span>{{ userInfo.position || '未设置' }}</span></div>
          </div>
          <div class="profile-about">
            <img :src="siteLogo()" alt="可以云码" class="about-logo" />
            <div class="about-text">
              <b>{{ site.site_name }}</b>
              <span>版本 V1.1 · 2026-11-11</span>
              <span>开发：{{ site.developer_name }}</span>
            </div>
          </div>
          <div class="profile-actions">
            <van-button plain type="primary" block @click="goChangePassword">修改密码</van-button>
            <van-button plain block class="logout-btn" @click="logout">退出登录</van-button>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { questionApi, noticeApi, practiceApi } from '../api'
import { site, siteLogo } from '../utils/site'

const router = useRouter()

const categories = ref([])
const totalCount = ref(0)
const pendingWrong = ref(0)
const masteredWrong = ref(0)
const isDarkMode = ref(false)

const notices = ref([])
const showNotice = ref(false)
const currentNotice = ref(null)

const showProfile = ref(false)
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
const userName = ref(userInfo.value.real_name || userInfo.value.username || '同学')

const tiles = [
  { text: '刷题练习', desc: '分类摸底', icon: 'records', to: '/practice', bg: 'rgba(23,87,156,.1)', color: '#17579c' },
  { text: '错题本', desc: '专项复习', icon: 'warning-o', to: '/wrong', bg: 'rgba(217,134,0,.12)', color: '#d98600' },
  { text: '在线考试', desc: '模拟实战', icon: 'edit', to: '/exam', bg: 'rgba(18,161,80,.12)', color: '#12a150' },
  { text: '视频教学', desc: '跟着学', icon: 'video-o', to: '/video', bg: 'rgba(124,92,255,.12)', color: '#7c5cff' },
  { text: '业务书籍', desc: '查规章', icon: 'notes-o', to: '/book', bg: 'rgba(15,157,160,.12)', color: '#0f9da0' },
  { text: '个人中心', desc: '账号设置', icon: 'user-o', to: '', bg: 'rgba(122,135,152,.14)', color: '#7a8798' }
]

const pad = (n) => String(n).padStart(2, '0')
const formatTime = (v) => {
  if (!v) return ''
  const raw = String(v)
  const d = new Date(raw.endsWith('Z') ? raw : raw + 'Z')
  if (Number.isNaN(d.getTime())) return raw
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const now = new Date()
const weekMap = ['日', '一', '二', '三', '四', '五', '六']
const todayText = `${now.getMonth() + 1}月${now.getDate()}日 周${weekMap[now.getDay()]}`

const loadCategories = async () => {
  try {
    const res = await questionApi.getCategories('question')
    // 只展示一级分类（专业大类），子分类在刷题页里按模块进入；空分类不占位
    categories.value = res.filter(cat => (!cat.parent_id || cat.parent_id === 0) && cat.question_count > 0)
    totalCount.value = categories.value.reduce((sum, cat) => sum + (cat.question_count || 0), 0)
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadWrongStats = async () => {
  try {
    const res = await practiceApi.getWrongList({ page: 1, page_size: 1, status: 'pending' })
    pendingWrong.value = res.pending_total || 0
    masteredWrong.value = res.mastered_total || 0
  } catch (error) {
    console.error('加载错题统计失败', error)
  }
}

const loadNotices = async () => {
  try {
    notices.value = await noticeApi.getHome(5)
  } catch (error) {
    console.error('加载公告失败', error)
  }
}

const openNotice = (item) => {
  currentNotice.value = item
  showNotice.value = true
}

const goPractice = (categoryId) => {
  router.push(`/practice/start?category=${categoryId}&mode=random`)
}

const onTile = (item) => {
  if (item.to) {
    router.push(item.to)
  } else {
    userInfo.value = JSON.parse(localStorage.getItem('userInfo') || '{}')
    showProfile.value = true
  }
}

const goChangePassword = () => {
  showProfile.value = false
  router.push('/change-password')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  showProfile.value = false
  showToast('已退出登录')
  router.push('/login')
}

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('darkMode', isDarkMode.value)
  document.documentElement.classList.toggle('dark-mode', isDarkMode.value)
}

onMounted(() => {
  loadCategories()
  loadWrongStats()
  loadNotices()
  // 读取夜间模式偏好
  const saved = localStorage.getItem('darkMode')
  if (saved === 'true') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark-mode')
  }
})
</script>

<style scoped>
.home-page {
  padding-bottom: 30px;
}

/* 渐变头部 */
.hero {
  background: var(--hero-gradient);
  padding: calc(14px + env(safe-area-inset-top)) 16px 54px;
  border-radius: 0 0 20px 20px;
  position: relative;
}
.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.hero-brand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.hero-logo {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);
  object-fit: cover;
  flex: none;
}
.hero-brand-name {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 1.2px;
  margin-bottom: 3px;
}
.hero-hello {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}
.hero-sub {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 1px;
}
.hero-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.theme-pill {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  cursor: pointer;
}
.hero-date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.hero-stats {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: -28px;
  display: flex;
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 14px 0;
}
.stat {
  flex: 1;
  text-align: center;
  position: relative;
}
.stat + .stat::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 1px;
  background: var(--border-color);
}
.stat b {
  display: block;
  font-size: 19px;
  font-weight: 600;
  color: var(--text-color);
  line-height: 1.2;
}
.stat span {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-secondary);
}

/* 公告卡 */
.notice-card {
  margin: 44px 14px 0;
  display: flex;
  align-items: center;
}
.notice-swipe {
  height: 46px;
  width: 100%;
}
.notice-row {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 14px;
}
.notice-icon {
  color: var(--accent);
  font-size: 16px;
}
.notice-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-color);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.notice-arrow {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* 功能格子 */
.tile-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.tile {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 14px 10px 12px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.15s ease;
}
.tile:active {
  transform: scale(0.97);
}
.tile-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.tile-text {
  margin-top: 9px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}
.tile-desc {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 分类列表 */
.cat-card {
  padding: 2px 0;
}
.cat-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  position: relative;
}
.cat-row::after {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 0;
  height: 1px;
  background: var(--border-color);
}
.cat-row.no-line::after {
  display: none;
}
.cat-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-color);
}
.cat-count {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 999px;
  padding: 2px 8px;
  margin-right: 6px;
}
.cat-arrow {
  color: var(--text-tertiary);
  font-size: 12px;
}
.cat-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

/* 公告详情 */
.notice-popup {
  padding-bottom: 16px;
}
.notice-head,
.profile-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid var(--border-color);
}
.notice-body {
  padding: 14px 16px;
}
.notice-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--text-color);
}
.notice-time {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
.notice-content {
  margin-top: 12px;
  max-height: 50vh;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

/* 个人中心 */
.profile {
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}
.profile-body {
  padding: 20px 18px 4px;
  text-align: center;
}
.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  margin: 0 auto;
  background: var(--brand-light);
  color: var(--brand);
  font-size: 22px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.profile-name {
  margin-top: 10px;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-color);
}
.profile-meta {
  margin-top: 16px;
  background: var(--card-bg-sub);
  border-radius: var(--radius-md);
  padding: 4px 14px;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}
.meta-row:last-child {
  border-bottom: none;
}
.meta-row span:last-child {
  color: var(--text-color);
}
.profile-about {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--card-bg-sub);
  border-radius: var(--radius-md);
}
.about-logo {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  object-fit: cover;
  flex: none;
}
.about-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.35;
}
.about-text b {
  font-size: 13px;
  color: var(--text-color);
}
.profile-actions {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.logout-btn {
  color: var(--danger);
  border-color: var(--border-color);
}
</style>
