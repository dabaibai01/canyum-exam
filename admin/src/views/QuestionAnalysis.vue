<template>
  <div class="analysis-page">
    <el-card shadow="never" class="filter-card">
      <div class="page-heading">
        <div class="page-title">题目分析</div>
        <div class="page-desc">
          按题目汇总刷题与考试的作答情况，快速定位“哪道题错的人最多”，用于重点出题和集中讲解。
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">日期范围</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :clearable="false"
            @change="handleSearch"
          />
        </div>
        <div class="filter-item">
          <span class="filter-label">专业</span>
          <el-select v-model="categoryId" style="width: 160px" @change="handleSearch">
            <el-option label="全部专业" :value="0" />
            <el-option
              v-for="cat in professionOptions"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">题型</span>
          <el-select v-model="type" placeholder="全部题型" style="width: 130px" @change="handleSearch">
            <el-option label="全部题型" value="" />
            <el-option label="单选题" value="single" />
            <el-option label="多选题" value="multiple" />
            <el-option label="判断题" value="judge" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">数据来源</span>
          <el-select v-model="source" style="width: 130px" @change="handleSearch">
            <el-option label="全部来源" value="all" />
            <el-option label="刷题" value="practice" />
            <el-option label="考试" value="exam" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">题干</span>
          <el-input
            v-model="keyword"
            placeholder="输入题干关键词"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </div>
        <div class="filter-item">
          <span class="filter-label">排序</span>
          <el-select v-model="sort" style="width: 150px" @change="handleSearch">
            <el-option label="错得最多" value="wrong_count" />
            <el-option label="错误率最高" value="wrong_rate" />
            <el-option label="作答最多" value="answered" />
          </el-select>
        </div>
        <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-icon blue"><el-icon><Document /></el-icon></div>
        <div>
          <div class="summary-label">有作答的题目</div>
          <div class="summary-value">{{ summary.question_count || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon orange"><el-icon><EditPen /></el-icon></div>
        <div>
          <div class="summary-label">作答总量</div>
          <div class="summary-value">{{ summary.answered || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon red"><el-icon><Warning /></el-icon></div>
        <div>
          <div class="summary-label">错题总量</div>
          <div class="summary-value">{{ summary.wrong || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon green"><el-icon><CircleCheck /></el-icon></div>
        <div>
          <div class="summary-label">整体正确率</div>
          <div class="summary-value">{{ summary.accuracy || 0 }}%</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon purple"><el-icon><TrendCharts /></el-icon></div>
        <div>
          <div class="summary-label">高频错题（≥3次且错误率≥50%）</div>
          <div class="summary-value">{{ summary.high_wrong || 0 }}</div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="table-head">
          <div>
            <span class="table-title">题目作答排行</span>
            <span class="table-sub">默认按答错次数排序，可切换错误率或作答量；勾选题目可直接组成重点考试卷，或点“查看”查看正确项与错选分布</span>
          </div>
          <el-button
            type="primary"
            :disabled="selectedRows.length === 0"
            @click="openComposeDialog"
          >
            用选中题组卷（{{ selectedRows.length }}）
          </el-button>
        </div>
      </template>

      <el-table
        :data="items"
        v-loading="loading"
        border
        stripe
        row-key="question_id"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="46" reserve-selection />
        <el-table-column label="题目" min-width="240">
          <template #default="{ row }">
            <div class="question-cell">
              <span class="q-id">#{{ row.question_id }}</span>
              <span class="q-content">{{ row.content }}</span>
              <span v-if="row.image" class="q-img-tag">含图片</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type_label" label="题型" width="80" align="center" />
        <el-table-column prop="profession" label="专业" width="90" show-overflow-tooltip />
        <el-table-column prop="category_name" label="模块" width="100" show-overflow-tooltip />
        <el-table-column prop="answered" label="作答量" width="72" align="center" sortable />
        <el-table-column prop="wrong" label="答错" width="64" align="center" sortable />
        <el-table-column label="错误率" width="130">
          <template #default="{ row }">
            <div class="accuracy-cell">
              <el-progress
                :percentage="row.wrong_rate"
                :stroke-width="8"
                :show-text="false"
                :color="wrongColor(row.wrong_rate)"
              />
              <span class="accuracy-text" :style="{ color: wrongColor(row.wrong_rate) }">
                {{ row.wrong_rate }}%
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="users" label="涉及人数" width="76" align="center" />
        <el-table-column label="主要错选" min-width="130">
          <template #default="{ row }">
            <div class="wrong-answer-cell">
              <el-tag
                v-for="opt in row.wrong_answers.slice(0, 3)"
                :key="opt.answer"
                size="small"
                type="danger"
                effect="plain"
              >{{ opt.answer }} · {{ opt.count }} 人</el-tag>
              <span v-if="!row.wrong_answers.length" class="muted">暂无错选</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="76" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && !items.length"
        description="所选条件下暂无作答记录，试试扩大日期范围或切换数据来源"
      />

      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="题目分析" size="560px">
      <div v-if="detail" class="detail-wrap">
        <div class="detail-meta">
          <el-tag size="small">{{ detail.type_label }}</el-tag>
          <el-tag size="small" type="info">{{ detail.profession }} · {{ detail.category_name }}</el-tag>
          <el-tag size="small" type="success">正确答案 {{ detail.correct_answer }}</el-tag>
        </div>
        <div class="detail-content">{{ detail.content }}</div>
        <img v-if="detail.image" :src="detail.image" class="detail-image" alt="题目图片" />

        <div class="detail-stats">
          <div><b>{{ detail.answered }}</b><span>作答量</span></div>
          <div><b class="danger">{{ detail.wrong }}</b><span>答错</span></div>
          <div><b>{{ detail.wrong_rate }}%</b><span>错误率</span></div>
          <div><b>{{ detail.users }}</b><span>涉及人数</span></div>
          <div><b>{{ detail.practice_answered }}</b><span>刷题作答</span></div>
          <div><b>{{ detail.exam_answered }}</b><span>考试作答</span></div>
        </div>

        <div class="detail-section-title">选项与错选分布</div>
        <div class="option-list">
          <div
            v-for="opt in detail.options"
            :key="opt.id"
            class="option-row"
            :class="{ correct: opt.is_correct }"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-content">{{ opt.content }}</span>
            <el-tag v-if="opt.is_correct" size="small" type="success" effect="plain">正确项</el-tag>
            <el-tag
              v-for="w in detail.wrong_answers.filter(x => x.answer === opt.label)"
              :key="w.answer"
              size="small"
              type="danger"
              effect="plain"
            >{{ w.count }} 人选错</el-tag>
          </div>
        </div>

        <div class="detail-section-title">解析</div>
        <div class="analysis-text">{{ detail.analysis || '这道题暂无解析，可以在题库管理中补充。' }}</div>

        <div class="detail-actions">
          <el-button type="primary" @click="openComposeFromDetail">用这道题组卷</el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="composeVisible" title="用高频错题组卷" width="520px" destroy-on-close>
      <el-form :model="composeForm" label-width="96px">
        <el-form-item label="考试名称">
          <el-input v-model="composeForm.title" placeholder="例如：高频错题重点讲解卷" />
        </el-form-item>
        <el-form-item label="已选题目">
          <span class="compose-count">{{ composeIds.length }} 道，共 {{ composeTotalScore }} 分</span>
        </el-form-item>
        <el-form-item label="考试时长">
          <el-input-number v-model="composeForm.duration" :min="5" :max="300" />
          <span class="unit">分钟</span>
        </el-form-item>
        <el-form-item label="及格分">
          <el-input-number
            v-model="composeForm.pass_score"
            :min="0"
            :max="composeTotalScore || 1000"
            :step="0.5"
          />
          <span class="unit">默认按总分 60% 计算</span>
        </el-form-item>
        <el-form-item label="立即发布">
          <el-switch v-model="composeForm.publish" />
          <span class="unit">关闭时保存为草稿，可在考试管理中继续编辑</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="composeVisible = false">取消</el-button>
        <el-button type="primary" :loading="composeLoading" @click="submitCompose">创建考试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, Document, EditPen, TrendCharts, Warning } from '@element-plus/icons-vue'
import { examApi, questionApi, statsApi } from '../api'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const categoryId = ref(0)
const type = ref('')
const source = ref('all')
const sort = ref('wrong_count')
const professionOptions = ref([])
const summary = ref({
  question_count: 0,
  answered: 0,
  correct: 0,
  wrong: 0,
  accuracy: 0,
  high_wrong: 0
})

const detailVisible = ref(false)
const detail = ref(null)

const selectedRows = ref([])
const composeVisible = ref(false)
const composeLoading = ref(false)
const composeIds = ref([])
const composeForm = ref({ title: '', duration: 60, pass_score: 60, publish: false })

const formatDay = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const defaultRange = () => {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 6)
  return [formatDay(start), formatDay(end)]
}

const dateRange = ref(defaultRange())

const composeTotalScore = computed(() =>
  selectedRows.value.reduce((sum, row) => sum + Number(row.score || 0), 0)
)

const loadProfessions = async () => {
  try {
    const categories = await questionApi.getCategories('question')
    professionOptions.value = categories.filter(c => !c.parent_id || c.parent_id === 0)
  } catch (error) {
    console.error('加载专业分类失败', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      category_id: categoryId.value || 0,
      type: type.value || undefined,
      source: source.value,
      keyword: keyword.value.trim() || undefined,
      sort: sort.value,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await statsApi.getQuestionAnalysis(params)
    items.value = res.items || []
    total.value = res.total || 0
    summary.value = res.summary || summary.value
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载题目分析失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const resetFilters = () => {
  dateRange.value = defaultRange()
  categoryId.value = 0
  type.value = ''
  source.value = 'all'
  sort.value = 'wrong_count'
  keyword.value = ''
  handleSearch()
}

const wrongColor = (value) => {
  if (value >= 60) return '#f56c6c'
  if (value >= 30) return '#e6a23c'
  return '#67c23a'
}

const onSelectionChange = (rows) => {
  selectedRows.value = rows
}

const openDetail = (row) => {
  detail.value = row
  detailVisible.value = true
}

const openComposeDialog = () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先勾选要组卷的题目')
    return
  }
  composeIds.value = selectedRows.value.map(row => row.question_id)
  const totalScore = selectedRows.value.reduce((sum, row) => sum + Number(row.score || 0), 0)
  composeForm.value = {
    title: `高频错题重点卷 · ${formatDay(new Date()).slice(5)}`,
    duration: 60,
    pass_score: Math.round(totalScore * 0.6 * 10) / 10,
    publish: false
  }
  composeVisible.value = true
}

const openComposeFromDetail = () => {
  if (!detail.value) return
  selectedRows.value = [detail.value]
  openComposeDialog()
  detailVisible.value = false
}

const submitCompose = async () => {
  if (!composeForm.value.title.trim()) {
    ElMessage.warning('请填写考试名称')
    return
  }
  if (!composeIds.value.length) {
    ElMessage.warning('没有可组卷的题目')
    return
  }
  composeLoading.value = true
  try {
    await examApi.createExam({
      title: composeForm.value.title.trim(),
      description: '从题目分析中挑选高频错题组卷，建议用于重点讲解后的小测',
      category_id: null,
      duration: composeForm.value.duration,
      pass_score: composeForm.value.pass_score,
      status: composeForm.value.publish ? 1 : 0,
      allow_retake: 0,
      retake_limit: 0,
      question_ids: composeIds.value
    })
    ElMessage.success('考试已创建，可在“考试管理”中查看并发布')
    composeVisible.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建考试失败')
  } finally {
    composeLoading.value = false
  }
}

onMounted(() => {
  loadProfessions()
  loadData()
})
</script>

<style scoped>
.analysis-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-heading {
  margin-bottom: 14px;
}
.page-title {
  font-size: 17px;
  font-weight: 600;
  color: #1f2d3d;
}
.page-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 7px;
}
.filter-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}
.summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}
.summary-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.summary-icon.blue {
  color: #409eff;
  background: rgba(64, 158, 255, 0.12);
}
.summary-icon.orange {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.12);
}
.summary-icon.red {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.12);
}
.summary-icon.green {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.12);
}
.summary-icon.purple {
  color: #9254de;
  background: rgba(146, 84, 222, 0.12);
}
.summary-label {
  font-size: 12px;
  color: #909399;
  line-height: 1.3;
}
.summary-value {
  margin-top: 4px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.table-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}
.table-sub {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
.question-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.q-id {
  flex: none;
  color: #909399;
  font-size: 12px;
}
.q-content {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.q-img-tag {
  flex: none;
  font-size: 11px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  padding: 1px 5px;
}
.accuracy-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.accuracy-cell .el-progress {
  flex: 1;
}
.accuracy-text {
  width: 44px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
}
.wrong-answer-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.muted {
  color: #c0c4cc;
  font-size: 12px;
}
.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.detail-wrap {
  padding: 0 4px 12px;
}
.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.detail-content {
  margin-top: 14px;
  font-size: 15px;
  line-height: 1.7;
  color: #303133;
  white-space: pre-wrap;
}
.detail-image {
  display: block;
  max-width: 100%;
  margin-top: 12px;
  border-radius: 6px;
}
.detail-stats {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}
.detail-stats > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.detail-stats b {
  font-size: 20px;
  color: #303133;
}
.detail-stats .danger {
  color: #f56c6c;
}
.detail-stats span {
  font-size: 12px;
  color: #909399;
}
.detail-section-title {
  margin: 18px 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.option-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 6px;
  background: #f7f8fa;
  font-size: 13px;
}
.option-row.correct {
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
}
.option-label {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #dcdfe6;
  color: #606266;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}
.option-row.correct .option-label {
  background: #67c23a;
  color: #fff;
}
.option-content {
  flex: 1;
  color: #303133;
  white-space: pre-wrap;
}
.analysis-text {
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
  background: #fafafa;
  border-radius: 6px;
  padding: 10px 12px;
}
.detail-actions {
  margin-top: 18px;
}
.compose-count {
  color: #409eff;
  font-weight: 600;
}
.unit {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
