<template>
  <div class="exam-page">
    <van-nav-bar
      :title="stage === 'exam' ? '考试中' : stage === 'result' ? '考试成绩' : '考试详情'"
      left-text="返回"
      @click-left="handleBack"
    />

    <!-- 考试介绍 -->
    <div v-if="stage === 'intro'" class="intro">
      <van-empty v-if="errorMsg" :description="errorMsg" />
      <template v-else>
        <div class="card intro-card">
          <div class="intro-title">{{ exam.title }}</div>
          <div v-if="exam.description" class="intro-desc">{{ exam.description }}</div>

          <div class="info-grid">
            <div class="info">
              <b>{{ exam.question_count || 0 }}</b>
              <span>题目数</span>
            </div>
            <div class="info">
              <b>{{ exam.total_score }}</b>
              <span>总分</span>
            </div>
            <div class="info">
              <b>{{ exam.pass_score }}</b>
              <span>及格分</span>
            </div>
            <div class="info">
              <b>{{ duration }}</b>
              <span>分钟</span>
            </div>
          </div>

          <div v-if="attemptState.used > 0" class="attempt-rows">
            <div class="attempt-row"><span>已考次数</span><span>{{ attemptState.used }} 次</span></div>
            <div class="attempt-row"><span>最高分</span><span>{{ attemptState.best_score }} 分</span></div>
            <div class="attempt-row"><span>本次是</span><span>{{ retakeLine }}</span></div>
          </div>
        </div>

        <div class="intro-tip card">
          <van-icon name="info-o" class="tip-icon" />
          <span>开始后计时 {{ duration }} 分钟，时间到会自动交卷</span>
        </div>
        <div v-if="!attemptState.can_take" class="intro-tip card danger">
          <van-icon name="warning-o" class="tip-icon" />
          <span>{{ blockedText }}</span>
        </div>

        <div class="action-buttons">
          <van-button
            type="primary"
            round
            block
            :loading="loading"
            :disabled="!canStart || !attemptState.can_take"
            @click="startExam"
          >
            开始考试
          </van-button>
        </div>
      </template>
    </div>

    <!-- 答题 -->
    <div v-else-if="stage === 'exam'">
      <div class="exam-bar">
        <span class="timer" :class="{ urgent: remaining <= 300 }">剩余 {{ timeText }}</span>
        <span class="progress">已答 {{ answeredCount }} / {{ questions.length }}</span>
      </div>

      <div class="sheet">
        <span
          v-for="(q, i) in questions"
          :key="q.id"
          class="sheet-item"
          :class="{ done: !!answers[q.id], cur: i === currentIndex }"
          @click="jump(i)"
        >{{ i + 1 }}</span>
      </div>

      <div class="question-container">
        <div class="question-card card">
          <div class="question-type">
            <span class="type-pill">{{ typeText(current.type) }}</span>
            <span class="score-pill">{{ current.score }} 分</span>
            <span class="idx">{{ currentIndex + 1 }} / {{ questions.length }}</span>
          </div>
          <div class="question-content">{{ current.content }}</div>
          <img
            v-if="current.image"
            :src="current.image"
            alt="题目图片"
            class="question-image"
            @click="previewQuestionImage"
          />
        </div>

        <div class="options">
          <div
            v-for="option in current.options"
            :key="option.id"
            class="option"
            :class="{ selected: isSelected(option) }"
            @click="selectOption(option)"
          >
            <div class="option-letter">{{ option.label }}</div>
            <div class="option-text">{{ option.content }}</div>
            <van-icon v-if="isSelected(option)" name="success" class="option-check" />
          </div>
        </div>

        <div v-if="current.type === 'multiple'" class="multi-hint">
          多选题：可选多个选项，选完点「下一题」
        </div>
      </div>

      <div class="bottom-bar">
        <van-button round plain :disabled="currentIndex === 0" @click="prevQuestion">上一题</van-button>
        <van-button v-if="currentIndex < questions.length - 1" round type="primary" @click="nextQuestion">
          下一题
        </van-button>
        <van-button v-else round type="primary" @click="confirmSubmit">交卷</van-button>
      </div>
      <div class="early-submit">
        <van-button size="small" plain type="warning" block :loading="submitting" @click="confirmSubmit">
          提前交卷
        </van-button>
      </div>
    </div>

    <!-- 成绩 -->
    <div v-else class="result">
      <div class="score-card card" :class="result.is_passed ? 'ok' : 'no'">
        <div class="score-label">本次得分</div>
        <div class="score">{{ result.total_score }}<span class="unit">分</span></div>
        <div class="pass">
          {{ result.is_passed ? '恭喜，考试通过' : '未达到及格分' }}
        </div>
      </div>
      <van-cell-group inset class="result-group">
        <van-cell title="总分" :value="exam.total_score + ' 分'" />
        <van-cell title="及格分" :value="exam.pass_score + ' 分'" />
        <van-cell title="答对" :value="correctCount + ' 道'" />
        <van-cell title="答错" :value="wrongCount + ' 道'" />
        <van-cell title="未答" :value="unansweredCount + ' 道'" />
        <van-cell title="本次为" :value="'第 ' + (result.attempts_used || 1) + ' 次作答'" />
        <van-cell title="之后" :value="resultLine" />
      </van-cell-group>
      <div class="action-buttons">
        <van-button type="warning" plain round block @click="goExamWrongBook">查看考试错题</van-button>
      </div>
      <div class="action-buttons">
        <van-button type="primary" round block @click="goExamList">返回考试列表</van-button>
      </div>
      <div class="action-buttons">
        <van-button plain round block @click="goRecords">查看我的成绩</van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast, showImagePreview } from 'vant'
import { examApi } from '../api'

const route = useRoute()
const router = useRouter()

const examId = Number(route.query.id || 0)

const exam = ref({})
const questions = ref([])
const currentIndex = ref(0)
const answers = reactive({})
const stage = ref('intro')
const loading = ref(false)
const submitting = ref(false)
const errorMsg = ref('')
const remaining = ref(0)
const result = ref({ total_score: 0, is_passed: false, correct_count: 0 })
const attemptState = ref({ used: 0, can_take: true, remaining: null, best_score: null })

let timer = null

const duration = computed(() => exam.value.duration || 60)
const canStart = computed(() => (exam.value.question_count || 0) > 0)
const retakeLine = computed(() => {
  if (!attemptState.value.can_take) return '重考次数已用完'
  if (attemptState.value.remaining === null) return '不限次数'
  return `还可考 ${attemptState.value.remaining} 次`
})
const blockedText = computed(() => {
  if (!attemptState.value.can_take && attemptState.value.used > 0) {
    return `这场考试${exam.value.allow_retake ? '重考次数已用完' : '不允许重考'}，最高分 ${attemptState.value.best_score} 分`
  }
  return ''
})
const resultLine = computed(() => {
  if (!result.value.can_take_again) return '本场考试不能重考了'
  if (result.value.remaining === null || result.value.remaining === undefined) return '可不限次数重考'
  return `还可考 ${result.value.remaining} 次`
})
const current = computed(() => questions.value[currentIndex.value] || { options: [] })

const previewQuestionImage = () => {
  if (!current.value?.image) return
  showImagePreview({ images: [current.value.image], closeable: true })
}
const answeredCount = computed(() =>
  Object.keys(answers).filter(id => answers[id]).length
)
const correctCount = computed(() => result.value.correct_count || 0)
const wrongCount = computed(() => Math.max(answeredCount.value - correctCount.value, 0))
const unansweredCount = computed(() => questions.value.length - answeredCount.value)

const timeText = computed(() => {
  const total = Math.max(remaining.value, 0)
  const m = String(Math.floor(total / 60)).padStart(2, '0')
  const s = String(total % 60).padStart(2, '0')
  return `${m}:${s}`
})

const typeText = (type) => {
  const map = { single: '单选题', multiple: '多选题', judge: '判断题' }
  return map[type] || type
}

const isSelected = (option) => (answers[current.value.id] || '').includes(option.label)

const loadExam = async () => {
  loading.value = true
  try {
    const info = await examApi.getExam(examId)
    exam.value = info
    if (info.status !== 1) {
      errorMsg.value = '这场考试还未发布，暂时不能参加'
    }
    try {
      attemptState.value = await examApi.getExamAttempts(examId)
    } catch (e) {
      // 无记录时后端仍返回 can_take，忽略
    }
  } catch (error) {
    errorMsg.value = '考试不存在或已结束'
  } finally {
    loading.value = false
  }
}

const startExam = async () => {
  if (!attemptState.value.can_take) {
    showToast(blockedText.value || '重考次数已用完')
    return
  }
  loading.value = true
  try {
    const list = await examApi.getExamQuestions(examId)
    if (!list.length) {
      showToast('这场考试还没有题目')
      return
    }
    questions.value = list
    Object.keys(answers).forEach(k => delete answers[k])
    currentIndex.value = 0
    remaining.value = duration.value * 60
    stage.value = 'exam'
    startTimer()
  } catch (error) {
    showToast('加载题目失败')
  } finally {
    loading.value = false
  }
}

const startTimer = () => {
  stopTimer()
  timer = setInterval(() => {
    remaining.value -= 1
    if (remaining.value <= 0) {
      stopTimer()
      showToast('考试时间到，已自动交卷')
      submitExam()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const selectOption = (option) => {
  const qid = current.value.id
  if (current.value.type === 'multiple') {
    const labels = (answers[qid] || '').split('').filter(Boolean)
    const i = labels.indexOf(option.label)
    if (i > -1) labels.splice(i, 1)
    else labels.push(option.label)
    answers[qid] = labels.sort().join('')
  } else {
    answers[qid] = option.label
  }
}

const prevQuestion = () => {
  if (currentIndex.value > 0) currentIndex.value -= 1
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value += 1
}

const jump = (i) => {
  currentIndex.value = i
}

const confirmSubmit = async () => {
  const left = questions.value.length - answeredCount.value
  const tip = left > 0 ? `还有 ${left} 道题未作答，确定交卷吗？` : '确定要交卷吗？'
  try {
    await showConfirmDialog({
      title: '交卷确认',
      message: tip,
      confirmButtonText: '确定交卷',
      cancelButtonText: '继续答题'
    })
  } catch (e) {
    return
  }
  submitExam()
}

const submitExam = async () => {
  if (submitting.value || stage.value !== 'exam') return
  submitting.value = true
  stopTimer()
  try {
    const payload = questions.value
      .filter(q => answers[q.id])
      .map(q => ({ question_id: q.id, user_answer: answers[q.id] }))
    const res = await examApi.submitExam(examId, payload)
    result.value = res
    stage.value = 'result'
    showToast(res.is_passed ? '考试通过' : '交卷完成')
  } catch (error) {
    const detail = error?.response?.data?.detail
    if (detail) {
      // 后端拒绝（如重考次数已用完），回到详情页重新拉取资格状态
      showToast(detail)
      stage.value = 'intro'
      await loadExam()
    } else {
      showToast('交卷失败，请重试')
      startTimer()
    }
  } finally {
    submitting.value = false
  }
}

const handleBack = async () => {
  if (stage.value === 'exam') {
    try {
      await showConfirmDialog({
        title: '退出考试',
        message: '退出后本次作答不会保存，确定退出吗？',
        confirmButtonText: '确定退出',
        cancelButtonText: '继续答题'
      })
    } catch (e) {
      return
    }
    stopTimer()
  }
  router.back()
}

const goExamList = () => {
  router.replace('/exam')
}

const goRecords = () => {
  router.push('/exam/records')
}

const goExamWrongBook = () => {
  router.push('/wrong?source=exam')
}

onMounted(loadExam)
onUnmounted(stopTimer)
</script>

<style scoped>
.exam-page {
  padding-bottom: 40px;
}
.intro {
  padding: 14px;
}
.intro-card {
  padding: 18px 16px;
}
.intro-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  line-height: 1.4;
}
.intro-desc {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
  margin-top: 8px;
  white-space: pre-wrap;
}
.info-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: var(--card-bg-sub);
  border-radius: var(--radius-md);
  padding: 12px 0;
}
.info {
  text-align: center;
}
.info b {
  display: block;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-color);
}
.info span {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-secondary);
}
.attempt-rows {
  margin-top: 12px;
}
.attempt-row {
  display: flex;
  justify-content: space-between;
  padding: 9px 0;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}
.attempt-row:last-child {
  border-bottom: none;
}
.attempt-row span:last-child {
  color: var(--text-color);
}
.intro-tip {
  margin-top: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--accent);
  background: rgba(217, 134, 0, 0.07);
  border: 1px solid rgba(217, 134, 0, 0.18);
  box-shadow: none;
}
.intro-tip.danger {
  color: var(--danger);
  background: rgba(229, 72, 77, 0.07);
  border-color: rgba(229, 72, 77, 0.2);
}
.tip-icon {
  font-size: 15px;
}
.action-buttons {
  margin-top: 18px;
}

/* 答题顶栏 */
.exam-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}
.timer {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  background: var(--brand-light);
  color: var(--brand);
  border-radius: 999px;
  padding: 3px 12px;
  font-variant-numeric: tabular-nums;
}
.timer.urgent {
  color: var(--danger);
  background: rgba(229, 72, 77, 0.1);
}
.progress {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 答题卡 */
.sheet {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 12px 16px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}
.sheet-item {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  border-radius: 50%;
  font-size: 12px;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  background: var(--card-bg-sub);
}
.sheet-item.done {
  background: var(--brand);
  border-color: var(--brand);
  color: #fff;
}
.sheet-item.cur {
  border-color: var(--accent);
  color: var(--accent);
  border-width: 2px;
  line-height: 26px;
  background: transparent;
}

.question-container {
  padding: 14px 14px 0;
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
.idx {
  margin-left: auto;
  color: var(--text-tertiary);
  font-size: 12px;
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

/* 选项 */
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
.bottom-bar {
  display: flex;
  gap: 12px;
  padding: 16px 14px 0;
}
.bottom-bar :deep(.van-button) {
  flex: 1;
}
.early-submit {
  padding: 12px 14px 0;
}

/* 成绩 */
.result {
  padding: 18px 14px;
  text-align: center;
}
.score-card {
  padding: 26px 20px 22px;
  margin-bottom: 16px;
  background: var(--hero-gradient);
  border-radius: var(--radius-lg);
}
.score-label {
  font-size: 12px;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.7);
}
.score {
  margin-top: 8px;
  font-size: 46px;
  font-weight: 700;
  color: #fff;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.unit {
  font-size: 16px;
  margin-left: 4px;
  font-weight: 400;
}
.pass {
  margin-top: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}
.pass.ok {
  color: #b5f2cf;
}
.pass.no {
  color: #ffd0d1;
}
.result-group {
  text-align: left;
}
</style>
