<template>
  <div class="page records-page">
    <van-nav-bar title="我的成绩" left-text="返回" @click-left="router.back()" />

    <div v-if="records.length" class="section first">
      <div class="card summary-card">
        <div class="sum-item">
          <b>{{ records.length }}</b>
          <span>参加次数</span>
        </div>
        <div class="sum-item">
          <b class="ok">{{ passedCount }}</b>
          <span>通过次数</span>
        </div>
        <div class="sum-item">
          <b>{{ passRate }}%</b>
          <span>通过率</span>
        </div>
      </div>
    </div>

    <div v-if="records.length" class="record-list">
      <div
        v-for="item in records"
        :key="item.id"
        class="card record-card"
        :class="{ passed: item.passed }"
      >
        <div class="record-head">
          <span class="record-title">{{ item.exam_title }}</span>
          <van-tag :type="item.passed ? 'success' : 'danger'" plain round>
            {{ item.passed ? '通过' : '未通过' }}
          </van-tag>
        </div>
        <div class="record-score">
          <span class="num">{{ item.score }}</span>
          <span class="den">/ {{ item.total_score }} 分</span>
        </div>
        <div class="record-meta">
          答对 {{ item.correct_count }} 道 · 已答 {{ item.answered_count }} 道 · {{ formatTime(item.submitted_at) }}
        </div>
      </div>
    </div>

    <van-empty v-else :description="loaded ? '还没有考试记录，去考一场吧' : '加载中...'" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { examApi } from '../api'

const router = useRouter()
const records = ref([])
const loaded = ref(false)

const passedCount = computed(() => records.value.filter(r => r.passed).length)
const passRate = computed(() => {
  if (!records.value.length) return 0
  return Math.round((passedCount.value / records.value.length) * 100)
})

const pad = (n) => String(n).padStart(2, '0')

const formatTime = (v) => {
  if (!v) return ''
  const raw = String(v)
  // 后端存的是 UTC 时间，补 Z 后按本地时区显示
  const d = new Date(raw.endsWith('Z') ? raw : raw + 'Z')
  if (Number.isNaN(d.getTime())) return raw
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const loadRecords = async () => {
  try {
    records.value = await examApi.getMyAttempts()
  } catch (error) {
    console.error('加载成绩记录失败', error)
  } finally {
    loaded.value = true
  }
}

onMounted(loadRecords)
</script>

<style scoped>
.records-page {
  padding-bottom: 30px;
}
.section.first {
  margin-top: 12px;
}
.summary-card {
  display: flex;
  padding: 16px 0;
}
.sum-item {
  flex: 1;
  text-align: center;
  position: relative;
}
.sum-item + .sum-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 1px;
  background: var(--border-color);
}
.sum-item b {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color);
}
.sum-item b.ok {
  color: var(--success);
}
.sum-item span {
  display: block;
  margin-top: 3px;
  font-size: 11px;
  color: var(--text-secondary);
}
.record-list {
  padding: 12px 14px 0;
}
.record-card {
  padding: 15px 16px;
  margin-bottom: 12px;
  border-left: 3px solid var(--danger);
}
.record-card.passed {
  border-left-color: var(--success);
}
.record-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.record-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
}
.record-score {
  margin-top: 10px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.record-score .num {
  font-size: 26px;
  font-weight: 700;
  color: var(--brand);
  font-variant-numeric: tabular-nums;
}
.record-card.passed .num {
  color: var(--success);
}
.record-score .den {
  font-size: 12px;
  color: var(--text-secondary);
}
.record-meta {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
