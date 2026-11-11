<template>
  <div v-loading="loading">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
            <div class="stat-sub" v-if="card.sub">{{ card.sub }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>最近 7 天答题趋势</template>
          <div ref="trendRef" class="chart" style="height: 320px;"></div>
          <div class="chart-tip">数据来源：学员每次提交答案都会记录一条答题明细</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>题型分布</template>
          <div ref="pieRef" class="chart" style="height: 320px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>各专业题量</template>
          <div ref="categoryRef" class="chart" style="height: 240px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { statsApi } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const stats = ref({
  total_questions: 0,
  total_users: 0,
  total_exams: 0,
  ongoing_exams: 0,
  today_answers: 0,
  today_correct_rate: 0,
  total_answers: 0,
  type_stats: [],
  category_stats: [],
  daily_stats: []
})

const trendRef = ref(null)
const pieRef = ref(null)
const categoryRef = ref(null)

let chartInstances = []

const fmt = (n) => (n === null || n === undefined ? 0 : Number(n).toLocaleString())

const cards = computed(() => ([
  { label: '总题目数', value: fmt(stats.value.total_questions), color: '#409EFF', sub: '' },
  { label: '注册用户', value: fmt(stats.value.total_users), color: '#67C23A', sub: '' },
  {
    label: '进行中考试',
    value: fmt(stats.value.ongoing_exams),
    color: '#E6A23C',
    sub: `共 ${fmt(stats.value.total_exams)} 场考试`
  },
  {
    label: '今日答题人次',
    value: fmt(stats.value.today_answers),
    color: '#F56C6C',
    sub: stats.value.today_answers > 0 ? `正确率 ${stats.value.today_correct_rate}%` : '今天还没有人答题'
  }
]))

const initChart = (el, option) => {
  if (!el) return
  const instance = echarts.init(el)
  instance.setOption(option)
  chartInstances.push(instance)
}

const renderCharts = () => {
  // 1. 近 7 天答题趋势
  const daily = stats.value.daily_stats || []
  initChart(trendRef.value, {
    tooltip: { trigger: 'axis' },
    legend: { data: ['答题量', '答对数'], top: 0 },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: daily.map(d => d.date) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '答题量',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        itemStyle: { color: '#409EFF' },
        areaStyle: { opacity: 0.12 },
        data: daily.map(d => d.answered)
      },
      {
        name: '答对数',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        itemStyle: { color: '#67C23A' },
        data: daily.map(d => d.correct)
      }
    ]
  })

  // 2. 题型分布
  const types = stats.value.type_stats || []
  initChart(pieRef.value, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 题 ({d}%)' },
    legend: {
      bottom: 0,
      icon: 'circle',
      formatter: (name) => {
        const item = types.find(t => t.name === name)
        return item ? `${name} ${item.value} 题` : name
      }
    },
    series: [{
      type: 'pie',
      radius: ['42%', '64%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold', formatter: '{b}\n{d}%' }
      },
      data: types.map(t => ({ name: t.name, value: t.value })),
      color: ['#409EFF', '#67C23A', '#E6A23C', '#909399']
    }]
  })

  // 3. 各专业题量
  const cats = stats.value.category_stats || []
  initChart(categoryRef.value, {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 90, right: 40, top: 20, bottom: 20 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', inverse: true, data: cats.map(c => c.name) },
    series: [{
      type: 'bar',
      barWidth: 22,
      itemStyle: { color: '#409EFF', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', formatter: '{c}' },
      data: cats.map(c => c.value)
    }]
  })
}

const loadData = async () => {
  loading.value = true
  try {
    stats.value = await statsApi.getDashboard()
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('加载统计数据失败', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  chartInstances.forEach(c => c.resize())
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstances.forEach(c => c.dispose())
  chartInstances = []
})
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 6px 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 600;
}
.stat-label {
  color: #909399;
  margin-top: 8px;
}
.stat-sub {
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 6px;
  min-height: 16px;
}
.chart-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
