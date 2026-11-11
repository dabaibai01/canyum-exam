<template>
  <div class="page practice-start-page">
    <van-nav-bar
      :title="isWrong ? '错题重做' : '答题中'"
      left-text="返回"
      right-text="换一批"
      @click-left="goBack"
      @click-right="nextBatch"
    />

    <div v-if="finished" class="finish-panel">
      <div class="finish-card card">
        <div class="finish-icon"><van-icon name="checked" size="30" /></div>
        <div class="finish-title">本组已完成</div>
        <div class="finish-desc">
          已答 <b>{{ doneCount }}</b> 题，答对 <b class="ok">{{ correctCount }}</b> 题
        </div>
        <div class="finish-actions">
          <van-button type="primary" round block :loading="loadingBatch" @click="nextBatch">
            继续练习
          </van-button>
          <van-button plain round block @click="goBack">返回</van-button>
        </div>
        <div class="finish-tip">每次 10 题，答完可继续往下</div>
      </div>
    </div>

    <div v-else-if="currentQuestion" class="question-container">
      <div class="progress-row">
        <div class="progress-pill">
          <b>{{ progressIndex }}</b><span>/ {{ progressTotal }}</span>
        </div>
        <div v-if="doneCount > 0" class="progress-total">累计已答 {{ doneCount }} 题</div>
      </div>

      <div class="question-card card">
        <div class="question-type">
          <span class="type-pill">{{ questionTypeText(currentQuestion.type) }}</span>
          <span class="score-pill">{{ currentQuestion.score }} 分</span>
        </div>
        <div class="question-content">{{ currentQuestion.content }}</div>
        <img
          v-if="currentQuestion.image"
          :src="currentQuestion.image"
          alt="题目图片"
          class="question-image"
          @click="previewQuestionImage"
        />
      </div>

      <div class="options">
        <div
          v-for="option in currentQuestion.options"
          :key="option.id"
          class="option"
          :class="{ selected: isSelected(option) }"
          @click="selectOption(option)"
        >
          <div class="option-letter">{{ option.label }}</div>
          <div class="option-text">{{ option.content }}</div>
          <van-icon
            v-if="isSelected(option)"
            name="success"
            class="option-check"
          />
        </div>
      </div>

      <div v-if="isMultiple && !showResult" class="multi-hint">
        多选题：可选择多个选项，选完再点提交
      </div>

      <div v-if="showResult" class="result-panel">
        <div class="result-banner" :class="isCorrect ? 'ok' : 'no'">
          <van-icon :name="isCorrect ? 'checked' : 'cross'" size="18" />
          <span>{{ isCorrect ? '回答正确' : '回答错误' }}</span>
          <span class="answer-text">正确答案 {{ formatAnswer(correctAnswer) }}</span>
        </div>
        <div v-if="isWrong && isCorrect" class="result-sub">
          答对了，这道题已自动移出「待复习」
        </div>
        <div v-if="currentQuestion.analysis" class="analysis-card card">
          <div class="analysis-title">答案解析</div>
          <div class="analysis-text">{{ currentQuestion.analysis }}</div>
        </div>
      </div>

      <div class="action-buttons">
        <van-button
          v-if="!showResult"
          type="primary"
          round
          block
          :disabled="selected.length === 0"
          @click="submitAnswer"
        >
          提交答案
        </van-button>
        <van-button v-else type="primary" round block @click="nextQuestion">
          {{ currentIndex === questions.length - 1 ? '完成' : '下一题' }}
        </van-button>
      </div>
    </div>

    <van-empty v-else :description="loaded ? '这个分类下暂时没有题目' : '加载中...'" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showImagePreview } from 'vant'
import { questionApi, practiceApi } from '../api'
import { getPracticeOffset, savePracticeOffset } from '../utils/practiceProgress'

const route = useRoute()
const router = useRouter()

const questions = ref([])
const currentIndex = ref(0)
const currentQuestion = ref(null)

const previewQuestionImage = () => {
  if (!currentQuestion.value?.image) return
  showImagePreview({ images: [currentQuestion.value.image], closeable: true })
}
// 已选中的选项标签数组（单选/判断题只会有 1 个，多选题可有多个）
const selected = ref([])
const showResult = ref(false)
const isCorrect = ref(false)
const correctAnswer = ref('')
const loaded = ref(false)
// 本组题目做完后进入完成页，可继续下一组
const finished = ref(false)
const loadingBatch = ref(false)
const doneCount = ref(0)
const correctCount = ref(0)
const currentCategory = route.query.category || 0
const mode = route.query.mode || 'order'
const totalQuestions = Number(route.query.total || 0)
const requestedOffset = Number(route.query.offset || 0) || getPracticeOffset(currentCategory)
const initialOffset = totalQuestions > 0 && requestedOffset >= totalQuestions ? 0 : requestedOffset

// 顺序练习时已做过的题目数，用于取下一批
const offset = ref(initialOffset)
// 随机练习时记录本会话出现过的题目，尽量避免重复
const seenIds = ref([])

// 来源为错题本时，按错题筛选条件取题
const isWrong = route.query.source === 'wrong'
const wrongFilter = {
  category_id: route.query.category || 0,
  type: route.query.type || '',
  status: route.query.status || 'pending',
  sort: route.query.sort || 'count',
  start_date: route.query.start_date || '',
  end_date: route.query.end_date || ''
}

const isMultiple = computed(() => currentQuestion.value?.type === 'multiple')
const progressIndex = computed(() =>
  isWrong ? currentIndex.value + 1 : offset.value + currentIndex.value + 1
)
const progressTotal = computed(() => totalQuestions || questions.value.length)

const loadQuestions = async (keepStats = false) => {
  loadingBatch.value = true
  if (!keepStats) {
    doneCount.value = 0
    correctCount.value = 0
    offset.value = isWrong ? 0 : initialOffset
    seenIds.value = []
  }
  finished.value = false
  try {
    let list = []
    if (isWrong) {
      list = await practiceApi.getWrongQuestions({
        category_id: wrongFilter.category_id || undefined,
        type: wrongFilter.type || undefined,
        status: wrongFilter.status,
        sort: wrongFilter.sort,
        start_date: wrongFilter.start_date || undefined,
        end_date: wrongFilter.end_date || undefined,
        count: 10,
        offset: offset.value
      })
      if (list.length === 0 && offset.value > 0) {
        // 本组错题已做完，从头再来
        offset.value = 0
        list = await practiceApi.getWrongQuestions({
          category_id: wrongFilter.category_id || undefined,
          type: wrongFilter.type || undefined,
          status: wrongFilter.status,
          sort: wrongFilter.sort,
          start_date: wrongFilter.start_date || undefined,
          end_date: wrongFilter.end_date || undefined,
          count: 10,
          offset: 0
        })
      }
      seenIds.value = list.map(q => q.id)
    } else {
      const res = await questionApi.getRandomQuestions(
        currentCategory,
        10,
        mode,
        mode === 'order' ? offset.value : 0
      )
      list = res
      if (mode !== 'order') {
        // 随机练习：过滤掉本轮已出现过的题，尽量不重复
        list = res.filter(q => !seenIds.value.includes(q.id))
        list.forEach(q => seenIds.value.push(q.id))
      }
      if (list.length === 0 && offset.value > 0) {
        // 顺序练习已经做到末尾，回到开头
        offset.value = 0
        if (mode === 'order') savePracticeOffset(currentCategory, 0)
        const again = await questionApi.getRandomQuestions(currentCategory, 10, mode, 0)
        list = again
        again.forEach(q => { if (!seenIds.value.includes(q.id)) seenIds.value.push(q.id) })
      }
    }
    questions.value = list
    currentIndex.value = 0
    selected.value = []
    showResult.value = false
    isCorrect.value = false
    currentQuestion.value = list.length > 0 ? list[0] : null
  } catch (error) {
    showToast('加载题目失败')
  } finally {
    loaded.value = true
    loadingBatch.value = false
  }
}

// 换一批 / 继续练习：顺序练习和错题重做往后翻 10 题，随机练习重新抽一批
const nextBatch = () => {
  if (isWrong) {
    offset.value += questions.value.length
  } else if (mode === 'order') {
    let next = offset.value + questions.value.length
    if (totalQuestions > 0 && next >= totalQuestions) next = 0
    offset.value = next
    savePracticeOffset(currentCategory, offset.value)
  }
  loadQuestions(true)
}

const questionTypeText = (type) => {
  const map = {
    single: '单选题',
    multiple: '多选题',
    judge: '判断题',
    fill: '填空题'
  }
  return map[type] || type
}

const isSelected = (option) => selected.value.includes(option.label)

const selectOption = (option) => {
  if (showResult.value) return
  if (isMultiple.value) {
    const i = selected.value.indexOf(option.label)
    if (i > -1) {
      selected.value.splice(i, 1)
    } else {
      selected.value.push(option.label)
    }
  } else {
    selected.value = [option.label]
  }
}

const formatAnswer = (answer) => {
  if (!answer) return ''
  return answer.split('').join(' ')
}

const submitAnswer = async () => {
  try {
    const userAnswer = [...selected.value].sort().join('')
    const res = await practiceApi.submitAnswer({
      question_id: currentQuestion.value.id,
      user_answer: userAnswer
    })
    isCorrect.value = res.is_correct
    correctAnswer.value = res.correct_answer
    showResult.value = true
    doneCount.value++
    if (res.is_correct) correctCount.value++
    if (!isWrong && mode === 'order') {
      savePracticeOffset(currentCategory, offset.value + currentIndex.value + 1)
    }
  } catch (error) {
    showToast('提交失败')
  }
}

const nextQuestion = () => {
  if (currentIndex.value >= questions.value.length - 1) {
    finished.value = true
    if (!isWrong && mode === 'order') {
      savePracticeOffset(currentCategory, offset.value + questions.value.length)
    }
    return
  }
  currentIndex.value++
  currentQuestion.value = questions.value[currentIndex.value]
  selected.value = []
  showResult.value = false
  isCorrect.value = false
}

const persistPosition = () => {
  if (isWrong || mode !== 'order') return
  const position = finished.value
    ? offset.value + questions.value.length
    : offset.value + currentIndex.value + (showResult.value ? 1 : 0)
  savePracticeOffset(currentCategory, position)
}

const goBack = () => {
  persistPosition()
  router.back()
}

onMounted(() => {
  loadQuestions()
})

onBeforeUnmount(persistPosition)
</script>

<style scoped>
.practice-start-page {
  padding-bottom: 30px;
}
.question-container {
  padding: 14px 14px 0;
}

.progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.progress-pill {
  background: var(--brand-light);
  color: var(--brand);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
}
.progress-pill b {
  font-size: 15px;
}
.progress-pill span {
  font-size: 12px;
  opacity: 0.8;
}
.progress-total {
  font-size: 12px;
  color: var(--text-tertiary);
}

.question-card {
  padding: 16px;
}
.question-type {
  display: flex;
  align-items: center;
  gap: 8px;
}
.type-pill {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 6px;
  padding: 2px 8px;
}
.score-pill {
  font-size: 12px;
  color: var(--text-tertiary);
}
.question-content {
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.75;
  color: var(--text-color);
}
.question-image {
  display: block;
  max-width: 100%;
  max-height: 260px;
  margin: 12px auto 0;
  border-radius: 10px;
  object-fit: contain;
  background: var(--bg-page, #f7f8fa);
}

.options {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 13px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.option:active {
  transform: scale(0.99);
}
.option.selected {
  border-color: var(--brand);
  background: var(--brand-light);
}
.option-letter {
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  border-radius: 50%;
  background: var(--card-bg-sub);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.option.selected .option-letter {
  background: var(--brand);
  color: #fff;
}
.option-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-color);
}
.option-check {
  color: var(--brand);
  font-size: 18px;
}

.multi-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--accent);
}

.result-panel {
  margin-top: 14px;
}
.result-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: var(--radius-md);
  padding: 12px 14px;
  font-size: 14px;
  font-weight: 500;
}
.result-banner.ok {
  background: rgba(18, 161, 80, 0.1);
  color: var(--success);
}
.result-banner.no {
  background: rgba(229, 72, 77, 0.1);
  color: var(--danger);
}
.answer-text {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
}
.result-sub {
  margin-top: 8px;
  font-size: 12px;
  color: var(--success);
}
.analysis-card {
  margin-top: 10px;
  padding: 14px 16px;
}
.analysis-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 6px;
}
.analysis-text {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.action-buttons {
  margin-top: 18px;
}

.finish-panel {
  padding: 30px 18px;
}
.finish-card {
  padding: 30px 20px 22px;
  text-align: center;
}
.finish-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin: 0 auto;
  background: rgba(18, 161, 80, 0.12);
  color: var(--success);
  display: flex;
  align-items: center;
  justify-content: center;
}
.finish-title {
  margin-top: 14px;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-color);
}
.finish-desc {
  margin-top: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}
.finish-desc b {
  color: var(--text-color);
  font-size: 16px;
}
.finish-desc .ok {
  color: var(--success);
}
.finish-actions {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.finish-tip {
  margin-top: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
