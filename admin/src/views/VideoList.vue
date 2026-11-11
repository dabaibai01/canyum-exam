<template>
  <el-card>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between;">
      <el-button type="primary" @click="openAddDialog">上传视频</el-button>
    </div>

    <el-table :data="tableData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="视频标题" />
      <el-table-column prop="category" label="分类" width="150" />
      <el-table-column prop="duration" label="时长" width="100" />
      <el-table-column prop="sort" label="排序" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑视频' : '上传视频'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="视频标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="视频描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="视频链接">
          <el-input v-model="form.video_url" placeholder="视频URL地址" />
        </el-form-item>
        <el-form-item label="时长(秒)">
          <el-input-number v-model="form.duration" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { mediaApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)

const form = ref({
  title: '',
  description: '',
  video_url: '',
  duration: 0,
  sort: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await mediaApi.getVideos()
    tableData.value = res
  } catch (error) {
    console.error('加载视频失败', error)
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = { title: '', description: '', video_url: '', duration: 0, sort: 0 }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await mediaApi.updateVideo(form.value.id, form.value)
    } else {
      await mediaApi.createVideo(form.value)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '上传成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('提交失败', error)
    ElMessage.error('提交失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个视频吗？', '确认删除', { type: 'warning' })
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
