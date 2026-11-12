<template>
  <div class="wrong-page">
    <van-nav-bar
      title="错题本"
      left-text="返回"
      right-text="重做"
      @click-left="router.back()"
      @click-right="redoWrong"
    />

    <van-tabs v-model:active="status" @change="onFilterChange" shrink>
      <van-tab :title="`待复习 ${pendingTotal}`" name="pending" />
      <van-tab :title="`已掌握 ${masteredTotal}`" name="mastered" />
      <van-tab title="全部" name="all" />
    </van-tabs>

    <van-search
      v-model="keyword"
      placeholder="搜索题干关键词"
      shape="round"
      @update:model-value="onKeywordInput"
    />

    <div class="filter-bar">
      <div class="filter-item" :class="{ on: categoryId }" @click="openCategory">
        <span class="ellipsis">{{ categoryName }}</span>
        <van-icon name="arrow-down" size="12" />
      </div>
      <div class="filter-item" :class="{ on: type }" @click="openType">
        <span>{{ typeText }}</span>
        <van-icon name="arrow-down" size="12" />
      </div>
      <div class="filter-item" :class="{ on: source }" @click="openSource">
        <span>{{ sourceText }}</span>
        <van-icon name="records" size="12" />
      </div>
      <div class="filter-item" :class="{ on: dateStart && dateEnd }" @click="openDate">
        <span>{{ dateText }}</span>
        <van-icon name="calendar-o" size="12" />
      </div>
      <div class="filter-item" :class="{ on: sort === 'count' }" @click="toggleSort">
        <span>{{ sort === 'count' ? '错得多的在前' : '最近错的在前' }}</span>
        <van-icon name="exchange" size="12" />
      </div>
    </div>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      finished-text=""
      :immediate-check="false"
      @load="loadPage"
    >
      <div
        v-for="item in list"
        :key="item.id"
        class="wrong-card"
        @click="openDetail(item)"
      >
        <div class="card-top">
          <van-tag :type="typeTag(item.type)" size="mini" plain>{{ typeLabel(item.type) }}</van-tag>
          <span class="cat">{{ item.category_name }}</span>
          <van-tag
            v-if="item.source === 'exam'"
            type="warning"
            size="mini"
            plain
          >考试</van-tag>
          <van-tag v-else type="primary" size="mini" plain>刷题</van-tag>
          <van-tag v-if="item.mastered" type="success" size="mini">已掌握</van-tag>
          <van-tag v-else type="danger" size="mini" plain>待复习</van-tag>
          <van-icon
            :name="item.is_favorite ? 'star' : 'star-o'"
            class="fav-icon"
            :class="{ active: item.is_favorite }"
            @click.stop="toggleCardFavorite(item)"
          />
        </div>
        <div class="card-content">{{ item.content }}</div>
        <div v-if="item.exam_title" class="card-exam">来自考试：{{ item.exam_title }}</div>
        <div class="card-bottom">
          <span>错 {{ item.wrong_count }} 次</span>
          <span>{{ formatTime(item.last_wrong_time) }}</span>
          <van-icon name="arrow" size="12" />
        </div>
      </div>
    </van-list>

    <van-empty
      v-if="!list.length && finished && !loading"
      :description="emptyText"
    />

    <div v-if="total > 0" class="bottom-bar">
      <van-button type="primary" block :loading="composing" @click="openWrongCompose">
        错题组卷
      </van-button>
      <van-button plain type="primary" block :loading="starting" @click="redoWrong">
        重做这些错题（{{ Math.min(total, 20) }} 题）
      </van-button>
    </div>

    <!-- 日期筛选：只允许最近 10 天 -->
    <van-popup v-model:show="showDate" position="bottom" round class="date-popup">
      <div class="date-head">
        <span>按日期筛选</span>
        <van-icon name="cross" size="18" @click="showDate = false" />
      </div>
      <div class="date-body">
        <div class="date-quick">
          <span @click="setPreset(0)">全部</span>
          <span @click="setPreset(1)">今天</span>
          <span @click="setPreset(3)">近3天</span>
          <span @click="setPreset(7)">近7天</span>
          <span @click="setPreset(10)">近10天</span>
        </div>
        <label class="date-field">
          <span>开始日期</span>
          <input
            v-model="draftStart"
            type="date"
            :min="minDateStr"
            :max="draftEnd || maxDateStr"
          />
        </label>
        <label class="date-field">
          <span>结束日期</span>
          <input
            v-model="draftEnd"
            type="date"
            :min="draftStart || minDateStr"
            :max="maxDateStr"
          />
        </label>
        <div class="date-note">
          错题本只保留最近 10 天内的记录，超过 10 天的错题会自动从数据库移除。
        </div>
        <van-button type="primary" block round @click="applyDate">确定</van-button>
        <van-button plain block round class="date-clear" @click="clearDate">清除日期</van-button>
      </div>
    </van-popup>

    <!-- 分类筛选 -->
    <van-popup v-model:show="showCategory" position="bottom" round>
      <div class="popup-title">按分类筛选</div>
      <div class="cat-list">
        <div class="cat-row all" :class="{ active: !categoryId }" @click="pickCategory(0, '全部分类')">
          全部分类
        </div>
        <template v-for="group in categoryGroups" :key="group.id">
          <div class="cat-group-title">{{ group.name }}</div>
          <div
            class="cat-row"
            :class="{ active: categoryId === group.id }"
            @click="pickCategory(group.id, group.name + '（全部模块）')"
          >
            {{ group.name }}（全部模块）
          </div>
          <div
            v-for="child in group.children"
            :key="child.id"
            class="cat-row child"
            :class="{ active: categoryId === child.id }"
            @click="pickCategory(child.id, child.name)"
          >
            {{ child.name }}
          </div>
        </template>
      </div>
    </van-popup>

    <!-- 题型筛选 -->
    <van-popup v-model:show="showType" position="bottom" round>
      <div class="popup-title">按题型筛选</div>
      <van-cell
        v-for="opt in typeOptions"
        :key="opt.value"
        :title="opt.text"
        clickable
        :class="{ 'type-active': type === opt.value }"
        @click="pickType(opt)"
      />
    </van-popup>

    <!-- 来源筛选：刷题错题 / 考试错题 -->
    <van-popup v-model:show="showSource" position="bottom" round>
      <div class="popup-title">按错题来源筛选</div>
      <van-cell
        v-for="opt in sourceOptions"
        :key="opt.value"
        :title="opt.text"
        clickable
        :class="{ 'type-active': source === opt.value }"
        @click="pickSource(opt)"
      />
    </van-popup>

    <!-- 错题详情 -->
    <van-popup v-model:show="showDetail" position="bottom" round class="detail-popup">
      <div class="detail-head">
        <span>错题详情</span>
        <van-icon name="cross" size="18" @click="showDetail = false" />
      </div>
      <div v-if="detail" class="detail-body">
        <div class="detail-meta">
          <van-tag :type="typeTag(detail.type)" size="mini" plain>{{ typeLabel(detail.type) }}</van-tag>
          <van-tag v-if="detail.source === 'exam'" type="warning" size="mini" plain>考试错题</van-tag>
          <van-tag v-else type="primary" size="mini" plain>刷题错题</van-tag>
          <span>{{ detail.category_name }}</span>
          <span>错 {{ detail.wrong_count }} 次</span>
          <van-tag v-if="detail.mastered" type="success" size="mini">已掌握</van-tag>
        </div>
        <div v-if="detail.exam_title" class="detail-exam">来自考试：{{ detail.exam_title }}</div>
        <div class="detail-content">{{ detail.content }}</div>
        <img
          v-if="detail.image"
          :src="detail.image"
          alt="题目图片"
          class="detail-image"
          @click="previewDetailImage"
        />
        <div class="detail-options">
          <div
            v-for="opt in detail.options"
            :key="opt.id"
            class="opt"
            :class="{ correct: opt.is_correct, mine: !opt.is_correct && isMine(opt.label) }"
          >
            <span class="opt-label">{{ opt.label }}</span>
            <span class="opt-content">{{ opt.content }}</span>
            <van-tag v-if="opt.is_correct" type="success" size="mini">正确答案</van-tag>
            <van-tag v-else-if="isMine(opt.label)" type="danger" size="mini">你选了</van-tag>
          </div>
        </div>
        <div class="answer-line">
          正确答案：<b>{{ detail.correct_answer }}</b>
          <span v-if="detail.last_answer">（上次你答 {{ detail.last_answer }}）</span>
        </div>
        <div v-if="detail.analysis" class="analysis">
          <div class="analysis-title">解析</div>
          <div>{{ detail.analysis }}</div>
        </div>
      </div>
      <div class="detail-actions">
        <van-button
          :type="detail?.is_favorite ? 'warning' : 'default'"
          plain
          @click="toggleDetailFavorite"
        >
          {{ detail?.is_favorite ? '已收藏' : '收藏' }}
        </van-button>
        <van-button v-if="detail && !detail.mastered" type="success" plain @click="markMastered">
          标记已掌握
        </van-button>
        <van-button type="danger" plain @click="removeWrong">移出错题本</van-button>
      </div>
    </van-popup>

    <!-- 错题组卷：先选题量、分值和时长 -->
    <van-popup v-model:show="showCompose" position="bottom" round class="compose-popup">
      <div class="compose-head">
        <span>错题组卷</span>
        <van-icon name="cross" size="18" @click="showCompose = false" />
      </div>
      <div class="compose-body">
        <div class="compose-summary">
          当前筛选下共 <b>{{ total }}</b> 道错题，最多可组 <b>{{ composeMax }}</b> 道。
        </div>
        <div class="compose-row">
          <div>
            <div class="compose-label">题目数量</div>
            <div class="compose-hint">按当前筛选条件抽取</div>
          </div>
          <van-stepper v-model="composeForm.count" :min="1" :max="composeMax" integer />
        </div>
        <div class="compose-row">
          <div>
            <div class="compose-label">每题分值</div>
            <div class="compose-hint">0.5～10 分</div>
          </div>
          <van-stepper v-model="composeForm.score" :min="0.5" :max="10" :step="0.5" :decimal-length="1" />
        </div>
        <div class="compose-row">
          <div>
            <div class="compose-label">考试时长</div>
            <div class="compose-hint">5～180 分钟</div>
          </div>
          <van-stepper v-model="composeForm.duration" :min="5" :max="180" :step="5" integer />
        </div>
        <div class="compose-total">
          共 <b>{{ composeForm.count }}</b> 题 · 满分 <b>{{ composeScore }}</b> 分 · 及格 <b>{{ composePass }}</b> 分
        </div>
        <van-button
          type="primary"
          round
          block
          :loading="composing"
          @click="submitWrongCompose"
        >
          生成错题卷并开始
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog, showImagePreview } from 'vant'
import { practiceApi, questionApi, examApi } from '../api'

const router = useRouter()
const route = useRoute()

const status = ref('pending')
const categoryId = ref(0)
const categoryName = ref('全部分类')
const type = ref('')
const source = ref(route.query.source === 'exam' ? 'exam' : '')
const sort = ref('recent')
const keyword = ref('')
const dateStart = ref('')
const dateEnd = ref('')
const draftStart = ref('')
const draftEnd = ref('')
const showDate = ref(false)

const list = ref([])
const total = ref(0)
const pendingTotal = ref(0)
const masteredTotal = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const finished = ref(false)

const showCategory = ref(false)
const showType = ref(false)
const showSource = ref(false)
const showDetail = ref(false)
const detail = ref(null)

const previewDetailImage = () => {
  if (!detail.value?.image) return
  showImagePreview({ images: [detail.value.image], closeable: true })
}
const starting = ref(false)
const composing = ref(false)
const showCompose = ref(false)
const composeForm = ref({ count: 10, score: 1, duration: 30 })
const composeMax = computed(() => Math.min(total.value, 50))
const composeScore = computed(() => {
  const value = Number(composeForm.value.count || 0) * Number(composeForm.value.score || 0)
  return Number(value.toFixed(1))
})
const composePass = computed(() => Number((composeScore.value * 0.6).toFixed(1)))

const categoryGroups = ref([])

const typeOptions = [
  { text: '全部题型', value: '' },
  { text: '单选题', value: 'single' },
  { text: '多选题', value: 'multiple' },
  { text: '判断题', value: 'judge' }
]

const typeText = computed(() => typeOptions.find(o => o.value === type.value)?.text || '全部题型')

const sourceOptions = [
  { text: '全部来源', value: '' },
  { text: '刷题错题', value: 'practice' },
  { text: '考试错题', value: 'exam' }
]

const sourceText = computed(() => sourceOptions.find(o => o.value === source.value)?.text || '全部来源')

const emptyText = computed(() => {
  if (dateStart.value && dateEnd.value) return '这个日期范围内没有错题'
  if (status.value === 'mastered') return '还没有已掌握的题目'
  if (categoryId.value || type.value) return '这个筛选条件下没有错题'
  return '错题本还是空的，去刷题吧'
})

const typeLabel = (t) => ({ single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题' }[t] || t)
const typeTag = (t) => ({ single: 'primary', multiple: 'warning', judge: 'success' }[t] || 'default')

const pad = (n) => String(n).padStart(2, '0')
const toDateStr = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const todayDate = new Date()
todayDate.setHours(0, 0, 0, 0)
const maxDateStr = toDateStr(todayDate)
const minDate = new Date(todayDate)
minDate.setDate(minDate.getDate() - 9)
const minDateStr = toDateStr(minDate)

const dateText = computed(() => {
  if (!dateStart.value || !dateEnd.value) return '全部日期'
  return `${dateStart.value.slice(5)} ~ ${dateEnd.value.slice(5)}`
})

const dateQuery = computed(() => {
  if (!dateStart.value || !dateEnd.value) return {}
  return { start_date: dateStart.value, end_date: dateEnd.value }
})

const openDate = () => {
  draftStart.value = dateStart.value
  draftEnd.value = dateEnd.value
  showDate.value = true
}

const setPreset = (days) => {
  if (!days) {
    draftStart.value = ''
    draftEnd.value = ''
    return
  }
  const end = new Date(todayDate)
  const start = new Date(todayDate)
  start.setDate(start.getDate() - (days - 1))
  draftStart.value = toDateStr(start)
  draftEnd.value = toDateStr(end)
}

const applyDate = () => {
  if (!draftStart.value || !draftEnd.value) {
    showToast('请选择完整的开始和结束日期')
    return
  }
  if (draftStart.value > draftEnd.value) {
    showToast('开始日期不能晚于结束日期')
    return
  }
  const start = new Date(draftStart.value + 'T00:00:00')
  const end = new Date(draftEnd.value + 'T00:00:00')
  const days = Math.round((end - start) / 86400000) + 1
  if (days > 10) {
    showToast('最多只能筛选最近 10 天')
    return
  }
  dateStart.value = draftStart.value
  dateEnd.value = draftEnd.value
  showDate.value = false
  reload()
}

const clearDate = () => {
  dateStart.value = ''
  dateEnd.value = ''
  draftStart.value = ''
  draftEnd.value = ''
  showDate.value = false
  reload()
}

const formatTime = (v) => {
  if (!v) return ''
  const raw = String(v)
  const d = new Date(raw.endsWith('Z') ? raw : raw + 'Z')
  if (Number.isNaN(d.getTime())) return raw
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const isMine = (label) => {
  const mine = (detail.value?.last_answer || '').toUpperCase()
  return mine.includes(String(label).toUpperCase())
}

const loadPage = async () => {
  loading.value = true
  try {
    const res = await practiceApi.getWrongList({
      page: page.value,
      page_size: pageSize,
      status: status.value,
      sort: sort.value,
      category_id: categoryId.value || undefined,
      type: type.value || undefined,
      source: source.value || undefined,
      keyword: keyword.value.trim() || undefined,
      ...dateQuery.value
    })
    if (page.value === 1) list.value = []
    list.value = list.value.concat(res.items)
    total.value = res.total
    pendingTotal.value = res.pending_total
    masteredTotal.value = res.mastered_total
    finished.value = list.value.length >= res.total
    if (!finished.value) page.value += 1
  } catch (error) {
    showToast('加载错题失败')
    finished.value = true
  } finally {
    loading.value = false
  }
}

const reload = () => {
  page.value = 1
  finished.value = false
  loading.value = true
  loadPage()
}

const onFilterChange = () => {
  reload()
}

let searchTimer = null
const onKeywordInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    reload()
  }, 500)
}

const openCategory = () => {
  showCategory.value = true
}
const openType = () => {
  showType.value = true
}
const openSource = () => {
  showSource.value = true
}
const toggleSort = () => {
  sort.value = sort.value === 'count' ? 'recent' : 'count'
  reload()
}

const pickCategory = (id, name) => {
  categoryId.value = id
  categoryName.value = name
  showCategory.value = false
  reload()
}

const pickType = (opt) => {
  type.value = opt.value
  showType.value = false
  reload()
}

const pickSource = (opt) => {
  source.value = opt.value
  showSource.value = false
  reload()
}

const openDetail = async (item) => {
  try {
    detail.value = await practiceApi.getWrongDetail(item.question_id)
    showDetail.value = true
  } catch (error) {
    showToast('加载详情失败')
  }
}

const toggleCardFavorite = async (item) => {
  const next = !item.is_favorite
  item.is_favorite = next
  try {
    await practiceApi.saveMark(item.question_id, { is_favorite: next })
    if (detail.value && detail.value.question_id === item.question_id) {
      detail.value.is_favorite = next
    }
    showToast(next ? '已加入收藏' : '已取消收藏')
  } catch (error) {
    item.is_favorite = !next
    showToast('收藏操作失败')
  }
}

const toggleDetailFavorite = async () => {
  if (!detail.value) return
  const next = !detail.value.is_favorite
  try {
    await practiceApi.saveMark(detail.value.question_id, { is_favorite: next })
    detail.value.is_favorite = next
    const row = list.value.find(x => x.question_id === detail.value.question_id)
    if (row) row.is_favorite = next
    showToast(next ? '已加入收藏，可在收藏夹组卷' : '已取消收藏')
  } catch (error) {
    showToast('收藏操作失败')
  }
}

const markMastered = async () => {
  try {
    await practiceApi.markMastered(detail.value.id)
    showDetail.value = false
    showToast('已标记为掌握')
    reload()
  } catch (error) {
    showToast('操作失败')
  }
}

const removeWrong = async () => {
  try {
    await showConfirmDialog({
      title: '移出错题本',
      message: '这道题将从错题本中移除，确定吗？',
      confirmButtonText: '移出',
      cancelButtonText: '取消'
    })
  } catch (e) {
    return
  }
  try {
    await practiceApi.deleteWrong(detail.value.id)
    showDetail.value = false
    showToast('已移出错题本')
    reload()
  } catch (error) {
    showToast('操作失败')
  }
}

const redoWrong = () => {
  if (starting.value) return
  if (!total.value) {
    showToast('当前没有可重做的错题')
    return
  }
  starting.value = true
  const query = {
    source: 'wrong',
    wrong_source: source.value || undefined,
    category: categoryId.value || 0,
    type: type.value || '',
    status: status.value,
    sort: sort.value,
    ...dateQuery.value
  }
  router.push({ path: '/practice/start', query })
  setTimeout(() => { starting.value = false }, 800)
}

const openWrongCompose = () => {
  if (composing.value) return
  if (!total.value) {
    showToast('当前没有可组卷的错题')
    return
  }
  composeForm.value.count = Math.min(10, composeMax.value)
  showCompose.value = true
}

const submitWrongCompose = async () => {
  if (composing.value) return
  if (!total.value) {
    showToast('当前没有可组卷的错题')
    return
  }
  const count = Math.min(Math.max(Number(composeForm.value.count || 0), 1), composeMax.value)
  if (count < 1) {
    showToast('请设置题目数量')
    return
  }
  composing.value = true
  try {
    const exam = await examApi.createSelfExam({
      source: 'wrong',
      category_id: categoryId.value || undefined,
      wrong_type: type.value || undefined,
      wrong_status: status.value,
      wrong_sort: sort.value,
      wrong_source: source.value || undefined,
      count,
      score: Number(composeForm.value.score || 1),
      duration: Number(composeForm.value.duration || 30),
      ...dateQuery.value
    })
    showCompose.value = false
    showToast('错题卷已生成')
    router.push('/exam/start?id=' + exam.id)
  } catch (error) {
    showToast(error.response?.data?.detail || '组卷失败')
  } finally {
    composing.value = false
  }
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
    categoryGroups.value = roots
      .filter(root => (byParent[root.id] || []).length || root.question_count)
      .map(root => ({ id: root.id, name: root.name, children: byParent[root.id] || [] }))
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

onMounted(() => {
  loadCategories()
  reload()
})
</script>

<style scoped>
.wrong-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 200px;
}
.filter-bar {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  background: var(--card-bg);
  overflow-x: auto;
  white-space: nowrap;
  border-bottom: 1px solid var(--border-color);
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 11px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--card-bg-sub);
  border-radius: 14px;
  max-width: 45%;
}
.filter-item.on {
  color: var(--brand);
  background: var(--brand-light);
}
.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 日期筛选 */
.date-popup {
  overflow: hidden;
}
.date-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}
.date-body {
  padding: 4px 16px calc(18px + env(safe-area-inset-bottom));
}
.date-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 6px 0 16px;
}
.date-quick span {
  padding: 6px 12px;
  border-radius: 15px;
  background: var(--card-bg-sub);
  color: var(--text-secondary);
  font-size: 12px;
}
.date-quick span:active {
  background: var(--brand-light);
  color: var(--brand);
}
.date-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-color);
}
.date-field input {
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-color);
  font-size: 14px;
  text-align: right;
}
.date-note {
  margin: 14px 0 16px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--card-bg-sub);
  color: var(--text-tertiary);
  font-size: 11px;
  line-height: 1.6;
}
.date-clear {
  margin-top: 10px;
}
.wrong-card {
  background: var(--card-bg);
  margin: 10px 12px;
  border-radius: var(--radius-lg);
  padding: 13px 15px;
  box-shadow: var(--shadow-card);
}
.card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
.card-top .cat {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fav-icon {
  flex: none;
  margin-left: 4px;
  font-size: 19px;
  color: var(--text-tertiary);
  padding: 2px;
}
.fav-icon.active {
  color: #ffb300;
}
.card-exam {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-content {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-color);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-bottom {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.card-bottom .van-icon {
  margin-left: auto;
}
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 50px;
  padding: 10px 16px;
  background: var(--card-bg);
  box-shadow: 0 -4px 16px rgba(16, 44, 85, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.popup-title {
  padding: 16px;
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  color: var(--text-color);
}
.cat-list {
  max-height: 60vh;
  overflow-y: auto;
  padding-bottom: 16px;
}
.cat-row {
  padding: 12px 20px;
  font-size: 14px;
  color: var(--text-color);
}
.cat-row.child {
  padding-left: 34px;
  color: var(--text-secondary);
  font-size: 13px;
}
.cat-row.active {
  color: var(--brand);
  font-weight: 600;
}
.cat-group-title {
  padding: 12px 20px 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
.type-active {
  color: var(--brand);
  font-weight: 600;
}
.detail-popup {
  height: 82vh;
  display: flex;
  flex-direction: column;
}
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  font-size: 15px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
.detail-content {
  margin: 12px 0;
  font-size: 15px;
  line-height: 1.65;
  color: var(--text-color);
}
.detail-exam {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.detail-image {
  display: block;
  max-width: 100%;
  max-height: 220px;
  margin: 0 auto 12px;
  border-radius: 10px;
  object-fit: contain;
  background: var(--bg-page, #f7f8fa);
}
.detail-options .opt {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 11px 12px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.5;
  background: var(--card-bg);
}
.detail-options .opt.correct {
  border-color: var(--success);
  background: rgba(18, 161, 80, 0.08);
}
.detail-options .opt.mine {
  border-color: var(--danger);
  background: rgba(229, 72, 77, 0.08);
}
.opt-label {
  font-weight: 600;
  color: var(--text-color);
}
.opt-content {
  flex: 1;
  color: var(--text-color);
}
.answer-line {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.answer-line b {
  color: var(--success);
}
.analysis {
  margin-top: 14px;
  padding: 12px;
  background: var(--card-bg-sub);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-secondary);
}
.analysis-title {
  margin-bottom: 6px;
  font-weight: 600;
  color: var(--text-color);
}
.detail-actions {
  display: flex;
  gap: 12px;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--border-color);
}
.detail-actions .van-button {
  flex: 1;
}

/* 错题组卷 */
.compose-popup {
  overflow: hidden;
}
.compose-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}
.compose-body {
  padding: 4px 16px calc(18px + env(safe-area-inset-bottom));
}
.compose-summary {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--card-bg-sub);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}
.compose-summary b {
  color: var(--brand);
}
.compose-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}
.compose-label {
  font-size: 14px;
  color: var(--text-color);
}
.compose-hint {
  margin-top: 3px;
  font-size: 11px;
  color: var(--text-tertiary);
}
.compose-total {
  padding: 14px 0 16px;
  color: var(--text-secondary);
  font-size: 13px;
}
.compose-total b {
  color: var(--danger);
}

/* 夜间模式：提高错题筛选、日期和组卷弹窗的可读性 */
.dark-mode .date-field input {
  color-scheme: dark;
}
.dark-mode .date-field input::-webkit-calendar-picker-indicator {
  filter: invert(1);
  opacity: 0.85;
}
.dark-mode .filter-item {
  color: var(--text-secondary);
}
.dark-mode .filter-item.on {
  color: var(--brand);
}
.dark-mode .card-bottom,
.dark-mode .date-note,
.dark-mode .compose-hint {
  color: var(--text-tertiary);
}
.dark-mode .compose-total {
  color: var(--text-secondary);
}
.dark-mode .compose-total b {
  color: #ff9a9e;
}
.dark-mode .date-quick span {
  color: var(--text-secondary);
  background: var(--card-bg-sub);
}
.dark-mode .date-quick span:active {
  color: var(--brand);
  background: var(--brand-light);
}
</style>
