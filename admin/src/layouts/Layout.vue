<template>
  <el-container style="height: 100vh">
    <el-aside width="200px" class="admin-aside" style="background-color: #304156">
      <div class="side-brand">
        <img :src="siteLogo()" alt="铁刷客" class="side-logo" />
        <div>
          <div class="side-name">{{ shortName }}</div>
          <div class="side-sub">{{ site.site_subtitle }} · 管理后台</div>
        </div>
      </div>
      <el-menu
        class="side-menu"
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-sub-menu index="question">
          <template #title>
            <el-icon><EditPen /></el-icon>
            <span>题库管理</span>
          </template>
          <el-menu-item index="/questions">题目列表</el-menu-item>
          <el-menu-item index="/questions/import">批量导入</el-menu-item>
          <el-menu-item index="/categories">分类管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="practice-stats">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>练习统计</span>
          </template>
          <el-menu-item index="/practice-stats/practice">刷题统计</el-menu-item>
          <el-menu-item index="/practice-stats/exam">考试统计</el-menu-item>
          <el-menu-item index="/practice-stats/question">题目分析</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/exams">
          <el-icon><Document /></el-icon>
          <span>考试管理</span>
        </el-menu-item>
        <el-menu-item index="/notices">
          <el-icon><Bell /></el-icon>
          <span>公告管理</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
        <el-sub-menu index="media">
          <template #title>
            <el-icon><VideoCamera /></el-icon>
            <span>学习资源</span>
          </template>
          <el-menu-item index="/videos">视频管理</el-menu-item>
          <el-menu-item index="/books">书籍管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
      <div class="side-bottom">
        <router-link to="/about" class="about-link">关于系统</router-link>
        <div class="side-version">V2.0 · {{ site.developer_name }}</div>
      </div>
    </el-aside>

    <el-container>
      <el-header style="background: white; display: flex; justify-content: space-between; align-items: center;">
        <div>欢迎使用，{{ site.site_name }}管理后台</div>
        <div style="display: flex; align-items: center; gap: 20px;">
          <el-button
            :icon="isDarkMode ? Sunny : Moon"
            circle
            @click="toggleDarkMode"
          />
          <el-dropdown @command="handleCommand">
            <span class="user-trigger">{{ adminName }}<el-icon class="el-icon--right"><ArrowDown /></el-icon></span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="pwdVisible" title="修改密码" width="420px" destroy-on-close>
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.old" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPassword">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Sunny, Moon, ArrowDown, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { site, siteLogo } from '../utils/site'

const router = useRouter()
const route = useRoute()
const shortName = computed(() => site.site_name.replace(/考试系统$/, '') || '铁刷客')

const isDarkMode = ref(false)
const adminName = ref('管理员')
const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = ref({ old: '', new: '', confirm: '' })

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark', isDarkMode.value)
  localStorage.setItem('adminDarkMode', isDarkMode.value)
}

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminInfo')
    router.replace('/login')
  } else if (command === 'password') {
    pwdForm.value = { old: '', new: '', confirm: '' }
    pwdVisible.value = true
  }
}

const submitPassword = async () => {
  if (!pwdForm.value.old || !pwdForm.value.new) {
    ElMessage.warning('请填写旧密码和新密码')
    return
  }
  if (pwdForm.value.new !== pwdForm.value.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (pwdForm.value.new.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  pwdLoading.value = true
  try {
    const resp = await fetch('/api/users/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
      },
      body: JSON.stringify({ old_password: pwdForm.value.old, new_password: pwdForm.value.new })
    })
    const data = await resp.json()
    if (!resp.ok) throw new Error(data.detail || '修改失败')
    ElMessage.success('密码已修改，请重新登录')
    pwdVisible.value = false
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminInfo')
    router.replace('/login')
  } catch (error) {
    ElMessage.error(error.message || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

onMounted(() => {
  try {
    const info = JSON.parse(localStorage.getItem('adminInfo') || '{}')
    adminName.value = info.real_name || info.username || '管理员'
  } catch (e) {
    adminName.value = '管理员'
  }
  const saved = localStorage.getItem('adminDarkMode')
  if (saved === 'true') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>

<style scoped>
.admin-aside {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.side-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 16px 14px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.side-logo {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  object-fit: cover;
  flex: none;
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.side-name {
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1.2;
}
.side-sub {
  color: #8fa0b5;
  font-size: 10px;
  margin-top: 3px;
  letter-spacing: 0.4px;
  white-space: nowrap;
}
.side-menu {
  flex: 1;
  overflow-y: auto;
  border-right: none;
}
.side-bottom {
  padding: 10px 14px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.about-link {
  display: block;
  color: #bfcbd9;
  font-size: 12px;
  text-decoration: none;
  margin-bottom: 5px;
}
.about-link:hover {
  color: #409eff;
}
.side-version {
  color: #7c8ba1;
  font-size: 10px;
  line-height: 1.4;
  white-space: nowrap;
}
.user-trigger {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  color: #1f2d3d;
  font-size: 13px;
}
</style>
