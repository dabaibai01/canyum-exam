<template>
  <el-card>
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="search"
          placeholder="搜索用户名/姓名"
          clearable
          style="width: 220px;"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 130px;" @change="handleSearch">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button type="primary" plain @click="handleSearch">查询</el-button>
        <el-tag v-if="pendingCount > 0" type="warning" effect="dark">
          待审核 {{ pendingCount }}
        </el-tag>
      </div>
      <el-button type="primary" @click="openAddDialog">新增用户</el-button>
    </div>

    <el-table :data="tableData" border v-loading="loading">
      <el-table-column prop="id" label="ID" width="42" />
      <el-table-column prop="username" label="用户名" width="90" show-overflow-tooltip />
      <el-table-column label="姓名" width="95">
        <template #default="scope">
          <div class="cell-main">{{ scope.row.real_name }}</div>
          <el-tag v-if="scope.row.role === 'admin'" size="small" type="danger" effect="plain">管理员</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="92">
        <template #default="scope">
          <span
            class="status-badge"
            :class="scope.row.status || 'approved'"
            :title="'注册时间：' + (scope.row.created_at || '未知')"
          >{{ statusText(scope.row.status) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" width="112" />
      <el-table-column label="部门/岗位" width="98">
        <template #default="scope">
          <div class="cell-main">{{ scope.row.department || '-' }}</div>
          <div v-if="scope.row.position" class="cell-sub">{{ scope.row.position }}</div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="172" fixed="right">
        <template #default="scope">
          <el-button
            v-if="scope.row.status !== 'approved'"
            size="small"
            type="success"
            @click="handleReview(scope.row, 'approved')"
          >通过</el-button>
          <el-button
            v-if="scope.row.status === 'pending'"
            size="small"
            type="danger"
            plain
            @click="handleReview(scope.row, 'rejected')"
          >拒绝</el-button>
          <el-button size="small" v-if="scope.row.status === 'approved'" @click="openEditDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" plain v-if="scope.row.status !== 'pending'" @click="handleDelete(scope.row)">删除</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" maxlength="11" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="岗位">
          <el-input v-model="form.position" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="isEdit ? '留空则不修改，填写则重置该学员密码' : '请设置初始密码（至少 6 位）'"
          />
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
import { userApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const pendingCount = ref(0)
const search = ref('')
const statusFilter = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)

const query = ref({
  page: 1,
  pageSize: 10
})

const statusText = (status) => {
  if (status === 'pending') return '待审核'
  if (status === 'rejected') return '已拒绝'
  return '已通过'
}

const form = ref({
  username: '',
  real_name: '',
  phone: '',
  department: '',
  position: '',
  role: 'user',
  password: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await userApi.getUserList({
      page: query.value.page,
      page_size: query.value.pageSize,
      keyword: search.value,
      status: statusFilter.value || undefined
    })
    tableData.value = res.items
    total.value = res.total
    pendingCount.value = res.pending_count || 0
  } catch (error) {
    console.error('加载用户失败', error)
    ElMessage.error(error.response?.data?.detail || '加载用户失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.value.page = 1
  loadData()
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    username: '',
    real_name: '',
    phone: '',
    department: '',
    position: '',
    role: 'user',
    password: ''
  }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!isEdit.value && !(form.value.password || '').trim()) {
    ElMessage.warning('请给新学员设置初始密码')
    return
  }
  if (form.value.password && form.value.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  try {
    if (isEdit.value) {
      await userApi.updateUser(form.value.id, form.value)
    } else {
      await userApi.createUser(form.value)
    }
    ElMessage.success(isEdit.value ? '修改成功' : '新增成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('提交失败', error)
    ElMessage.error(error.response?.data?.detail || '提交失败')
  }
}

const handleReview = async (row, status) => {
  const actionText = status === 'approved' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(
      `确定要${actionText}「${row.real_name}（${row.username}）」的注册申请吗？`,
      `${actionText}注册申请`,
      { type: status === 'approved' ? 'success' : 'warning' }
    )
    await userApi.reviewUser(row.id, status)
    ElMessage.success(status === 'approved' ? '已审核通过，该学员现在可以登录' : '已拒绝该注册申请')
    loadData()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error.response?.data?.detail || '审核失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户吗？', '确认删除', { type: 'warning' })
    await userApi.deleteUser(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.cell-main {
  line-height: 1.4;
}
.cell-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
  line-height: 1.3;
}
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
}
.status-badge.pending {
  color: #b45309;
  background: #fef3c7;
}
.status-badge.approved {
  color: #15803d;
  background: #dcfce7;
}
.status-badge.rejected {
  color: #b91c1c;
  background: #fee2e2;
}
</style>
