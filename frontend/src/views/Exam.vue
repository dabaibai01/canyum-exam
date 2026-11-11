<template>
  <div class="page exam-page">
    <van-nav-bar
      title="在线考试"
      left-text="返回"
      right-text="我的成绩"
      @click-left="router.back()"
      @click-right="goRecords"
    />

    <div class="self-entry">
      <div class="card self-card">
        <div class="self-main">
          <div class="self-title">自己组卷自测</div>
          <div class="self-sub">按专业和题型出题，提交后计入「我的成绩」</div>
        </div>
        <van-button size="small" type="primary" round @click="openCompose">开始组卷</van-button>
      </div>
    </div>

    <div v-if="exams.length" class="exam-list">
      <div
        v-for="exam in exams"
        :key="exam.id"
        class="card exam-card"
        :class="{ passed: exam.passed, failed: exam.used > 0 && !exam.passed }"
      >
        <div class="exam-head">
          <div class="exam-title">{{ exam.title }}</div>
          <van-tag
            v-if="exam.used > 0"
            :type="exam.passed ? 'success' : 'danger'"
            plain
            round
          >
            {{ exam.passed ? '已通过' : '未通过' }} · 最高 {{ exam.best_score }} 分
          </van-tag>
          <van-tag v-else type="primary" plain round>未参加</van-tag>
        </div>

        <div class="exam-meta">
          <span class="chip">{{ exam.question_count }} 道题</span>
          <span class="chip">总分 {{ exam.total_score }}</span>
          <span class="chip">及格 {{ exam.pass_score }}</span>
          <span class="chip">{{ exam.duration }} 分钟</span>
        </div>

        <div class="exam-foot">
          <span class="exam-rule">{{ retakeText(exam) }}</span>
          <van-button
            round
            size="small"
            :type="exam.can_take ? 'primary' : 'default'"
            :disabled="!exam.can_take || !exam.question_count"
            @click="enter(exam)"
          >
            {{ exam.can_take ? (exam.used > 0 ? '再考一次' : '进入考试') : '已考完' }}
          </van-button>
        </div>
      </div>
    </div>

    <van-empty v-else :description="loaded ? '暂无进行中的考试' : '加载中...'" />

    <!-- 自测组卷 -->
    <van-popup v-model:show="showCompose" position="bottom" round class="compose-popup">
      <div class="compose-head">
        <span>自己组卷自测</span>
        <van-icon name="cross" size="18" @click="showCompose = false" />
      </div>
      <div class="compose-body">
        <div class="field-label">选择专业 / 模块</div>
        <van-field
          v-model="composeCategoryName"
          is-link
          readonly
          placeholder="选择分类"
          @click="showCategoryPicker = true"
        />
        <div class="available-tip">
          可用题量：单选 {{ available.single || 0 }} · 多选 {{ available.multiple || 0 }} · 判断 {{ available.judge || 0 }}
        </div>

        <div v-for="item in composeTypes" :key="item.key" class="count-row">
          <div class="count-main">
            <div class="count-title">{{ item.label }}</div>
            <div class="count-sub">每题 1 分</div>
          </div>
          <van-stepper
            v-model="composeForm[item.key]"
            :min="0"
            :max="available[item.key] || 0"
            integer
          />
        </div>

        <div class="compose-total">
          合计 <b>{{ composeTotal }}</b> 题，满分 {{ composeTotal }} 分
        </div>
        <van-button
          type="primary"
          round
          block
          :loading="creating"
          :disabled="composeTotal <= 0"
          @click="createSelfExam"
        >
          生成自测卷
        </van-button>
      </div>
    </van-popup>

    <van-popup v-model:show="showCategoryPicker" position="bottom" round class="category-popup">
      <div class="compose-head">
        <span>选择专业 / 模块</span>
        <van-icon name="cross" size="18" @click="showCategoryPicker = false" />
      </div>
      <div class="category-list">
        <div class="category-row" :class="{ active: composeForm.category_id === 0 }" @click="pickCategory({ id: 0, name: '全部题目' })">
          全部题目
        </div>
        <template v-for="group in categoryGroups" :key="group.id">
          <div class="category-group">{{ group.name }}</div>
          <div
            class="category-row parent"
            :class="{ active: composeForm.category_id === group.id }"
            @click="pickCategory({ id: group.id, name: group.name + '（全部模块）' })"
          >
            {{ group.name }}（全部模块）
          </div>
          <div
            v-for="child in group.children"
            :key="child.id"
            class="category-row child"
            :class="{ active: composeForm.category_id === child.id }"
            @click="pickCategory(child)"
          >
            {{ child.name }}
          </div>
        </template>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { examApi, questionApi } from '../api'

const router = useRouter()
const exams = ref([])
const loaded = ref(false)

const showCompose = ref(false)
const showCategoryPicker = ref(false)
const creating = ref(false)
const composeCategoryName = ref('全部题目')
const categories = ref([])
const available = ref({ single: 0, multiple: 0, judge: 0, total: 0 })
const composeForm = ref({ category_id: 0, single: 0, multiple: 0, judge: 0 })
const composeTypes = [
  { key: 'single', label: '单选题' },
  { key: 'multiple', label: '多选题' },
  { key: 'judge', label: '判断题' }
]
const composeTotal = computed(() =>
  Number(composeForm.value.single || 0) + Number(composeForm.value.multiple || 0) + Number(composeForm.value.judge || 0)
)
const categoryGroups = computed(() => {
  const roots = categories.value.filter(c => !c.parent_id || c.parent_id === 0)
  return roots
    .map(parent => ({
      id: parent.id,
      name: parent.name,
      children: categories.value.filter(c => c.parent_id === parent.id)
    }))
    .filter(group => group.children.length > 0 || (categories.value.find(c => c.id === group.id)?.question_count || 0) > 0)
})

const loadExams = async () => {
  try {
    exams.value = await examApi.getMyExams({ status: 1 })
  } catch (error) {
    console.error('加载考试列表失败', error)
  } finally {
    loaded.value = true
  }
}

const loadCategories = async () => {
  try {
    categories.value = await questionApi.getCategories('question')
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadAvailable = async (categoryId) => {
  try {
    available.value = await examApi.getAvailableQuestions(categoryId || 0)
  } catch (error) {
    available.value = { single: 0, multiple: 0, judge: 0, total: 0 }
    showToast('加载可用题量失败')
  }
}

const applyDefaults = () => {
  const single = Math.min(10, available.value.single || 0)
  const multiple = single === 0 ? Math.min(10, available.value.multiple || 0) : 0
  composeForm.value.single = single
  composeForm.value.multiple = multiple
  composeForm.value.judge = Math.min(5, available.value.judge || 0)
}

const openCompose = async () => {
  if (!categories.value.length) await loadCategories()
  await loadAvailable(composeForm.value.category_id || 0)
  if (composeTotal.value === 0) applyDefaults()
  showCompose.value = true
}

const pickCategory = async (cat) => {
  composeForm.value.category_id = cat.id
  composeCategoryName.value = cat.name
  showCategoryPicker.value = false
  await loadAvailable(cat.id)
  applyDefaults()
}

const createSelfExam = async () => {
  const compose = composeTypes
    .filter(item => Number(composeForm.value[item.key] || 0) > 0)
    .map(item => ({ type: item.key, count: Number(composeForm.value[item.key]) }))
  if (!compose.length) {
    showToast('请至少设置一种题型')
    return
  }
  creating.value = true
  try {
    const exam = await examApi.createSelfExam({
      source: 'bank',
      category_id: composeForm.value.category_id || 0,
      compose,
      duration: 30
    })
    showCompose.value = false
    showToast('自测卷已生成')
    router.push('/exam/start?id=' + exam.id)
  } catch (error) {
    showToast(error.response?.data?.detail || '组卷失败')
  } finally {
    creating.value = false
  }
}

const retakeText = (exam) => {
  if (!exam.allow_retake) {
    return exam.used > 0 ? '本场考试不可重考' : '每人限考 1 次'
  }
  if (!exam.retake_limit) {
    return exam.used > 0 ? `已考 ${exam.used} 次 · 不限次数` : '可不限次数重考'
  }
  if (exam.remaining === null) {
    return '可不限次数重考'
  }
  if (exam.remaining === 0) {
    return `次数已用完（共 ${1 + exam.retake_limit} 次）`
  }
  return `还可考 ${exam.remaining} 次（共 ${1 + exam.retake_limit} 次）`
}

const enter = (exam) => {
  if (!exam.can_take) {
    showToast('重考次数已用完')
    return
  }
  router.push({ path: '/exam/start', query: { id: exam.id } })
}

const goRecords = () => {
  router.push('/exam/records')
}

onMounted(() => {
  loadExams()
  loadCategories()
})
</script>

<style scoped>
.exam-page {
  padding-bottom: 90px;
}
.self-entry {
  padding: 12px 14px 0;
}
.self-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #eef5ff 0%, #f7fbff 100%);
  border: 1px solid rgba(23, 87, 156, 0.12);
}
.self-main {
  flex: 1;
  min-width: 0;
}
.self-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
}
.self-sub {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.compose-popup {
  max-height: 86vh;
  display: flex;
  flex-direction: column;
}
.compose-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
}
.compose-body {
  padding: 4px 18px 24px;
  overflow-y: auto;
}
.field-label {
  margin: 8px 0 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.available-tip {
  margin: 8px 2px 14px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-tertiary);
}
.count-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-top: 1px solid var(--border-color);
}
.count-title {
  font-size: 14px;
  color: var(--text-color);
}
.count-sub {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-tertiary);
}
.compose-total {
  margin: 12px 0 16px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--brand-light);
  font-size: 13px;
  color: var(--brand);
}
.compose-total b {
  font-size: 17px;
}
.category-popup {
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}
.category-list {
  overflow-y: auto;
  padding: 0 0 16px;
}
.category-group {
  padding: 12px 20px 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
.category-row {
  padding: 12px 20px;
  font-size: 14px;
  color: var(--text-color);
}
.category-row.child {
  padding-left: 36px;
  font-size: 13px;
  color: var(--text-secondary);
}
.category-row.active {
  color: var(--brand);
  font-weight: 600;
}
.exam-list {
  padding: 12px 14px;
}
.exam-card {
  position: relative;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 3px solid var(--brand);
}
.exam-card.passed {
  border-left-color: var(--success);
}
.exam-card.failed {
  border-left-color: var(--danger);
}
.exam-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.exam-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-color);
}
.exam-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.chip {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--card-bg-sub);
  border-radius: 999px;
  padding: 3px 10px;
}
.exam-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}
.exam-rule {
  font-size: 12px;
  color: var(--accent);
  line-height: 1.4;
}
</style>
