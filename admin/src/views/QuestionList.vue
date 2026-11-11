<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-select v-model="query.categoryId" placeholder="选择分类" style="width: 200px;" @change="reload">
          <el-option label="全部分类" :value="0" />
          <el-option v-for="cat in categories" :key="cat.id" :label="cat.name + '（' + cat.question_count + '）'" :value="cat.id" />
        </el-select>

        <el-select v-model="query.type" placeholder="全部题型" clearable style="width: 130px;" @change="reload">
          <el-option label="单选题" value="single" />
          <el-option label="多选题" value="multiple" />
          <el-option label="判断题" value="judge" />
        </el-select>

        <el-input
          v-model="query.keyword"
          placeholder="搜索题干关键词"
          clearable
          style="width: 240px;"
          @keyup.enter="reload"
          @clear="reload"
        />
        <el-button type="primary" @click="reload">搜索</el-button>
        <el-button @click="resetQuery">重置</el-button>

        <div style="flex: 1;"></div>
        <el-button type="primary" @click="openAddDialog">新增题目</el-button>
      </div>

      <el-table :data="tableData" border v-loading="loading" style="width: 100%;">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column label="分类" width="160">
          <template #default="scope">
            {{ categoryName(scope.row.category_id) }}
          </template>
        </el-table-column>
        <el-table-column label="题型" width="100">
          <template #default="scope">
            <el-tag size="small">{{ typeText(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="题干" show-overflow-tooltip min-width="320" />
        <el-table-column label="选项数" width="90">
          <template #default="scope">
            {{ (scope.row.options || []).length }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="80" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 16px; justify-content: flex-end;"
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑题目' : '新增题目'" width="760px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="form.category_id" filterable style="width: 100%;">
                <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题型">
              <el-select v-model="form.type" style="width: 100%;" @change="onTypeChange">
                <el-option label="单选题" value="single" />
                <el-option label="多选题" value="multiple" />
                <el-option label="判断题" value="judge" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题干">
          <el-input v-model="form.content" type="textarea" :rows="3" placeholder="请输入题干" />
        </el-form-item>

        <el-form-item label="题目图片">
          <div class="image-field">
            <div v-if="form.image" class="image-preview">
              <el-image
                :src="form.image"
                :preview-src-list="[form.image]"
                fit="contain"
                preview-teleported
                class="question-image"
              />
              <div class="image-actions">
                <el-button link type="danger" @click="form.image = ''">移除图片</el-button>
              </div>
            </div>
            <el-upload
              v-else
              action="/api/upload/image"
              :show-file-list="false"
              :http-request="handleImageUpload"
              accept="image/png,image/jpeg,image/webp,image/gif"
            >
              <el-button :loading="imageUploading">上传图片</el-button>
            </el-upload>
            <div class="tip">用于“必须看图”的题。支持 jpg / png / webp / gif，单张不超过 8MB。</div>
          </div>
        </el-form-item>

        <el-form-item label="选项">
          <div style="width: 100%;">
            <div v-for="(opt, i) in form.options" :key="i" class="option-row">
              <span class="option-label">{{ opt.label }}</span>
              <el-input v-model="opt.content" placeholder="选项内容" style="flex: 1;" />
              <el-switch
                v-model="opt.is_correct"
                :active-value="1"
                :inactive-value="0"
                active-text="正确"
                @change="onCorrectChange(i)"
              />
              <el-button
                link
                type="danger"
                :disabled="form.options.length <= 2"
                @click="removeOption(i)"
              >删除</el-button>
            </div>
            <el-button link type="primary" style="margin-top: 6px;" @click="addOption">+ 添加选项</el-button>
            <div class="tip">
              {{ form.type === 'multiple' ? '多选题：可以同时把多个选项设为正确' : '单选/判断题：只能有一个正确选项' }}
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="分值">
              <el-input-number v-model="form.score" :min="0.5" :max="10" :step="0.5" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width: 100%;">
                <el-option label="简单" :value="1" />
                <el-option label="中等" :value="2" />
                <el-option label="困难" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="解析">
          <el-input v-model="form.analysis" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { questionApi, uploadApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

const loading = ref(false)
const submitting = ref(false)
const imageUploading = ref(false)
const tableData = ref([])
const categories = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)

const query = ref({
  categoryId: 0,
  type: '',
  keyword: '',
  page: 1,
  pageSize: 20
})

const form = ref({
  id: null,
  category_id: null,
  type: 'single',
  content: '',
  image: '',
  analysis: '',
  difficulty: 1,
  score: 1,
  options: []
})

const typeText = (type) => {
  const map = { single: '单选题', multiple: '多选题', judge: '判断题' }
  return map[type] || type
}

const categoryName = (id) => {
  const cat = categories.value.find(c => c.id === id)
  return cat ? cat.name : '未分类'
}

const loadCategories = async () => {
  try {
    const res = await questionApi.getCategories('question', true)
    categories.value = res
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await questionApi.getQuestionPage({
      category_id: query.value.categoryId,
      type: query.value.type || undefined,
      keyword: query.value.keyword || undefined,
      show_all: true,
      page: query.value.page,
      page_size: query.value.pageSize
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载题目失败', error)
    ElMessage.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

const reload = () => {
  query.value.page = 1
  loadData()
}

const resetQuery = () => {
  query.value.categoryId = 0
  query.value.type = ''
  query.value.keyword = ''
  reload()
}

const defaultOptions = () => ([
  { label: 'A', content: '', is_correct: 0 },
  { label: 'B', content: '', is_correct: 0 }
])

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    id: null,
    category_id: categories.value.length ? categories.value[0].id : null,
    type: 'single',
    content: '',
    image: '',
    analysis: '',
    difficulty: 1,
    score: 1,
    options: defaultOptions()
  }
  dialogVisible.value = true
}

const openEditDialog = async (row) => {
  isEdit.value = true
  try {
    const detail = await questionApi.getQuestion(row.id)
    const options = (detail.options || []).map(o => ({
      label: o.label,
      content: o.content,
      is_correct: o.is_correct ? 1 : 0
    }))
    form.value = {
      id: detail.id,
      category_id: detail.category_id,
      type: detail.type,
      content: detail.content,
      image: detail.image || '',
      analysis: detail.analysis || '',
      difficulty: detail.difficulty || 1,
      score: Number(detail.score) || 1,
      options: options.length ? options : defaultOptions()
    }
    dialogVisible.value = true
  } catch (error) {
    console.error('加载题目详情失败', error)
    ElMessage.error('加载题目详情失败')
  }
}

const onTypeChange = (type) => {
  if (type === 'judge') {
    form.value.options = [
      { label: 'A', content: '对', is_correct: 1 },
      { label: 'B', content: '错', is_correct: 0 }
    ]
    return
  }
  // 单选/多选保持已有选项，单选题只保留一个正确项
  if (type === 'single') {
    const first = form.value.options.find(o => o.is_correct === 1)
    form.value.options.forEach(o => { o.is_correct = first && o === first ? 1 : 0 })
  }
}

const onCorrectChange = (index) => {
  // 单选和判断题只能有一个正确选项
  if (form.value.type !== 'multiple') {
    form.value.options.forEach((o, i) => {
      if (i !== index) o.is_correct = 0
    })
  }
}

const addOption = () => {
  if (form.value.options.length >= LABELS.length) {
    ElMessage.warning('最多支持 10 个选项')
    return
  }
  const nextLabel = LABELS[form.value.options.length]
  form.value.options.push({ label: nextLabel, content: '', is_correct: 0 })
}

const removeOption = (index) => {
  if (form.value.options.length <= 2) return
  form.value.options.splice(index, 1)
  form.value.options.forEach((o, i) => { o.label = LABELS[i] })
}

const handleImageUpload = async ({ file, onSuccess, onError }) => {
  imageUploading.value = true
  try {
    const res = await uploadApi.image(file)
    form.value.image = res.url
    onSuccess(res)
    ElMessage.success('图片上传成功')
  } catch (error) {
    console.error('图片上传失败', error)
    onError(error)
    ElMessage.error(error.response?.data?.detail || '图片上传失败')
  } finally {
    imageUploading.value = false
  }
}

const handleSubmit = async () => {
  if (!form.value.category_id) {
    ElMessage.warning('请选择分类')
    return
  }
  if (!form.value.content.trim()) {
    ElMessage.warning('请填写题干')
    return
  }
  const options = form.value.options.filter(o => o.content.trim())
  if (options.length < 2) {
    ElMessage.warning('至少需要两个有内容的选项')
    return
  }
  const correctCount = options.filter(o => o.is_correct === 1).length
  if (correctCount === 0) {
    ElMessage.warning('请至少设置一个正确选项')
    return
  }
  if (form.value.type !== 'multiple' && correctCount > 1) {
    ElMessage.warning('单选题和判断题只能有一个正确选项')
    return
  }

  const payload = {
    category_id: form.value.category_id,
    type: form.value.type,
    content: form.value.content.trim(),
    image: form.value.image || null,
    analysis: form.value.analysis || null,
    difficulty: form.value.difficulty,
    score: form.value.score,
    options: options.map((o, i) => ({
      label: LABELS[i],
      content: o.content.trim(),
      is_correct: o.is_correct ? 1 : 0,
      sort: i + 1
    }))
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await questionApi.updateQuestion(form.value.id, payload)
    } else {
      await questionApi.createQuestion(payload)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '新增成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('提交失败', error)
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这道题吗？', '确认删除', { type: 'warning' })
    await questionApi.deleteQuestion(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    // 取消删除
  }
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.option-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.option-label {
  width: 20px;
  font-weight: 600;
}
.tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.image-field {
  width: 100%;
}
.image-preview {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.question-image {
  width: 200px;
  height: 130px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #f7f8fa;
}
.image-actions {
  padding-top: 4px;
}
</style>
