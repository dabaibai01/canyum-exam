<template>
  <el-card>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; gap: 10px;">
        <el-input
          v-model="keyword"
          placeholder="搜索公告标题"
          style="width: 240px;"
          clearable
          @keyup.enter="loadData"
          @clear="loadData"
        />
        <el-select v-model="statusFilter" placeholder="全部状态" style="width: 130px;" @change="loadData">
          <el-option label="全部状态" :value="null" />
          <el-option label="已发布" :value="1" />
          <el-option label="草稿" :value="0" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
      </div>
      <el-button type="primary" @click="openCreate">新建公告</el-button>
    </div>

    <el-table :data="tableData" border v-loading="loading" size="small">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="88">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
            {{ scope.row.status === 1 ? '已发布' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="150">
        <template #default="scope"><span style="font-size: 12px;">{{ formatTime(scope.row.updated_at) }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button>
          <el-button
            link
            :type="scope.row.status === 1 ? 'warning' : 'success'"
            @click="toggleStatus(scope.row)"
          >
            {{ scope.row.status === 1 ? '下线' : '发布' }}
          </el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin-top: 16px; justify-content: flex-end;"
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @current-change="loadData"
      @size-change="loadData"
    />

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑公告' : '新建公告'" width="620px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="120" show-word-limit placeholder="例如：关于开展 11 月月度抽考的通知" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="公告正文，学员端点击公告可查看全文"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="0">保存为草稿</el-radio>
            <el-radio :value="1">立即发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div class="preview">
        <div class="preview-title">学员端预览</div>
        <div class="notice-bar">
          <span class="icon">📢</span>
          <span class="text">{{ form.title || '公告标题' }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { noticeApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref(null)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ title: '', content: '', status: 1 })

const formatTime = (v) => {
  if (!v) return ''
  const d = new Date(String(v).endsWith('Z') ? v : v + 'Z')
  if (Number.isNaN(d.getTime())) return v
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await noticeApi.getList({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: statusFilter.value === null ? undefined : statusFilter.value
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('加载公告失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  editId.value = null
  form.value = { title: '', content: '', status: 1 }
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = { title: row.title, content: row.content, status: row.status }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!form.value.content.trim()) {
    ElMessage.warning('请填写公告内容')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      const res = await noticeApi.updateNotice(editId.value, {
        title: form.value.title,
        content: form.value.content,
        status: form.value.status
      })
      ElMessage.success(res.status === 1 ? '已保存并发布' : '已保存为草稿')
    } else {
      const res = await noticeApi.createNotice({
        title: form.value.title,
        content: form.value.content,
        status: form.value.status
      })
      ElMessage.success(res.status === 1 ? '公告已发布' : '已存为草稿')
    }
    dialogVisible.value = false
    loadData()
  } catch (error) {
    const msg = error.response?.data?.detail
    ElMessage.error(typeof msg === 'string' ? msg : '保存失败')
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  const target = row.status === 1 ? 0 : 1
  try {
    await noticeApi.updateNotice(row.id, { status: target })
    ElMessage.success(target === 1 ? '公告已发布，学员端可见' : '公告已下线，学员端不再显示')
    loadData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除公告「${row.title}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (e) {
    return
  }
  try {
    await noticeApi.deleteNotice(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.preview {
  margin-top: 8px;
  padding: 12px 14px;
  background: #f7f8fa;
  border-radius: 6px;
}
.preview-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}
.notice-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 12px;
  background: #fffbe8;
  color: #ed6a0c;
  border-radius: 4px;
  font-size: 14px;
}
.notice-bar .text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
