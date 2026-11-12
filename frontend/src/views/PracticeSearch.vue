<template>
  <div class="page search-page">
    <van-nav-bar title="搜题" left-text="返回" @click-left="router.back()" />
    <div class="search-box">
      <van-search
        v-model="keyword"
        shape="round"
        placeholder="输入题干或解析里的关键词"
        show-action
        action-text="搜索"
        @search="doSearch"
        @click-action="doSearch"
      />
    </div>

    <div v-if="searched" class="search-summary">
      找到 <b>{{ total }}</b> 道题
      <span v-if="total > items.length">· 显示前 {{ items.length }} 道</span>
    </div>

    <div v-if="loading" class="loading-wrap">
      <van-loading size="24">搜索中...</van-loading>
    </div>

    <div v-else-if="items.length" class="result-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="result-card card"
        @click="openDetail(item)"
      >
        <div class="result-meta">
          <span class="type-pill">{{ typeText(item.type) }}</span>
          <span class="category-text">{{ item.category_name || '未分类' }}</span>
        </div>
        <div class="result-content">{{ item.content }}</div>
        <div class="result-foot">
          <span>答案 {{ formatAnswer(item.correct_answer) }}</span>
          <van-icon name="arrow" />
        </div>
      </div>
      <div v-if="total > items.length" class="search-tip">
        结果较多，请再输入更具体的关键词缩小范围
      </div>
    </div>

    <van-empty v-else-if="searched" description="没有找到相关题目，换个关键词试试" />
    <van-empty v-else description="输入关键词，搜索题干或解析内容" />

    <van-popup v-model:show="detailVisible" position="bottom" round class="detail-popup">
      <div v-if="active" class="detail-body">
        <div class="detail-head">
          <span class="type-pill">{{ typeText(active.type) }}</span>
          <span class="category-text">{{ active.category_name || '未分类' }}</span>
          <van-icon name="cross" class="detail-close" @click="detailVisible = false" />
        </div>
        <div class="detail-question">{{ active.content }}</div>
        <img v-if="active.image" :src="active.image" class="detail-image" alt="题目图片" />

        <div class="detail-options">
          <div
            v-for="option in active.options"
            :key="option.id"
            class="detail-option"
            :class="{ correct: active.correct_answer.includes(option.label) }"
          >
            <span class="detail-letter">{{ option.label }}</span>
            <span class="detail-option-text">{{ option.content }}</span>
            <van-icon
              v-if="active.correct_answer.includes(option.label)"
              name="success"
              class="detail-ok"
            />
          </div>
        </div>

        <div class="detail-answer">正确答案 {{ formatAnswer(active.correct_answer) }}</div>
        <div v-if="active.analysis" class="detail-analysis">
          <div class="detail-title">解析</div>
          <div>{{ active.analysis }}</div>
        </div>
        <div v-if="active.note" class="detail-analysis">
          <div class="detail-title">我的笔记</div>
          <div>{{ active.note }}</div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { practiceApi } from '../api'

const route = useRoute()
const router = useRouter()
const keyword = ref(String(route.query.keyword || ''))
const items = ref([])
const total = ref(0)
const loading = ref(false)
const searched = ref(false)
const detailVisible = ref(false)
const active = ref(null)

const typeText = (type) => {
  const map = { single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题' }
  return map[type] || type
}

const formatAnswer = (answer) => (answer || '').split('').join(' ')

const doSearch = async () => {
  const text = keyword.value.trim()
  if (!text) {
    showToast('请输入搜索关键词')
    return
  }
  loading.value = true
  searched.value = true
  try {
    const res = await practiceApi.searchQuestions({ keyword: text, page: 1, page_size: 30 })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    items.value = []
    total.value = 0
    showToast('搜索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const openDetail = (item) => {
  active.value = item
  detailVisible.value = true
}

onMounted(() => {
  if (keyword.value) doSearch()
})
</script>

<style scoped>
.search-page {
  padding-bottom: 30px;
}
.search-box {
  padding: 8px 12px 0;
}
.search-box :deep(.van-search) {
  padding: 4px 0;
  background: transparent;
}
.search-summary {
  padding: 8px 18px 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.search-summary b {
  color: var(--brand);
}
.loading-wrap {
  padding: 50px 0;
  text-align: center;
}
.result-list {
  padding: 8px 14px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-card {
  padding: 14px 16px;
  cursor: pointer;
}
.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.type-pill {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 6px;
  padding: 2px 7px;
}
.category-text {
  font-size: 12px;
  color: var(--text-tertiary);
}
.result-content {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-color);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.result-foot {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--success);
}
.search-tip {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 8px 0;
}

.detail-popup {
  max-height: 85vh;
}
.detail-body {
  padding: 18px 20px calc(20px + env(safe-area-inset-bottom));
  max-height: 85vh;
  overflow-y: auto;
  box-sizing: border-box;
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.detail-close {
  margin-left: auto;
  font-size: 18px;
  color: var(--text-tertiary);
}
.detail-question {
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.75;
  color: var(--text-color);
  white-space: pre-wrap;
}
.detail-image {
  display: block;
  max-width: 100%;
  max-height: 240px;
  margin: 12px auto 0;
  border-radius: 10px;
  object-fit: contain;
}
.detail-options {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.detail-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--card-bg-sub);
  border: 1px solid var(--border-color);
}
.detail-option.correct {
  background: rgba(18, 161, 80, 0.12);
  border-color: rgba(18, 161, 80, 0.5);
}
.detail-letter {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  border-radius: 50%;
  background: var(--card-bg);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}
.detail-option.correct .detail-letter {
  background: var(--success);
  color: #fff;
}
.detail-option-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-color);
}
.detail-ok {
  color: var(--success);
  font-size: 18px;
}
.detail-answer {
  margin-top: 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--success);
}
.detail-analysis {
  margin-top: 14px;
  padding: 14px;
  border-radius: 10px;
  background: var(--card-bg-sub);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 6px;
}
</style>
