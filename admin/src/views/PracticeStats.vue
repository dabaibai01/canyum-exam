<template>
  <div class="stats-page">
    <el-card shadow="never" class="filter-card">
      <div class="page-heading">
        <div class="page-title">{{ pageTitle }}</div>
        <div class="page-desc">{{ pageDesc }}</div>
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
          <el-select v-model="categoryId" style="width: 180px" @change="handleSearch">
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
          <span class="filter-label">人员</span>
          <el-input
            v-model="keyword"
            placeholder="姓名 / 用户名 / 部门"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </div>
        <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <div class="summary-grid" :class="{ six: isExam }">
      <div class="summary-card">
        <div class="summary-icon blue"><el-icon><User /></el-icon></div>
        <div>
          <div class="summary-label">账号总数</div>
          <div class="summary-value">{{ summary.all_users || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon green"><el-icon><TrendCharts /></el-icon></div>
        <div>
          <div class="summary-label">{{ isExam ? '有考试账号' : '有刷题账号' }}</div>
          <div class="summary-value">{{ summary.active_users || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon orange"><el-icon><EditPen /></el-icon></div>
        <div>
          <div class="summary-label">{{ isExam ? '考试答题量' : '刷题量' }}</div>
          <div class="summary-value">{{ summary.answered || 0 }}</div>
        </div>
      </div>
      <div v-if="isExam" class="summary-card">
        <div class="summary-icon blue"><el-icon><Document /></el-icon></div>
        <div>
          <div class="summary-label">考试场次</div>
          <div class="summary-value">{{ summary.exam_count || 0 }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon purple"><el-icon><CircleCheck /></el-icon></div>
        <div>
          <div class="summary-label">整体正确率</div>
          <div class="summary-value">{{ summary.accuracy || 0 }}%</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon gray"><el-icon><Calendar /></el-icon></div>
        <div>
          <div class="summary-label">统计天数</div>
          <div class="summary-value">{{ summary.days || 0 }}</div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="table-head">
          <span class="table-title">{{ isExam ? '考试明细' : '刷题明细' }}</span>
          <span class="table-sub">{{ tableSub }}</span>
        </div>
      </template>

      <el-table :data="items" v-loading="loading" border stripe>
        <el-table-column prop="date" label="日期" width="120" align="center" />
        <el-table-column label="人员" min-width="170">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-line">
                <span class="user-name">{{ row.real_name || row.username }}</span>
                <el-tag v-if="row.is_admin" size="small" type="warning" effect="plain">管理员</el-tag>
              </div>
              <span class="user-account">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" min-width="130" show-overflow-tooltip />
        <el-table-column prop="position" label="岗位" min-width="120" show-overflow-tooltip />
        <el-table-column prop="profession" label="专业" width="120" />
        <el-table-column
          v-if="isExam"
          prop="exam_title"
          label="考试名称"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column
          prop="answered"
          :label="isExam ? '考试答题量' : '刷题量'"
          width="120"
          align="center"
          sortable
        />
        <el-table-column prop="correct" label="答对" width="90" align="center" />
        <el-table-column label="正确率" width="190">
          <template #default="{ row }">
            <div class="accuracy-cell">
              <el-progress
                :percentage="row.accuracy"
                :stroke-width="8"
                :show-text="false"
                :color="accuracyColor(row.accuracy)"
              />
              <span class="accuracy-text" :style="{ color: accuracyColor(row.accuracy) }">{{ row.accuracy }}%</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && !items.length"
        :description="isExam ? '所选条件下暂无考试记录' : '所选条件下暂无刷题记录'"
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
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi, questionApi } from '../api'

const props = defineProps({
  mode: {
    type: String,
    default: 'practice'
  }
})

const isExam = computed(() => props.mode === 'exam')
const pageTitle = computed(() => (isExam.value ? '考试统计' : '刷题统计'))
const pageDesc = computed(() => (
  isExam.value
    ? '在线考试与自己组卷的作答记录，包含管理员账号'
    : '刷题练习的作答记录，包含管理员账号'
))
const tableSub = computed(() => (
  isExam.value
    ? '按日期、专业统计考试答题量与正确率；数据来源为在线考试和自己组卷'
    : '按日期、专业统计刷题量与正确率；数据来源为学员和管理员的刷题记录'
))

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const categoryId = ref(0)
const professionOptions = ref([])
const summary = ref({
  all_users: 0,
  active_users: 0,
  answered: 0,
  correct: 0,
  accuracy: 0,
  days: 0,
  exam_count: 0
})

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
      keyword: keyword.value.trim() || undefined,
      category_id: categoryId.value || 0,
      page: page.value,
      page_size: pageSize.value
    }
    const res = isExam.value
      ? await statsApi.getExamUsers(params)
      : await statsApi.getPracticeUsers(params)
    items.value = res.items || []
    total.value = res.total || 0
    summary.value = res.summary || summary.value
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载统计数据失败')
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
  keyword.value = ''
  categoryId.value = 0
  handleSearch()
}

const accuracyColor = (value) => {
  if (value >= 80) return '#67c23a'
  if (value >= 60) return '#e6a23c'
  return '#f56c6c'
}

watch(() => props.mode, () => {
  page.value = 1
  loadData()
})

onMounted(() => {
  loadProfessions()
  loadData()
})
</script>

<style scoped>
.stats-page {
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
  gap: 14px;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
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
.summary-grid.six {
  grid-template-columns: repeat(6, minmax(0, 1fr));
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
.summary-icon.green {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.12);
}
.summary-icon.orange {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.12);
}
.summary-icon.purple {
  color: #9254de;
  background: rgba(146, 84, 222, 0.12);
}
.summary-icon.gray {
  color: #909399;
  background: rgba(144, 147, 153, 0.12);
}
.summary-label {
  font-size: 12px;
  color: #909399;
}
.summary-value {
  margin-top: 4px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.table-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.table-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}
.table-sub {
  font-size: 12px;
  color: #909399;
}
.user-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.5;
}
.user-line {
  display: flex;
  align-items: center;
  gap: 6px;
}
.user-name {
  font-size: 13px;
  color: #303133;
}
.user-account {
  font-size: 11px;
  color: #909399;
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
.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
