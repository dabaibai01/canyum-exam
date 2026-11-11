<template>
  <el-card>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <el-button type="primary" @click="openAddDialog">上传书籍</el-button>
        <span class="page-tip">支持直接拖入 PDF、Word、PPT、Excel 等文档，不需要填写线上地址。</span>
      </div>
    </div>

    <el-table :data="tableData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="书名" min-width="160" />
      <el-table-column prop="author" label="作者" width="110" />
      <el-table-column label="文件" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.file_url ? 'success' : 'info'" effect="plain">
            {{ scope.row.file_url ? (isLocalUrl(scope.row.file_url) ? '本地文件' : '线上地址') : '未上传' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort" label="排序" width="80" />
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑书籍' : '上传书籍'" width="640px" :close-on-click-modal="false">
      <el-form :model="form" label-width="96px">
        <el-form-item label="书名" required>
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="例如：安全生产规章制度汇编" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="form.author" maxlength="100" placeholder="可选" />
        </el-form-item>
        <el-form-item label="书籍描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" placeholder="可选，简单说明文档内容" />
        </el-form-item>

        <el-form-item label="书籍文件">
          <div class="upload-block">
            <el-upload
              ref="bookUploadRef"
              drag
              :auto-upload="false"
              :show-file-list="false"
              :limit="1"
              accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.epub"
              :on-change="handleBookChange"
              :on-remove="clearBookFile"
              :on-exceed="handleBookExceed"
            >
              <div class="upload-plus">+</div>
              <div class="el-upload__text">把文档拖到这里，或 <em>点击选择</em></div>
              <template #tip>
                <div class="el-upload__tip">支持 PDF / DOC / DOCX / PPT / PPTX / XLS / XLSX / TXT / EPUB，单个文件最大 100MB。</div>
              </template>
            </el-upload>
            <div v-if="bookFile" class="selected-file">
              <span class="selected-name">{{ bookFile.name }}</span>
              <span class="selected-size">{{ formatSize(bookFile.size) }}</span>
              <el-button link type="danger" @click="clearBookFile">移除</el-button>
            </div>
            <div v-if="form.file_url" class="current-file">
              <span>当前文件：</span>
              <a v-if="isEdit" :href="`/api/media/books/${form.id}/file`" target="_blank" rel="noopener">打开 / 下载</a>
              <span v-else>{{ form.file_url }}</span>
            </div>
            <el-progress v-if="uploading" :percentage="uploadProgress" :stroke-width="8" style="margin-top: 10px;" />
          </div>
        </el-form-item>

        <el-form-item label="线上地址">
          <el-input v-model="form.file_url" placeholder="可选；使用本地文件上传时会自动填入，不必手写" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="10000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" :disabled="uploading">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleSubmit">
          {{ uploading ? '上传中...' : '确定' }}
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { mediaApi, uploadApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const MAX_BOOK_SIZE = 100 * 1024 * 1024

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const bookFile = ref(null)
const bookUploadRef = ref(null)

const form = ref({
  title: '',
  author: '',
  description: '',
  category_id: null,
  cover_image: null,
  file_url: '',
  sort: 0
})

const isLocalUrl = (url) => String(url || '').startsWith('/api/uploads/')

const formatSize = (size) => {
  if (!size) return '0 B'
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
}

const clearBookFile = () => {
  bookFile.value = null
  if (bookUploadRef.value) bookUploadRef.value.clearFiles()
}

const handleBookExceed = () => {
  ElMessage.warning('一次只能选择一个文档，请先移除已选文件')
}

const handleBookChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return
  if (file.size > MAX_BOOK_SIZE) {
    ElMessage.error('文档不能超过 100MB，请压缩后再上传')
    clearBookFile()
    return
  }
  bookFile.value = file
  if (!form.value.title.trim()) {
    form.value.title = file.name.replace(/\.\w+$/, '')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await mediaApi.getBooks()
    tableData.value = res
  } catch (error) {
    console.error('加载书籍失败', error)
    ElMessage.error('加载书籍列表失败')
  } finally {
    loading.value = false
  }
}

const resetUpload = () => {
  clearBookFile()
  uploading.value = false
  uploadProgress.value = 0
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    title: '',
    author: '',
    description: '',
    category_id: null,
    cover_image: null,
    file_url: '',
    sort: 0
  }
  dialogVisible.value = true
  nextTick(resetUpload)
}

const openEditDialog = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
  nextTick(resetUpload)
}

const handleSubmit = async () => {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写书名')
    return
  }
  if (!bookFile.value && !form.value.file_url.trim()) {
    ElMessage.warning('请拖入本地文档，或填写线上文件地址')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  try {
    if (bookFile.value) {
      const res = await uploadApi.book(bookFile.value, (percent) => {
        uploadProgress.value = percent
      })
      form.value.file_url = res.url
    }

    const payload = {
      title: form.value.title.trim(),
      author: form.value.author?.trim() || null,
      description: form.value.description?.trim() || null,
      category_id: form.value.category_id || null,
      cover_image: form.value.cover_image || null,
      file_url: form.value.file_url.trim(),
      sort: Number(form.value.sort) || 0
    }

    if (isEdit.value) {
      await mediaApi.updateBook(form.value.id, payload)
    } else {
      await mediaApi.createBook(payload)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '书籍上传成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('提交失败', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '提交失败，请检查文件格式和大小')
  } finally {
    uploading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这本书吗？本地文件也会一并清理。', '确认删除', { type: 'warning' })
    await mediaApi.deleteBook(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    // 取消删除
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-tip {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
.upload-block {
  width: 100%;
}
.upload-plus {
  font-size: 34px;
  line-height: 1;
  color: #c0c4cc;
  margin-bottom: 8px;
}
.selected-file,
.current-file {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.selected-name {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.selected-size {
  color: #909399;
}
.current-file a {
  color: #409eff;
}
</style>
