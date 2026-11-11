<template>
  <el-card>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between;">
      <el-button type="primary" @click="openAddDialog">创建考试</el-button>
    </div>

    <el-table :data="tableData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="56" />
      <el-table-column prop="title" label="考试名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="question_count" label="题数" width="62" />
      <el-table-column label="总分/及格" width="92">
        <template #default="scope">{{ scope.row.total_score }} / {{ scope.row.pass_score }}</template>
      </el-table-column>
      <el-table-column prop="duration" label="时长" width="64" />
      <el-table-column prop="status" label="状态" width="88">
        <template #default="scope">
          <el-tag :type="['info', 'success', 'danger'][scope.row.status]" size="small">
            {{ ['草稿', '已发布', '已结束'][scope.row.status] }}
          </el-tag>
          <div class="hint retake-line">
            {{ !scope.row.allow_retake ? '不可重考' : (!scope.row.retake_limit ? '不限重考' : '可重考' + scope.row.retake_limit + '次') }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="190">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleMonitor(scope.row)">成绩</el-button>
          <el-button
            link
            size="small"
            :type="scope.row.status === 1 ? 'warning' : 'success'"
            @click="handlePublish(scope.row)"
          >
            {{ scope.row.status === 1 ? '下线' : '发布' }}
          </el-button>
          <el-button link type="primary" size="small" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin-top: 16px; justify-content: flex-end;"
      v-model:current-page="query.page"
      v-model:page-size="query.pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadData"
    />

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑考试' : '创建考试'" width="920px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="考试名称">
              <el-input v-model="form.title" placeholder="例如：2026年提职司机模拟考" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="时长(分钟)">
              <el-input-number v-model="form.duration" :min="5" :max="300" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="考试说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="重考设置">
          <el-switch
            v-model="form.allow_retake"
            :active-value="1"
            :inactive-value="0"
            active-text="允许重考"
            inactive-text="不可重考"
          />
          <el-input-number
            v-model="form.retake_limit"
            :min="0"
            :max="10"
            :disabled="form.allow_retake !== 1"
            style="margin-left: 12px; width: 130px;"
          />
          <span class="hint" style="margin-left: 8px;">次（0 表示不限次数）</span>
        </el-form-item>
      </el-form>

      <el-tabs v-model="buildMode" type="border-card" @tab-change="onTabChange">
        <el-tab-pane label="按题型随机抽题" name="random">
          <div class="toolbar">
            <span>出题范围：</span>
            <el-select v-model="composeCategory" style="width: 220px;" @change="loadAvailable">
              <el-option label="全部题目" :value="0" />
              <el-option
                v-for="cat in parentCategories"
                :key="cat.id"
                :label="cat.name + '（' + cat.question_count + ' 题）'"
                :value="cat.id"
              />
            </el-select>
            <span class="hint">从选定范围内按题型随机抽题；同一题型每道题分数相同</span>
          </div>

          <el-table :data="composeRows" border size="small" style="margin-top: 12px;">
            <el-table-column prop="label" label="题型" width="110" />
            <el-table-column label="可用题量" width="110">
              <template #default="scope">{{ scope.row.available }}</template>
            </el-table-column>
            <el-table-column label="抽题数量" width="170">
              <template #default="scope">
                <el-input-number
                  v-model="scope.row.count"
                  :min="0"
                  :max="Math.max(scope.row.available, 0)"
                  size="small"
                  @change="onComposeChange"
                />
              </template>
            </el-table-column>
            <el-table-column label="每题分值" width="170">
              <template #default="scope">
                <el-input-number
                  v-model="scope.row.score"
                  :min="0.5"
                  :max="20"
                  :step="0.5"
                  size="small"
                  @change="onComposeChange"
                />
              </template>
            </el-table-column>
            <el-table-column label="小计" width="120">
              <template #default="scope">{{ scope.row.count * scope.row.score }} 分</template>
            </el-table-column>
            <el-table-column label="">
              <template #default="scope">
                <el-button
                  link
                  type="primary"
                  :disabled="scope.row.available === 0"
                  @click="pickAll(scope.row)"
                >全部</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="summary">
            共 <b>{{ composeCount }}</b> 题，总分 <b>{{ composeTotal }}</b> 分
            <span class="err" v-if="composeError">{{ composeError }}</span>
          </div>

          <el-form label-width="100px" style="margin-top: 12px;">
            <el-form-item label="及格分">
              <el-input-number
                v-model="form.pass_score"
                :min="0"
                :max="composeTotal > 0 ? composeTotal : 1000"
                @change="passTouched = true"
              />
              <span class="hint" style="margin-left: 8px;">默认按总分的 60% 计算，可手动修改</span>
            </el-form-item>
          </el-form>

          <el-alert
            v-if="isEdit"
            type="warning"
            :closable="false"
            show-icon
            title="编辑已有考试时选择这项，保存后会重新随机抽题，原题目会被替换"
          />
        </el-tab-pane>

        <el-tab-pane label="手动选题" name="manual">
          <div class="toolbar">
            <el-select v-model="manualQuery.categoryId" style="width: 200px;" @change="loadManual">
              <el-option label="全部分类" :value="0" />
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
            <el-select v-model="manualQuery.type" clearable placeholder="全部题型" style="width: 130px;" @change="loadManual">
              <el-option label="单选题" value="single" />
              <el-option label="多选题" value="multiple" />
              <el-option label="判断题" value="judge" />
            </el-select>
            <el-input
              v-model="manualQuery.keyword"
              placeholder="搜索题干关键词"
              clearable
              style="width: 220px;"
              @keyup.enter="loadManual"
              @clear="loadManual"
            />
            <el-button type="primary" @click="loadManual">搜索</el-button>
            <span class="selected-count">已选 {{ selectedIds.length }} 道</span>
            <el-button link type="danger" :disabled="selectedIds.length === 0" @click="clearSelection">清空已选</el-button>
          </div>

          <el-table
            ref="manualTableRef"
            :data="manualData"
            border
            size="small"
            height="360"
            row-key="id"
            @selection-change="onManualSelection"
          >
            <el-table-column type="selection" width="45" reserve-selection />
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column label="题型" width="80">
              <template #default="scope">{{ typeText(scope.row.type) }}</template>
            </el-table-column>
            <el-table-column prop="content" label="题干" show-overflow-tooltip />
          </el-table>
          <div class="hint" style="margin-top: 8px;">
            列表最多显示 {{ manualQuery.pageSize }} 条，用分类、题型或关键词缩小范围后勾选
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="monitorVisible" :title="'考试成绩 · ' + resultTitle" width="820px">
      <div class="result-summary">
        <div class="result-cell"><b>{{ resultSummary.participants }}</b><span>参考人数</span></div>
        <div class="result-cell"><b>{{ resultSummary.attempts }}</b><span>答卷次数</span></div>
        <div class="result-cell"><b>{{ resultSummary.avg_score }}</b><span>平均分</span></div>
        <div class="result-cell"><b>{{ resultSummary.pass_rate }}%</b><span>通过率</span></div>
      </div>
      <el-table :data="resultRows" border size="small" max-height="380" empty-text="还没有学员提交答卷">
        <el-table-column prop="real_name" label="考生" width="110" />
        <el-table-column prop="username" label="账号" width="110" />
        <el-table-column label="得分" width="110">
          <template #default="scope">
            <span :class="scope.row.passed ? 'pass' : 'fail'">{{ scope.row.score }}</span>
            <span class="hint"> / {{ scope.row.total_score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="答对/题量" width="110">
          <template #default="scope">{{ scope.row.correct_count }} / {{ scope.row.answered_count }}</template>
        </el-table-column>
        <el-table-column label="结果" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.passed ? 'success' : 'danger'" size="small">
              {{ scope.row.passed ? '通过' : '未通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间">
          <template #default="scope">{{ formatTime(scope.row.submitted_at) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { examApi, questionApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const monitorVisible = ref(false)
const categories = ref([])
const parentCategories = ref([])

const buildMode = ref('random')
const composeCategory = ref(0)
const available = ref({ single: 0, multiple: 0, judge: 0 })
const composeRows = ref([
  { type: 'single', label: '单选题', count: 0, score: 1, available: 0 },
  { type: 'multiple', label: '多选题', count: 0, score: 2, available: 0 },
  { type: 'judge', label: '判断题', count: 0, score: 1, available: 0 }
])

const manualQuery = ref({ categoryId: 0, type: '', keyword: '', pageSize: 200 })
const manualData = ref([])
const manualTableRef = ref(null)
const selectedIds = ref([])

const query = ref({ page: 1, pageSize: 10 })

const form = ref({
  id: null,
  title: '',
  description: '',
  pass_score: 60,
  duration: 60,
  status: 0,
  allow_retake: 0,
  retake_limit: 0
})

const resultRows = ref([])
const resultTitle = ref('')
const resultSummary = ref({ participants: 0, attempts: 0, avg_score: 0, pass_rate: 0 })

const typeText = (type) => {
  const map = { single: '单选题', multiple: '多选题', judge: '判断题' }
  return map[type] || type
}

const composeCount = computed(() => composeRows.value.reduce((s, r) => s + (r.count || 0), 0))
const composeTotal = computed(() => composeRows.value.reduce((s, r) => s + (r.count || 0) * (r.score || 0), 0))

const composeError = computed(() => {
  const over = composeRows.value.find(r => r.count > r.available)
  if (over) return `${over.label}最多只能抽 ${over.available} 道`
  return ''
})

let passTouched = false

watch(composeTotal, (val) => {
  if (passTouched || buildMode.value !== 'random') return
  form.value.pass_score = Math.round(val * 0.6 * 10) / 10
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await examApi.getExamList()
    tableData.value = res
    total.value = res.length
  } catch (error) {
    console.error('加载考试失败', error)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const res = await questionApi.getCategories('question', true)
    // 组卷/选题只展示启用中的分类，停用的历史测试分类不出现在下拉里
    categories.value = (res || []).filter(c => c.status !== 0)
    parentCategories.value = res.filter(c => c.parent_id === 0 && c.question_count > 0)
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadAvailable = async () => {
  try {
    const res = await examApi.getAvailableQuestions(composeCategory.value)
    available.value = res
    composeRows.value.forEach(r => {
      r.available = res[r.type] || 0
      if (r.count > r.available) r.count = r.available
    })
  } catch (error) {
    console.error('加载可用题量失败', error)
  }
}

const onComposeChange = () => {
  // 数量或分值变化时重算及格分（用户手动改过则不再覆盖）
  if (!passTouched) {
    form.value.pass_score = Math.round(composeTotal.value * 0.6 * 10) / 10
  }
}

const pickAll = (row) => {
  row.count = row.available
  onComposeChange()
}

const loadManual = async () => {
  try {
    const page = await questionApi.getQuestionPage({
      category_id: manualQuery.value.categoryId,
      type: manualQuery.value.type || undefined,
      keyword: manualQuery.value.keyword || undefined,
      show_all: true,
      page: 1,
      page_size: manualQuery.value.pageSize
    })
    manualData.value = page.items
    await nextTick()
    syncTableSelection()
  } catch (error) {
    console.error('加载题目失败', error)
  }
}

const loadSelectedIntoList = async (examId) => {
  try {
    const rows = await examApi.getExamQuestions(examId)
    const existing = new Set(manualData.value.map(r => r.id))
    const missing = rows.filter(r => !existing.has(r.id))
    if (missing.length) {
      manualData.value = [...missing, ...manualData.value]
    }
    await nextTick()
    syncTableSelection()
  } catch (error) {
    console.error('加载卷内题目失败', error)
  }
}

const onTabChange = async (name) => {
  if (name === 'manual') {
    await nextTick()
    syncTableSelection()
    window.setTimeout(syncTableSelection, 60)
  }
}

let syncingSelection = false

const syncTableSelection = () => {
  if (!manualTableRef.value) return
  syncingSelection = true
  manualData.value.forEach(row => {
    manualTableRef.value.toggleRowSelection(row, selectedIds.value.includes(row.id))
  })
  syncingSelection = false
}

const onManualSelection = (rows) => {
  if (syncingSelection) return
  const pageIds = manualData.value.map(r => r.id)
  const rowIds = rows.map(r => r.id)
  const kept = selectedIds.value.filter(id => !pageIds.includes(id))
  selectedIds.value = kept.concat(rowIds)
}

const clearSelection = () => {
  selectedIds.value = []
  if (manualTableRef.value) {
    syncingSelection = true
    manualTableRef.value.clearSelection()
    syncingSelection = false
  }
}

const openAddDialog = async () => {
  isEdit.value = false
  buildMode.value = 'random'
  passTouched = false
  composeCategory.value = 0
  composeRows.value = [
    { type: 'single', label: '单选题', count: 0, score: 1, available: 0 },
    { type: 'multiple', label: '多选题', count: 0, score: 2, available: 0 },
    { type: 'judge', label: '判断题', count: 0, score: 1, available: 0 }
  ]
  selectedIds.value = []
  manualQuery.value = { categoryId: 0, type: '', keyword: '', pageSize: 200 }
  form.value = {
    id: null,
    title: '',
    description: '',
    pass_score: 60,
    duration: 60,
    status: 0,
    allow_retake: 0,
    retake_limit: 0
  }
  await loadAvailable()
  loadManual()
  dialogVisible.value = true
}

const openEditDialog = async (row) => {
  isEdit.value = true
  passTouched = true
  buildMode.value = 'manual'
  composeCategory.value = row.category_id || 0
  form.value = {
    id: row.id,
    title: row.title,
    description: row.description || '',
    pass_score: Number(row.pass_score) || 60,
    duration: row.duration || 60,
    status: row.status || 0,
    allow_retake: row.allow_retake ? 1 : 0,
    retake_limit: Number(row.retake_limit) || 0
  }
  selectedIds.value = []
  manualQuery.value = { categoryId: 0, type: '', keyword: '', pageSize: 200 }
  dialogVisible.value = true
  await loadAvailable()
  await loadManual()
  // 载入已有题目：置顶显示并勾选，避免"已选 N 道"却看不到勾选了哪些
  try {
    const existing = await examApi.getExamQuestions(row.id)
    selectedIds.value = existing.map(q => q.id)
  } catch (error) {
    console.error('加载考试题目失败', error)
  }
  await loadSelectedIntoList(row.id)
}

const handlePublish = async (row) => {
  const newStatus = row.status === 1 ? 0 : 1
  if (newStatus === 1 && (row.question_count === 0)) {
    ElMessage.warning('这场考试还没有题目，请先编辑加入题目再发布')
    return
  }
  try {
    await examApi.updateExam(row.id, {
      title: row.title,
      description: row.description,
      category_id: row.category_id,
      duration: row.duration,
      pass_score: row.pass_score,
      status: newStatus,
      allow_retake: row.allow_retake || 0,
      retake_limit: row.retake_limit || 0
    })
    ElMessage.success(newStatus === 1 ? '考试已发布，学员可以参加考试了' : '考试已下线')
    loadData()
  } catch (error) {
    console.error('操作失败', error)
    ElMessage.error('操作失败')
  }
}

const handleSubmit = async () => {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写考试名称')
    return
  }

  const payload = {
    title: form.value.title.trim(),
    description: form.value.description,
    duration: form.value.duration,
    pass_score: form.value.pass_score,
    status: form.value.status,
    allow_retake: form.value.allow_retake ? 1 : 0,
    retake_limit: form.value.allow_retake ? (form.value.retake_limit || 0) : 0
  }

  if (buildMode.value === 'random') {
    if (composeCount.value === 0) {
      ElMessage.warning('请至少给一种题型设置抽题数量')
      return
    }
    if (composeError.value) {
      ElMessage.warning(composeError.value)
      return
    }
    if (form.value.pass_score > composeTotal.value) {
      ElMessage.warning('及格分不能超过总分')
      return
    }
    payload.category_id = composeCategory.value || null
    payload.compose = composeRows.value
      .filter(r => r.count > 0)
      .map(r => ({ type: r.type, count: r.count, score: r.score }))
  } else {
    if (selectedIds.value.length === 0) {
      ElMessage.warning('请至少选择一道题目')
      return
    }
    payload.category_id = manualQuery.value.categoryId || null
    payload.question_ids = selectedIds.value
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await examApi.updateExam(form.value.id, payload)
    } else {
      await examApi.createExam(payload)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '创建成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('提交失败', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个考试吗？', '确认删除', { type: 'warning' })
    await examApi.deleteExam(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    // 取消删除
  }
}

const handleMonitor = async (row) => {
  resultTitle.value = row.title
  resultRows.value = []
  resultSummary.value = { participants: 0, attempts: 0, avg_score: 0, pass_rate: 0 }
  monitorVisible.value = true
  try {
    const res = await examApi.getExamResults(row.id)
    resultRows.value = res.items || []
    resultSummary.value = {
      participants: res.participants || 0,
      attempts: res.attempts || 0,
      avg_score: res.avg_score || 0,
      pass_rate: res.pass_rate || 0
    }
  } catch (error) {
    ElMessage.error('加载成绩失败')
  }
}

const formatTime = (value) => {
  if (!value) return '—'
  const raw = String(value)
  const d = new Date(raw.endsWith('Z') ? raw : raw + 'Z')
  return d.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  loadData()
  loadCategories()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.hint {
  color: #909399;
  font-size: 12px;
}
.summary {
  margin-top: 12px;
  font-size: 14px;
}
.summary b {
  color: #409eff;
}
.err {
  color: #f56c6c;
  margin-left: 12px;
}
.selected-count {
  color: #409eff;
}
.result-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.result-cell {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.result-cell b {
  font-size: 18px;
  color: #1f2d3d;
}
.result-cell span {
  font-size: 12px;
  color: #909399;
}
.pass {
  color: #16a34a;
  font-weight: 600;
}
.fail {
  color: #dc2626;
  font-weight: 600;
}
.retake-line {
  margin-top: 2px;
  font-size: 11px;
  line-height: 1.2;
}
</style>
