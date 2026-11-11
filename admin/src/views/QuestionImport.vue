<template>
  <div class="import-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-title">批量导入题库</span>
          <el-button link type="primary" @click="downloadTemplate">下载 CSV 模板</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon class="tip">
        <template #title>导入前请先看这里</template>
        <div class="tip-line">1. 支持 .xlsx 和 .csv；.xls 请先在 Excel 里另存为 .xlsx。</div>
        <div class="tip-line">2. 分类必须已经存在（填分类名称或分类ID），否则该行会失败；可先到「分类管理」建好分类。</div>
        <div class="tip-line">3. 单选/多选题至少要填两个选项；判断题选项可以不填，系统自动生成“对/错”。</div>
        <div class="tip-line">4. 正确答案填选项字母，例如 A 或 ABD；判断题也可填“对/错”。</div>
        <div class="tip-line">5. 同分类、同题型、同题干视为重复，自动跳过；单次最多 5000 道。</div>
      </el-alert>

      <div class="upload-row">
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          accept=".xlsx,.csv"
          :on-change="handleFileChange"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">把 Excel / CSV 文件拖到这里，或点击选择</div>
          <div class="upload-sub">仅支持 .xlsx / .csv，文件不超过 20MB</div>
        </el-upload>
      </div>

      <div v-if="selectedFile" class="file-row">
        <div class="file-name">
          <el-icon><Document /></el-icon>
          <span>{{ selectedFile.name }}</span>
          <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
        </div>
        <div class="file-actions">
          <el-button link type="danger" @click="clearFile">移除</el-button>
          <el-button type="primary" :loading="importing" @click="startImport">开始导入</el-button>
        </div>
      </div>
    </el-card>

    <el-card v-if="result" shadow="never" class="result-card">
      <template #header>
        <div class="card-head">
          <span class="card-title">导入结果</span>
          <el-button link @click="result = null">关闭</el-button>
        </div>
      </template>

      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-label">总行数</div>
          <div class="summary-value">{{ result.total }}</div>
        </div>
        <div class="summary-item success">
          <div class="summary-label">成功导入</div>
          <div class="summary-value">{{ result.success }}</div>
        </div>
        <div class="summary-item warning">
          <div class="summary-label">重复跳过</div>
          <div class="summary-value">{{ result.duplicates }}</div>
        </div>
        <div class="summary-item danger">
          <div class="summary-label">失败</div>
          <div class="summary-value">{{ result.failed }}</div>
        </div>
      </div>

      <el-alert
        v-if="result.success > 0"
        type="success"
        :closable="false"
        show-icon
        class="result-tip"
        :title="`已成功导入 ${result.success} 道题，可到「题目列表」查看`"
      />
      <el-alert
        v-if="result.failed > 0"
        type="warning"
        :closable="false"
        show-icon
        class="result-tip"
        title="有失败行，请按下面的行号和原因修正后重新导入（成功的题已入库，不会重复）"
      />

      <el-table v-if="result.errors?.length" :data="result.errors" border size="small" class="error-table">
        <el-table-column prop="row" label="Excel 行号" width="110" align="center" />
        <el-table-column prop="message" label="失败原因" min-width="320" />
      </el-table>
      <div v-if="result.failed > result.errors?.length" class="more-tip">
        仅展示前 {{ result.errors?.length || 0 }} 条失败原因，请先修正这些行再重新导入。
      </div>
    </el-card>

    <el-card shadow="never" class="format-card">
      <template #header>
        <span class="card-title">表头格式说明</span>
      </template>
      <el-table :data="formatRows" border size="small">
        <el-table-column prop="name" label="列名" width="160" />
        <el-table-column prop="required" label="是否必填" width="110" align="center" />
        <el-table-column prop="desc" label="说明" min-width="300" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { questionApi } from '../api'

const selectedFile = ref(null)
const importing = ref(false)
const result = ref(null)

const formatRows = [
  { name: '分类 / 专业', required: '必填', desc: '填已有分类名称，例如“内燃-第1模块”“电力-第1模块”“安全规章-第1模块”；也可改用“分类ID”列' },
  { name: '题型', required: '必填', desc: '单选题 / 多选题 / 判断题' },
  { name: '题干', required: '必填', desc: '题目正文；也可写“题目”或“content”' },
  { name: '正确答案', required: '必填', desc: '单选填 A；多选填 ABD；判断题填 对/错 或 A/B' },
  { name: '选项A ~ 选项J', required: '单选/多选必填', desc: '每个选项一行一列；判断题留空即自动生成“对/错”' },
  { name: '解析', required: '选填', desc: '答案解析' },
  { name: '分值', required: '选填', desc: '0.5 ~ 10，默认 1' },
  { name: '难度', required: '选填', desc: '简单 / 中等 / 困难，默认简单' },
  { name: '图片', required: '选填', desc: '题目图片地址，例如 /api/uploads/xxx.png' }
]

const formatSize = (size) => {
  if (!size) return '0 KB'
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw || uploadFile
  if (!file) return
  const lower = (file.name || '').toLowerCase()
  if (!lower.endsWith('.xlsx') && !lower.endsWith('.csv')) {
    ElMessage.warning('只支持 .xlsx 或 .csv 文件')
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning('文件不能超过 20MB')
    return
  }
  selectedFile.value = file
  result.value = null
}

const clearFile = () => {
  selectedFile.value = null
  result.value = null
}

const startImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  importing.value = true
  try {
    const res = await questionApi.importQuestions(selectedFile.value)
    result.value = res
    if (res.success > 0) {
      ElMessage.success(`成功导入 ${res.success} 道题`)
    } else {
      ElMessage.warning('没有成功导入的题目，请检查失败原因')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  const headers = ['分类', '题型', '题干', '正确答案', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F', '选项G', '选项H', '选项I', '选项J', '解析', '分值', '难度', '图片']
  const rows = [
    headers,
    ['内燃-第1模块', '单选题', '内燃机车某部件的作用是什么？', 'A', '选项一内容', '选项二内容', '选项三内容', '选项四内容', '', '', '', '', '', '', '这里是答案解析', '1', '简单', ''],
    ['内燃-第1模块', '多选题', '下列哪些属于安全操作要求？', 'ABD', '选项一内容', '选项二内容', '选项三内容', '选项四内容', '', '', '', '', '', '', '这里是答案解析', '1', '中等', ''],
    ['内燃-第1模块', '判断题', '该操作符合安全规程。', '对', '', '', '', '', '', '', '', '', '', '', '这里是答案解析', '1', '简单', '']
  ]
  const quote = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const csv = '\ufeff' + rows.map(row => row.map(quote).join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '题库导入模板.csv'
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.import-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}
.tip-line {
  font-size: 13px;
  line-height: 1.9;
  color: #606266;
}
.upload-row {
  margin-top: 18px;
}
.upload-icon {
  font-size: 46px;
  color: #409eff;
  margin-bottom: 10px;
}
.upload-text {
  font-size: 14px;
  color: #303133;
}
.upload-sub {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 12px 14px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}
.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
}
.file-size {
  font-size: 12px;
  color: #909399;
}
.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.result-card {
  border-top: 3px solid #409eff;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.summary-item {
  padding: 14px;
  border-radius: 8px;
  background: #f5f7fa;
  text-align: center;
}
.summary-label {
  font-size: 12px;
  color: #909399;
}
.summary-value {
  margin-top: 6px;
  font-size: 26px;
  font-weight: 600;
  color: #303133;
}
.summary-item.success .summary-value {
  color: #67c23a;
}
.summary-item.warning .summary-value {
  color: #e6a23c;
}
.summary-item.danger .summary-value {
  color: #f56c6c;
}
.result-tip {
  margin-top: 14px;
}
.error-table {
  margin-top: 14px;
}
.more-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
.format-card {
  margin-bottom: 24px;
}
</style>
