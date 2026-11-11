<template>
  <div class="page practice-page">
    <van-nav-bar title="刷题练习" />

    <!-- 练习模式 -->
    <div class="section first">
      <div class="card mode-card">
        <div class="mode-label">练习模式</div>
        <div class="seg">
          <div class="seg-item" :class="{ active: mode === 'random' }" @click="mode = 'random'">
            随机练习
          </div>
          <div class="seg-item" :class="{ active: mode === 'order' }" @click="mode = 'order'">
            顺序练习
          </div>
        </div>
        <div class="mode-tip">
          {{ mode === 'random' ? '从当前分类随机抽题，每次 10 题' : '按题目顺序练习，每次 10 题；自动记住上次位置，下次接着刷' }}
        </div>
      </div>
    </div>

    <!-- 综合练习 -->
    <div class="section">
      <div class="section-head">
        <span class="section-title">综合练习</span>
      </div>
      <div class="card list-card">
        <div class="cat-row" @click="startPractice({ id: 0, name: '全部题目' })">
          <div class="row-icon all-icon"><van-icon name="apps-o" size="18" /></div>
          <div class="row-main">
            <div class="row-title">全部题目</div>
            <div class="row-sub">{{ resumeHint(0) || '覆盖全部专业与模块' }}</div>
          </div>
          <div class="row-count">{{ totalCount }} 题</div>
          <van-icon name="arrow" class="row-arrow" />
        </div>
        <div class="cat-row no-line" @click="router.push('/wrong')">
          <div class="row-icon wrong-icon"><van-icon name="warning-o" size="18" /></div>
          <div class="row-main">
            <div class="row-title">错题练习</div>
            <div class="row-sub">针对薄弱点专项复习</div>
          </div>
          <div class="row-count wrong-count">{{ pendingWrong }} 题</div>
          <van-icon name="arrow" class="row-arrow" />
        </div>
      </div>
    </div>

    <!-- 分类练习 -->
    <div v-for="group in groups" :key="group.id" class="section">
      <div class="section-head">
        <span class="section-title">{{ group.name }}</span>
        <span class="section-more">{{ group.count }} 题</span>
      </div>
      <div class="card list-card">
        <div
          v-for="(cat, index) in group.items"
          :key="cat.id"
          class="cat-row"
          :class="{ 'no-line': index === group.items.length - 1 }"
          @click="startPractice(cat)"
        >
          <div class="row-main single">
            <div class="row-title">{{ cat.name }}</div>
            <div v-if="resumeHint(cat.id)" class="row-sub">{{ resumeHint(cat.id) }}</div>
          </div>
          <div class="row-count">{{ cat.question_count }} 题</div>
          <van-icon name="arrow" class="row-arrow" />
        </div>
      </div>
    </div>

    <van-empty v-if="!groups.length" description="暂无题库分类" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { questionApi, practiceApi } from '../api'
import { getPracticeOffset } from '../utils/practiceProgress'

const router = useRouter()
const mode = ref('order')
const groups = ref([])
const totalCount = ref(0)
const pendingWrong = ref(0)

const resumeHint = (categoryId) => {
  if (mode.value !== 'order') return ''
  const offset = getPracticeOffset(categoryId)
  return offset > 0 ? `上次做到第 ${offset + 1} 题` : ''
}

const loadCategories = async () => {
  try {
    const res = await questionApi.getCategories('question')
    const byParent = {}
    const roots = []
    res.forEach(cat => {
      if (cat.parent_id && cat.parent_id !== 0) {
        if (!byParent[cat.parent_id]) byParent[cat.parent_id] = []
        byParent[cat.parent_id].push(cat)
      } else {
        roots.push(cat)
      }
    })

    // 有子分类的父分类单独成组；没有子分类的旧分类归到“其他分类”
    const grouped = []
    const others = []
    roots.forEach(parent => {
      const children = byParent[parent.id] || []
      if (children.length) {
        grouped.push({
          id: 'p' + parent.id,
          name: parent.name,
          count: children.reduce((sum, c) => sum + (c.question_count || 0), 0),
          items: children
        })
      } else if (parent.question_count > 0) {
        others.push(parent)
      }
    })
    if (others.length) {
      grouped.push({
        id: 'others',
        name: '其他分类',
        count: others.reduce((sum, c) => sum + (c.question_count || 0), 0),
        items: others
      })
    }

    groups.value = grouped
    totalCount.value = roots.reduce((sum, c) => sum + (c.question_count || 0), 0)
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadWrongCount = async () => {
  try {
    const res = await practiceApi.getWrongList({ page: 1, page_size: 1, status: 'pending' })
    pendingWrong.value = res.pending_total || 0
  } catch (error) {
    console.error('加载错题数失败', error)
  }
}

const startPractice = (cat) => {
  if (!cat) return
  const total = cat.id === 0 ? totalCount.value : (cat.question_count || 0)
  const params = new URLSearchParams({
    category: String(cat.id),
    mode: mode.value,
    total: String(total || 0)
  })
  if (mode.value === 'order') {
    const offset = getPracticeOffset(cat.id)
    if (offset > 0) params.set('offset', String(offset))
  }
  router.push('/practice/start?' + params.toString())
}

onMounted(() => {
  loadCategories()
  loadWrongCount()
})
</script>

<style scoped>
.practice-page {
  padding-bottom: 90px;
}
.section.first {
  margin-top: 12px;
}

/* 模式卡 */
.mode-card {
  padding: 14px 16px;
}
.mode-label {
  font-size: 13px;
  color: var(--text-secondary);
}
.seg {
  margin-top: 10px;
  display: flex;
  background: var(--card-bg-sub);
  border-radius: 10px;
  padding: 4px;
}
.seg-item {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}
.seg-item.active {
  background: var(--card-bg);
  color: var(--brand);
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(16, 44, 85, 0.08);
}
.mode-tip {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 列表卡 */
.list-card {
  padding: 2px 0;
}
.cat-row {
  display: flex;
  align-items: center;
  padding: 13px 16px;
  position: relative;
  cursor: pointer;
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
.row-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}
.all-icon {
  background: var(--brand-light);
  color: var(--brand);
}
.wrong-icon {
  background: rgba(217, 134, 0, 0.12);
  color: var(--accent);
}
.row-main {
  flex: 1;
  min-width: 0;
}
.row-title {
  font-size: 14px;
  color: var(--text-color);
}
.row-sub {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-tertiary);
}
.row-count {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 999px;
  padding: 2px 8px;
  margin-left: 8px;
  white-space: nowrap;
}
.wrong-count {
  color: var(--accent);
  background: rgba(217, 134, 0, 0.1);
}
.row-arrow {
  color: var(--text-tertiary);
  font-size: 12px;
  margin-left: 6px;
}
</style>
