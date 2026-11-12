<template>
  <div class="page practice-start-page" :class="{ 'is-read': modeType === 'read' }">
    <van-nav-bar left-text="返回" @click-left="goBack">
      <template #title>
        <div class="mode-switch">
          <span
            v-for="item in modeOptions"
            :key="item.key"
            class="mode-item"
            :class="{ active: modeType === item.key }"
            @click="switchMode(item.key)"
          >{{ item.label }}</span>
        </div>
      </template>
      <template #right>
        <div class="top-actions">
          <button class="top-action" @click="openNote">
            <van-icon name="notes-o" />
            <span>笔记</span>
          </button>
          <button
            v-if="modeType === 'read'"
            class="top-action"
            @click="beginAnnotate"
          >
            <van-icon name="edit" />
            <span>标注</span>
          </button>
        </div>
      </template>
    </van-nav-bar>

    <div v-if="finished" class="finish-panel">
      <div class="finish-card card">
        <div class="finish-icon"><van-icon name="checked" size="30" /></div>
        <div class="finish-title">本组已完成</div>
        <div class="finish-desc">
          本组答对 <b class="ok">{{ batchCorrect }}</b> 题，答错 <b class="no">{{ batchWrong }}</b> 题
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
        <div class="progress-pill" @click="openAnswerCard">
          <b>{{ progressIndex }}</b><span>/ {{ progressTotal }}</span>
        </div>
        <div class="progress-meta">
          <span>{{ modeLabel }}</span>
          <span class="jump-link" @click="openAnswerCard">跳题</span>
        </div>
      </div>

      <div ref="surfaceRef" class="annotation-surface">
        <div class="question-card card">
          <div class="question-type">
            <span class="type-pill">{{ questionTypeText(currentQuestion.type) }}</span>
            <span class="score-pill">{{ currentQuestion.score }} 分</span>
            <span v-if="currentQuestion.category_name" class="category-pill">
              {{ currentQuestion.category_name }}
            </span>
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
            :class="optionClass(option)"
            @click="selectOption(option)"
          >
            <div class="option-letter">{{ option.label }}</div>
            <div class="option-text">{{ option.content }}</div>
            <van-icon
              v-if="showAnswer && isCorrectOption(option)"
              name="success"
              class="option-icon option-icon-ok"
            />
            <van-icon
              v-else-if="showAnswer && isWrongOption(option)"
              name="cross"
              class="option-icon option-icon-no"
            />
            <van-icon
              v-else-if="!showAnswer && isSelected(option)"
              name="success"
              class="option-icon option-icon-select"
            />
          </div>
        </div>

        <img
          v-if="savedAnnotation && !annotating && modeType === 'read'"
          :src="savedAnnotation"
          class="annotation-display"
          alt="画重点标注"
        />
        <canvas
          v-if="annotating"
          ref="canvasRef"
          class="annotation-canvas"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointerleave="onPointerUp"
        />
      </div>

      <div v-if="annotating" class="annotate-toolbar">
        <button class="annotate-btn" @click="clearAnnotation">
          <van-icon name="delete-o" /> 清除
        </button>
        <button class="annotate-btn" @click="undoAnnotation">
          <van-icon name="revoke" /> 撤销
        </button>
        <button class="annotate-btn" @click="redoAnnotation">
          <van-icon name="replay" /> 重做
        </button>
        <button class="annotate-btn primary" @click="saveAnnotation">
          <van-icon name="success" /> 保存
        </button>
        <button class="annotate-btn" @click="cancelAnnotation">取消</button>
      </div>

      <div v-if="isMultiple && modeType === 'answer' && !showResult" class="multi-hint">
        多选题：可选择多个选项，选完再点提交
      </div>

      <div v-if="showAnswer" class="result-panel">
        <div class="result-banner" :class="answerState ? (isCorrect ? 'ok' : 'no') : 'answer'">
          <van-icon :name="answerState ? (isCorrect ? 'checked' : 'cross') : 'info-o'" size="18" />
          <span v-if="answerState">{{ isCorrect ? '回答正确' : '回答错误' }}</span>
          <span v-else>{{ modeType === 'recite' ? '背题模式 · 直接看答案' : '读题模式 · 边读边记' }}</span>
          <span class="answer-text">答案 {{ formatAnswer(correctAnswer) }}</span>
        </div>
        <div v-if="isWrongSource && isCorrect" class="result-sub">
          答对了，这道题已自动移出「待复习」
        </div>
        <div v-if="currentQuestion.analysis" class="analysis-card card">
          <div class="analysis-title">解析</div>
          <div class="analysis-text">{{ currentQuestion.analysis }}</div>
        </div>
        <div v-if="currentNote" class="note-card card">
          <div class="analysis-title">我的笔记</div>
          <div class="analysis-text">{{ currentNote }}</div>
        </div>
      </div>

      <div class="action-buttons">
        <van-button
          v-if="modeType === 'answer' && !showResult"
          type="primary"
          round
          block
          :disabled="selected.length === 0"
          @click="submitAnswer"
        >
          提交答案
        </van-button>
        <van-button v-else type="primary" round block @click="nextQuestion">
          {{ currentIndex === questions.length - 1 ? '完成本组' : '下一题' }}
        </van-button>
      </div>

      <div class="practice-bottom">
        <button class="bottom-item" :class="{ active: isFavoriteQuestion }" @click="toggleFavorite">
          <van-icon :name="isFavoriteQuestion ? 'star' : 'star-o'" />
          <span>{{ isFavoriteQuestion ? '已收藏' : '收藏' }}</span>
        </button>
        <div class="bottom-counts">
          <span class="count-ok"><van-icon name="checked" /> {{ correctCount }}</span>
          <span class="count-no"><van-icon name="cross" /> {{ wrongCount }}</span>
        </div>
        <button class="bottom-item" @click="openAnswerCard">
          <van-icon name="apps-o" />
          <span>答题卡</span>
        </button>
      </div>
    </div>

    <van-empty v-else :description="loaded ? emptyText : '加载中...'" />

    <van-popup v-model:show="cardVisible" position="bottom" round class="answer-card-popup">
      <div class="card-head">
        <b>答题卡</b>
        <span>{{ progressIndex }} / {{ progressTotal }}</span>
      </div>
      <div class="jump-row">
        <span>跳到第</span>
        <input v-model="jumpText" type="number" inputmode="numeric" class="jump-input" placeholder="题号" />
        <span>题</span>
        <van-button size="small" type="primary" round @click="jumpTo">跳转</van-button>
      </div>
      <div class="answer-grid">
        <button
          v-for="(q, index) in questions"
          :key="q.id"
          class="answer-cell"
          :class="[cellClass(index), { current: index === currentIndex }]"
          @click="jumpToIndex(index)"
        >{{ offset + index + 1 }}</button>
      </div>
      <div class="card-legend">
        <span><i class="dot ok"></i>答对</span>
        <span><i class="dot no"></i>答错</span>
        <span><i class="dot current"></i>当前</span>
        <span><i class="dot gray"></i>未答</span>
      </div>
    </van-popup>

    <van-dialog
      v-model:show="noteVisible"
      title="题目笔记"
      show-cancel-button
      confirm-button-text="保存笔记"
      @confirm="saveNote"
    >
      <div class="note-dialog">
        <textarea
          v-model="noteDraft"
          class="note-textarea"
          rows="5"
          placeholder="记录这道题的思路、易错点或记忆方法..."
        ></textarea>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showImagePreview } from 'vant'
import { questionApi, practiceApi } from '../api'
import { getPracticeOffset, savePracticeOffset } from '../utils/practiceProgress'

const route = useRoute()
const router = useRouter()

const questions = ref([])
const currentIndex = ref(0)
const currentQuestion = ref(null)
const selected = ref([])
const answerStates = ref({})
const marks = ref({})
const loaded = ref(false)
const finished = ref(false)
const loadingBatch = ref(false)
const correctCount = ref(0)
const wrongCount = ref(0)
const modeType = ref('answer')

const cardVisible = ref(false)
const jumpText = ref('')
const noteVisible = ref(false)
const noteDraft = ref('')
const annotating = ref(false)
const canvasRef = ref(null)
const surfaceRef = ref(null)
const strokes = ref([])
const redoStack = ref([])
let drawing = false
let activeStroke = null

const modeOptions = [
  { key: 'answer', label: '答题' },
  { key: 'recite', label: '背题' },
  { key: 'read', label: '读题' }
]

const currentCategory = route.query.category || 0
const mode = route.query.mode || 'order'
const totalQuestions = Number(route.query.total || 0)
const isWrongSource = route.query.source === 'wrong'
const isFavoriteSource = route.query.source === 'favorite'
const hasRouteOffset = route.query.offset !== undefined && route.query.offset !== ''
const remainingInitialOffset = hasRouteOffset
  ? Number(route.query.offset || 0)
  : (isFavoriteSource ? 0 : getPracticeOffset(currentCategory))
const initialOffset = totalQuestions > 0 && remainingInitialOffset >= totalQuestions ? 0 : remainingInitialOffset
const offset = ref(initialOffset)
const seenIds = ref([])

const wrongFilter = {
  category_id: route.query.category || 0,
  type: route.query.type || '',
  status: route.query.status || 'pending',
  sort: route.query.sort || 'count',
  start_date: route.query.start_date || '',
  end_date: route.query.end_date || ''
}

const isMultiple = computed(() => currentQuestion.value?.type === 'multiple')
const answerState = computed(() => currentQuestion.value ? answerStates.value[currentQuestion.value.id] : null)
const showResult = computed(() => !!answerState.value)
const showAnswer = computed(() => modeType.value !== 'answer' || showResult.value)
const isCorrect = computed(() => !!answerState.value?.isCorrect)
const correctAnswer = computed(() => answerState.value?.correctAnswer || currentQuestion.value?.correct_answer || '')
const currentNote = computed(() => marks.value[currentQuestion.value?.id]?.note || '')
const isFavoriteQuestion = computed(() => !!marks.value[currentQuestion.value?.id]?.is_favorite)
const savedAnnotation = computed(() => marks.value[currentQuestion.value?.id]?.annotation || '')

const modeLabel = computed(() => {
  const map = { answer: '答题模式', recite: '背题模式', read: '读题模式' }
  return map[modeType.value] || ''
})
const emptyText = computed(() => {
  if (isFavoriteSource) return '还没有收藏题目，刷题时点星标即可收藏'
  return '这个分类下暂时没有题目'
})

const progressIndex = computed(() => offset.value + currentIndex.value + 1)
const progressTotal = computed(() => totalQuestions || questions.value.length)

const batchCorrect = computed(() =>
  Object.values(answerStates.value).filter(s => s.isCorrect).length
)
const batchWrong = computed(() =>
  Object.values(answerStates.value).filter(s => !s.isCorrect).length
)

const previewQuestionImage = () => {
  if (!currentQuestion.value?.image) return
  showImagePreview({ images: [currentQuestion.value.image], closeable: true })
}

const loadMarks = async () => {
  const ids = questions.value.map(q => q.id)
  if (!ids.length) {
    marks.value = {}
    return
  }
  try {
    const list = await practiceApi.getMarks(ids.join(','))
    const map = {}
    list.forEach(item => { map[item.question_id] = item })
    marks.value = map
  } catch (error) {
    marks.value = {}
  }
}

const loadQuestions = async (keepStats = false) => {
  loadingBatch.value = true
  if (!keepStats) {
    correctCount.value = 0
    wrongCount.value = 0
    offset.value = isWrongSource || isFavoriteSource ? 0 : initialOffset
    seenIds.value = []
  }
  finished.value = false
  annotating.value = false
  try {
    let list = []
    if (isWrongSource) {
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
    } else if (isFavoriteSource) {
      list = await practiceApi.getFavoriteQuestions({ count: 10, offset: offset.value })
      if (list.length === 0 && offset.value > 0) {
        offset.value = 0
        list = await practiceApi.getFavoriteQuestions({ count: 10, offset: 0 })
      }
    } else {
      const res = await questionApi.getRandomQuestions(
        currentCategory,
        10,
        mode,
        mode === 'order' ? offset.value : 0
      )
      list = res
      if (mode !== 'order') {
        list = res.filter(q => !seenIds.value.includes(q.id))
        list.forEach(q => seenIds.value.push(q.id))
      }
      if (list.length === 0 && offset.value > 0) {
        offset.value = 0
        if (mode === 'order') savePracticeOffset(currentCategory, 0)
        const again = await questionApi.getRandomQuestions(currentCategory, 10, mode, 0)
        list = again
        again.forEach(q => { if (!seenIds.value.includes(q.id)) seenIds.value.push(q.id) })
      }
    }

    questions.value = list
    currentIndex.value = 0
    answerStates.value = {}
    selected.value = []
    currentQuestion.value = list.length > 0 ? list[0] : null
    await loadMarks()
  } catch (error) {
    showToast('加载题目失败')
  } finally {
    loaded.value = true
    loadingBatch.value = false
  }
}

const restoreSelection = () => {
  const q = currentQuestion.value
  const state = q ? answerStates.value[q.id] : null
  selected.value = state ? [...state.selected] : []
}

const nextBatch = () => {
  if (isWrongSource || isFavoriteSource) {
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

const switchMode = (type) => {
  modeType.value = type
  annotating.value = false
  if (type === 'answer') restoreSelection()
}

const isSelected = (option) => selected.value.includes(option.label)

const isCorrectOption = (option) => {
  return correctAnswer.value.includes(option.label)
}

const isWrongOption = (option) => {
  return !!answerState.value && isSelected(option) && !isCorrectOption(option)
}

const optionClass = (option) => {
  if (showAnswer.value) {
    if (isCorrectOption(option)) return 'correct'
    if (isWrongOption(option)) return 'wrong'
    return 'muted'
  }
  return isSelected(option) ? 'selected' : ''
}

const selectOption = (option) => {
  if (modeType.value !== 'answer' || showResult.value) return
  if (isMultiple.value) {
    const i = selected.value.indexOf(option.label)
    if (i > -1) selected.value.splice(i, 1)
    else selected.value.push(option.label)
  } else {
    selected.value = [option.label]
  }
}

const formatAnswer = (answer) => {
  if (!answer) return ''
  return answer.split('').join(' ')
}

const submitAnswer = async () => {
  if (!currentQuestion.value || selected.value.length === 0) return
  try {
    const userAnswer = [...selected.value].sort().join('')
    const res = await practiceApi.submitAnswer({
      question_id: currentQuestion.value.id,
      user_answer: userAnswer
    })
    answerStates.value[currentQuestion.value.id] = {
      selected: [...selected.value],
      isCorrect: res.is_correct,
      correctAnswer: res.correct_answer
    }
    correctCount.value += res.is_correct ? 1 : 0
    wrongCount.value += res.is_correct ? 0 : 1
    if (!isWrongSource && !isFavoriteSource && mode === 'order') {
      savePracticeOffset(currentCategory, offset.value + currentIndex.value + 1)
    }
  } catch (error) {
    showToast('提交失败')
  }
}

const nextQuestion = () => {
  if (currentIndex.value >= questions.value.length - 1) {
    finished.value = true
    if (!isWrongSource && !isFavoriteSource && mode === 'order') {
      savePracticeOffset(currentCategory, offset.value + questions.value.length)
    }
    return
  }
  currentIndex.value++
  currentQuestion.value = questions.value[currentIndex.value]
  restoreSelection()
  annotating.value = false
}

const persistPosition = () => {
  if (isWrongSource || mode !== 'order') return
  const key = isFavoriteSource ? 'favorite' : currentCategory
  const position = finished.value
    ? offset.value + questions.value.length
    : offset.value + currentIndex.value + (showResult.value ? 1 : 0)
  savePracticeOffset(key, position)
}

const goBack = () => {
  persistPosition()
  router.back()
}

const openAnswerCard = () => {
  jumpText.value = String(progressIndex.value)
  cardVisible.value = true
}

const cellClass = (index) => {
  const q = questions.value[index]
  const state = q ? answerStates.value[q.id] : null
  if (state) return state.isCorrect ? 'ok' : 'no'
  return 'unanswered'
}

const jumpToIndex = (index) => {
  if (index < 0 || index >= questions.value.length) return
  currentIndex.value = index
  currentQuestion.value = questions.value[index]
  restoreSelection()
  annotating.value = false
  cardVisible.value = false
}

const jumpTo = () => {
  const target = Number(jumpText.value)
  if (!Number.isInteger(target) || target < 1) {
    showToast('请输入正确的题号')
    return
  }
  if (progressTotal.value && target > progressTotal.value) {
    showToast(`本题库共 ${progressTotal.value} 题`)
    return
  }
  const targetIndex = target - 1
  if (targetIndex >= offset.value && targetIndex < offset.value + questions.value.length) {
    jumpToIndex(targetIndex - offset.value)
    return
  }
  if (isWrongSource || isFavoriteSource || (mode === 'order' && progressTotal.value > 0)) {
    offset.value = targetIndex
    cardVisible.value = false
    loadQuestions(true)
    return
  }
  showToast('当前批次内可跳转，跨组跳题请使用顺序练习')
}

const toggleFavorite = async () => {
  if (!currentQuestion.value) return
  const next = !isFavoriteQuestion.value
  try {
    const mark = await practiceApi.saveMark(currentQuestion.value.id, { is_favorite: next })
    marks.value = {
      ...marks.value,
      [currentQuestion.value.id]: { ...marks.value[currentQuestion.value.id], ...mark }
    }
    showToast(next ? '已收藏，以后可重点复习' : '已取消收藏')
  } catch (error) {
    showToast('收藏失败')
  }
}

const openNote = () => {
  if (!currentQuestion.value) return
  noteDraft.value = currentNote.value
  noteVisible.value = true
}

const saveNote = async () => {
  if (!currentQuestion.value) return
  try {
    const mark = await practiceApi.saveMark(currentQuestion.value.id, { note: noteDraft.value })
    marks.value = {
      ...marks.value,
      [currentQuestion.value.id]: { ...marks.value[currentQuestion.value.id], ...mark }
    }
    showToast('笔记已保存')
  } catch (error) {
    showToast('笔记保存失败')
  }
}

const setupCanvas = () => {
  const surface = surfaceRef.value
  const canvas = canvasRef.value
  if (!surface || !canvas) return
  const dpr = window.devicePixelRatio || 1
  const width = surface.clientWidth
  const height = surface.scrollHeight
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  const ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.lineWidth = 2.5
  ctx.strokeStyle = '#e5484d'
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  redrawAnnotation()
}

const beginAnnotate = async () => {
  annotating.value = true
  strokes.value = []
  redoStack.value = []
  await nextTick()
  setupCanvas()
}

const cancelAnnotation = () => {
  annotating.value = false
  strokes.value = []
  redoStack.value = []
}

const redrawAnnotation = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr)
  ctx.lineWidth = 2.5
  ctx.strokeStyle = '#e5484d'
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  for (const stroke of strokes.value) {
    if (!stroke.length) continue
    ctx.beginPath()
    ctx.moveTo(stroke[0].x, stroke[0].y)
    for (let i = 1; i < stroke.length; i++) {
      ctx.lineTo(stroke[i].x, stroke[i].y)
    }
    ctx.stroke()
  }
}

const pointFromEvent = (event) => {
  const rect = canvasRef.value.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
}

const onPointerDown = (event) => {
  event.preventDefault()
  if (!canvasRef.value) return
  drawing = true
  activeStroke = [pointFromEvent(event)]
  strokes.value.push(activeStroke)
  redoStack.value = []
  canvasRef.value.setPointerCapture?.(event.pointerId)
}

const onPointerMove = (event) => {
  if (!drawing || !activeStroke) return
  event.preventDefault()
  const point = pointFromEvent(event)
  activeStroke.push(point)
  const ctx = canvasRef.value.getContext('2d')
  const prev = activeStroke[activeStroke.length - 2]
  if (prev) {
    ctx.beginPath()
    ctx.moveTo(prev.x, prev.y)
    ctx.lineTo(point.x, point.y)
    ctx.stroke()
  }
}

const onPointerUp = () => {
  drawing = false
  activeStroke = null
}

const undoAnnotation = () => {
  const last = strokes.value.pop()
  if (last) {
    redoStack.value.push(last)
    redrawAnnotation()
  }
}

const redoAnnotation = () => {
  const last = redoStack.value.pop()
  if (last) {
    strokes.value.push(last)
    redrawAnnotation()
  }
}

const clearAnnotation = () => {
  strokes.value = []
  redoStack.value = []
  redrawAnnotation()
}

const saveAnnotation = async () => {
  const canvas = canvasRef.value
  if (!canvas) return
  try {
    const dataUrl = canvas.toDataURL('image/png')
    const mark = await practiceApi.saveMark(currentQuestion.value.id, { annotation: dataUrl })
    marks.value = {
      ...marks.value,
      [currentQuestion.value.id]: { ...marks.value[currentQuestion.value.id], ...mark }
    }
    annotating.value = false
    showToast('标注已保存')
  } catch (error) {
    showToast('标注保存失败')
  }
}

const onResize = () => {
  if (annotating.value) setupCanvas()
}

onMounted(() => {
  loadQuestions()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  persistPosition()
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.practice-start-page {
  padding-bottom: 96px;
}
.is-read {
  padding-bottom: 96px;
}

.mode-switch {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 3px;
  gap: 2px;
}
.mode-item {
  min-width: 54px;
  padding: 4px 8px;
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.88);
  border-radius: 999px;
  cursor: pointer;
}
.mode-item.active {
  background: #fff;
  color: var(--brand);
  font-weight: 600;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.top-action {
  border: 0;
  background: transparent;
  color: #fff;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 0;
}
.top-action .van-icon {
  font-size: 18px;
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
  cursor: pointer;
}
.progress-pill b {
  font-size: 15px;
}
.progress-pill span {
  font-size: 12px;
  opacity: 0.8;
}
.progress-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.jump-link {
  color: var(--brand);
  cursor: pointer;
}

.annotation-surface {
  position: relative;
}
.question-card {
  padding: 16px;
}
.question-type {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.type-pill {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 6px;
  padding: 2px 8px;
}
.score-pill,
.category-pill {
  font-size: 12px;
  color: var(--text-tertiary);
}
.question-content {
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.75;
  color: var(--text-color);
  white-space: pre-wrap;
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
.option.correct {
  border-color: rgba(18, 161, 80, 0.55);
  background: rgba(18, 161, 80, 0.12);
}
.option.wrong {
  border-color: rgba(229, 72, 77, 0.55);
  background: rgba(229, 72, 77, 0.11);
}
.option.muted {
  opacity: 0.72;
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
.option.correct .option-letter {
  background: var(--success);
  color: #fff;
}
.option.wrong .option-letter {
  background: var(--danger);
  color: #fff;
}
.option-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-color);
}
.option-icon {
  font-size: 19px;
}
.option-icon-ok {
  color: var(--success);
}
.option-icon-no {
  color: var(--danger);
}
.option-icon-select {
  color: var(--brand);
}

.annotation-canvas {
  position: absolute;
  inset: 0;
  z-index: 8;
  touch-action: none;
  cursor: crosshair;
}
.annotation-display {
  position: absolute;
  inset: 0;
  z-index: 7;
  width: 100%;
  height: 100%;
  pointer-events: none;
  object-fit: fill;
}

.annotate-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}
.annotate-btn {
  border: 0;
  background: var(--card-bg-sub);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 3px;
}
.annotate-btn.primary {
  background: var(--brand);
  color: #fff;
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
.result-banner.answer {
  background: var(--brand-light);
  color: var(--brand);
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
.analysis-card,
.note-card {
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

.practice-bottom {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px calc(10px + env(safe-area-inset-bottom));
  background: var(--card-bg);
  border-top: 1px solid var(--border-color);
}
.bottom-item {
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  padding: 0 4px;
}
.bottom-item.active {
  color: var(--accent);
}
.bottom-item .van-icon {
  font-size: 20px;
}
.bottom-counts {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 13px;
}
.count-ok {
  color: var(--success);
}
.count-no {
  color: var(--danger);
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
  font-size: 16px;
}
.finish-desc .ok {
  color: var(--success);
}
.finish-desc .no {
  color: var(--danger);
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

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 10px;
  font-size: 15px;
  color: var(--text-color);
}
.card-head span {
  font-size: 12px;
  color: var(--text-tertiary);
}
.jump-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px 14px;
  font-size: 13px;
  color: var(--text-secondary);
}
.jump-input {
  width: 76px;
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg-sub);
  color: var(--text-color);
  text-align: center;
  font-size: 14px;
  outline: none;
}
.answer-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  padding: 0 20px 18px;
}
.answer-cell {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: var(--card-bg-sub);
  color: var(--text-secondary);
  font-size: 14px;
  justify-self: center;
}
.answer-cell.ok {
  background: var(--success);
  border-color: var(--success);
  color: #fff;
}
.answer-cell.no {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}
.answer-cell.unanswered {
  background: var(--card-bg-sub);
  color: var(--text-tertiary);
}
.answer-cell.current {
  box-shadow: 0 0 0 3px var(--brand-light);
  border-color: var(--brand);
}
.card-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 0 20px 20px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.dot.ok {
  background: var(--success);
}
.dot.no {
  background: var(--danger);
}
.dot.current {
  background: var(--brand);
}
.dot.gray {
  background: var(--border-color);
}

.note-dialog {
  padding: 8px 18px 18px;
}
.note-textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 120px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--card-bg-sub);
  color: var(--text-color);
  padding: 10px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
}
</style>
