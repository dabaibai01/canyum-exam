<template>
  <div class="settings-page">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="settings-card">
          <template #header>
            <div class="card-head">
              <span>品牌设置</span>
              <span class="card-tip">修改后立即对学员端和管理端生效</span>
            </div>
          </template>

          <el-form :model="form" label-width="96px" label-position="left">
            <el-form-item label="系统名称">
              <el-input v-model="form.site_name" maxlength="40" show-word-limit placeholder="可以云码考试系统" />
            </el-form-item>
            <el-form-item label="副标题">
              <el-input v-model="form.site_subtitle" maxlength="80" show-word-limit placeholder="考试 · 刷题 · 组卷" />
            </el-form-item>

            <el-form-item label="系统 Logo">
              <div class="logo-row">
                <div class="logo-preview">
                  <img :src="form.logo_url || defaultLogo" alt="系统 Logo" />
                </div>
                <div class="logo-actions">
                  <el-button size="small" @click="pickLogo">上传新 Logo</el-button>
                  <el-button v-if="form.logo_url" size="small" text type="danger" @click="resetLogo">恢复默认</el-button>
                  <div class="logo-hint">建议 512×512 像素，支持 JPG / PNG / WebP，最大 2MB。</div>
                </div>
                <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" class="file-input" @change="onLogoFile" />
              </div>
            </el-form-item>

            <el-form-item label="开发者">
              <el-input v-model="form.developer_name" maxlength="60" placeholder="可以云码软件开发" />
            </el-form-item>
            <el-form-item label="页脚文字">
              <el-input v-model="form.footer_text" maxlength="120" placeholder="可以云码考试系统" />
            </el-form-item>
            <el-form-item label="备案号">
              <el-input v-model="form.icp_no" maxlength="60" placeholder="例如：蒙ICP备XXXXXXXX号" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveBrand">保存品牌设置</el-button>
              <el-button @click="reload">重新读取</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="settings-card">
          <template #header>
            <div class="card-head">
              <span>账号安全</span>
              <span class="card-tip">修改当前管理员密码</span>
            </div>
          </template>
          <el-form :model="pwd" label-width="96px" label-position="left">
            <el-form-item label="当前密码">
              <el-input v-model="pwd.old" type="password" show-password autocomplete="current-password" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="pwd.new" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="pwd.confirm" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pwdLoading" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
          <el-alert type="info" :closable="false" show-icon title="修改密码后需要重新登录。" />
        </el-card>

        <el-card shadow="never" class="settings-card preview-card">
          <template #header>
            <div class="card-head"><span>品牌预览</span></div>
          </template>
          <div class="preview-hero">
            <img :src="form.logo_url || defaultLogo" alt="Logo 预览" class="preview-logo" />
            <div>
              <div class="preview-name">{{ form.site_name || '可以云码考试系统' }}</div>
              <div class="preview-sub">{{ form.site_subtitle || '考试 · 刷题 · 组卷' }}</div>
            </div>
          </div>
          <div class="preview-foot">{{ form.footer_text || form.site_name || '可以云码考试系统' }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { siteApi, userApi } from '../api'
import { site } from '../utils/site'
import defaultLogo from '../assets/logo.png'

const router = useRouter()
const fileInput = ref(null)
const saving = ref(false)
const pwdLoading = ref(false)
const form = reactive({
  site_name: '',
  site_subtitle: '',
  developer_name: '',
  footer_text: '',
  icp_no: '',
  logo_url: ''
})
const pwd = reactive({ old: '', new: '', confirm: '' })

const fillForm = () => {
  form.site_name = site.site_name
  form.site_subtitle = site.site_subtitle
  form.developer_name = site.developer_name
  form.footer_text = site.footer_text
  form.icp_no = site.icp_no
  form.logo_url = site.logo_url
}

const reload = async () => {
  try {
    await siteApi.get().then((res) => {
      Object.assign(site, res)
      fillForm()
    })
    ElMessage.success('已读取最新设置')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '读取失败')
  }
}

const pickLogo = () => fileInput.value?.click()

const onLogoFile = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('Logo 不能超过 2MB')
    return
  }
  try {
    const res = await siteApi.uploadLogo(file)
    form.logo_url = res.logo_url
    ElMessage.success('Logo 已上传，保存后生效')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || 'Logo 上传失败')
  }
}

const resetLogo = () => {
  form.logo_url = ''
  ElMessage.info('已恢复默认 Logo，保存后生效')
}

const saveBrand = async () => {
  if (!form.site_name.trim()) {
    ElMessage.warning('系统名称不能为空')
    return
  }
  saving.value = true
  try {
    const res = await siteApi.update({
      site_name: form.site_name.trim(),
      site_subtitle: form.site_subtitle.trim(),
      developer_name: form.developer_name.trim(),
      footer_text: form.footer_text.trim(),
      icp_no: form.icp_no.trim(),
      logo_url: form.logo_url
    })
    Object.assign(site, res)
    fillForm()
    ElMessage.success('品牌设置已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  if (!pwd.old || !pwd.new) {
    ElMessage.warning('请填写当前密码和新密码')
    return
  }
  if (pwd.new !== pwd.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (pwd.new.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  pwdLoading.value = true
  try {
    await userApi.changePassword({ old_password: pwd.old, new_password: pwd.new })
    ElMessage.success('密码已修改，请重新登录')
    localStorage.removeItem('adminToken')
    localStorage.removeItem('adminInfo')
    router.replace('/login')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

fillForm()
</script>

<style scoped>
.settings-page {
  max-width: 1180px;
}
.settings-card {
  border-radius: 10px;
  margin-bottom: 16px;
}
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
  color: #1f2d3d;
}
.card-tip {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
}
.logo-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.logo-preview {
  width: 84px;
  height: 84px;
  border-radius: 18px;
  overflow: hidden;
  flex: none;
  border: 1px solid #e4e7ed;
  background: #f5f7fa;
}
.logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.logo-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
.logo-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.file-input {
  display: none;
}
.preview-card {
  margin-top: 16px;
}
.preview-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0f3568 0%, #17579c 55%, #2f7ac4 100%);
  color: #fff;
}
.preview-logo {
  width: 62px;
  height: 62px;
  border-radius: 16px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
}
.preview-name {
  font-size: 18px;
  font-weight: 700;
}
.preview-sub {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}
.preview-foot {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}
</style>
