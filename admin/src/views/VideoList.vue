<template>
  <el-card>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <el-button type="primary" @click="openAddDialog">上传视频</el-button>
        <span class="page-tip">支持直接拖入本地视频，自动填入文件地址，不需要手写 URL。</span>
      </div>
    </div>

    <el-table :data="tableData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="视频标题" min-width="180" />
      <el-table-column label="来源" width="100">
        <template #default="scope">
          <el-tag :type="isLocalUrl(scope.row.video_url) ? 'success' : 'info'" effect="plain">
            {{ isLocalUrl(scope.row.video_url) ? '本地文件' : '线上地址' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="时长" width="90">
        <template #default="scope">{{ formatDuration(scope.row.duration) }}</template>
      </el-table-column>
      <el-table-column prop="sort" label="排序" width="80" />
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑视频' : '上传视频'" width="640px" :close-on-click-modal="false">
      <el-form :model="form" label-width="96px">
        <el-form-item label="视频标题" required>
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="例如：第一讲 安全生产基础知识" />
        </el-form-item>
        <el-form-item label="视频描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" placeholder="可选，简单说明视频内容" />
        </el-form-item>

        <el-form-item label="视频文件">
          <div class="upload-block">
            <el-upload
              ref="videoUploadRef"
              drag
              :auto-upload="false"
              :show-file-list="false"
              :limit="1"
              accept=".mp4,.m4v,.webm,.ogg,.ogv"
              :on-change="handleVideoChange"
              :on-remove="clearVideoFile"
              :on-exceed="handleVideoExceed"
            >
              <div class="upload-plus">+</div>
              <div class="el-upload__text">把视频拖到这里，或 <em>点击选择</em></div>
              <template #tip>
                <div class="el-upload__tip">支持 MP4 / WebM / OGG，单个文件最大 512MB。上传后自动填入视频地址。</div>
              </template>
            </el-upload>
            <div v-if="videoFile" class="selected-file">
              <span class="selected-name">{{ videoFile.name }}</span>
              <span class="selected-size">{{ formatSize(videoFile.size) }}</span>
              <el-button link type="danger" @click="clearVideoFile">移除</el-button>
            </div>
            <div v-if="form.video_url" class="current-file">
              <span>当前文件：</span>
              <a :href="form.video_url" target="_blank" rel="noopener">{{ form.video_url }}</a>
            </div>
            <el-progress v-if="uploading" :percentage="uploadProgress" :stroke-width="8" style="margin-top: 10px;" />
          </div>
        </el-form-item>

        <el-form-item label="线上地址">
          <el-input v-model="form.video_url" placeholder="可选；使用本地文件上传时会自动填入，不必手写" />
        </el-form-item>
        <el-form-item label="时长(秒)">
          <el-input-number v-model="form.duration" :min="0" :max="100000" />
          <span class="field-tip">选择本地视频后会自动读取时长</span>
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

const MAX_VIDEO_SIZE = 512 * 1024 * 1024

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const videoFile = ref(null)
const videoUploadRef = ref(null)

const form = ref({
  title: '',
  description: '',
  category_id: null,
  cover_image: null,
  video_url: '',
  duration: 0,
  sort: 0
})

const isLocalUrl = (url) => String(url || '').startsWith('/api/uploads/')

const formatSize = (size) => {
  if (!size) return '0 B'
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
}

const formatDuration = (seconds) => {
  const total = Number(seconds) || 0
  if (!total) return '-'
  const min = Math.floor(total / 60)
  const sec = total % 60
  return `${min}:${String(sec).padStart(2, '0')}`
}

const clearVideoFile = () => {
  videoFile.value = null
  if (videoUploadRef.value) videoUploadRef.value.clearFiles()
}

const handleVideoExceed = () => {
  ElMessage.warning('一次只能选择一个视频，请先移除已选文件')
}

const probeDuration = (file) => new Promise((resolve) => {
  const url = URL.createObjectURL(file)
  const video = document.createElement('video')
  video.preload = 'metadata'
  video.style.display = 'none'
  const done = (value) => {
    URL.revokeObjectURL(url)
    if (video.parentNode) video.parentNode.removeChild(video)
    resolve(value)
  }
  video.onloadedmetadata = () => done(Math.round(video.duration || 0))
  video.onerror = () => done(0)
  video.src = url
  document.body.appendChild(video)
})

const handleVideoChange = async (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return
  if (file.size > MAX_VIDEO_SIZE) {
    ElMessage.error('视频不能超过 512MB，请压缩或分段后再上传')
    clearVideoFile()
    return
  }
  videoFile.value = file
  if (!form.value.title.trim()) {
    form.value.title = file.name.replace(/\.\w+$/, '')
  }
  if (!form.value.duration) {
    const duration = await probeDuration(file)
    if (duration && !form.value.duration) form.value.duration = duration
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await mediaApi.getVideos()
    tableData.value = res
  } catch (error) {
    console.error('加载视频失败', error)
    ElMessage.error('加载视频列表失败')
  } finally {
    loading.value = false
  }
}

const resetUpload = () => {
  clearVideoFile()
  uploading.value = false
  uploadProgress.value = 0
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    title: '',
    description: '',
    category_id: null,
    cover_image: null,
    video_url: '',
    duration: 0,
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
    ElMessage.warning('请填写视频标题')
    return
  }
  if (!videoFile.value && !form.value.video_url.trim()) {
    ElMessage.warning('请拖入本地视频，或填写线上视频地址')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  try {
    if (videoFile.value) {
      const res = await uploadApi.video(videoFile.value, (percent) => {
        uploadProgress.value = percent
      })
      form.value.video_url = res.url
    }

    const payload = {
      title: form.value.title.trim(),
      description: form.value.description?.trim() || null,
      category_id: form.value.category_id || null,
      cover_image: form.value.cover_image || null,
      video_url: form.value.video_url.trim(),
      duration: Number(form.value.duration) || 0,
      sort: Number(form.value.sort) || 0
    }

    if (isEdit.value) {
      await mediaApi.updateVideo(form.value.id, payload)
    } else {
      await mediaApi.createVideo(payload)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '视频上传成功')
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
    await ElMessageBox.confirm('确定要删除这个视频吗？本地文件也会一并清理。', '确认删除', { type: 'warning' })
    await mediaApi.deleteVideo(row.id)
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
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
