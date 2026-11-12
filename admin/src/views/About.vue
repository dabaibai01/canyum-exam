<template>
  <div class="about-page">
    <el-card shadow="never" class="about-card">
      <div class="about-head">
        <img :src="siteLogo()" alt="铁刷客" class="about-logo" />
        <div>
          <div class="about-title">{{ site.site_name }}</div>
          <div class="about-sub">{{ site.site_subtitle }}</div>
        </div>
        <el-tag type="success" effect="plain" class="version-tag">V2.0</el-tag>
      </div>

      <el-descriptions :column="2" border class="about-desc">
        <el-descriptions-item label="系统版本">V2.0（2026-11-12）</el-descriptions-item>
        <el-descriptions-item label="开发者">{{ site.developer_name }}</el-descriptions-item>
        <el-descriptions-item label="技术架构">FastAPI + Vue 3 + SQLite</el-descriptions-item>
        <el-descriptions-item label="部署环境">Nginx + Supervisor，支持私有化部署</el-descriptions-item>
        <el-descriptions-item label="管理端">当前访问地址</el-descriptions-item>
        <el-descriptions-item label="备案号">{{ site.icp_no || '未配置' }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title">本版本主要功能</div>
      <div class="feature-grid">
        <div v-for="item in features" :key="item.title" class="feature-item">
          <div class="feature-dot"></div>
          <div>
            <div class="feature-title">{{ item.title }}</div>
            <div class="feature-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>

      <div class="section-title">版本记录</div>
      <el-table :data="history" size="small" border>
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="content" label="更新内容" />
      </el-table>

      <div class="about-foot">
        <span>{{ site.site_name }}</span>
        <span>技术支持：{{ site.developer_name }}</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { site, siteLogo } from '../utils/site'

const features = [
  { title: '学员注册审核', desc: '学员可自助注册，管理员审核通过后才能登录使用。' },
  { title: '智能答题切题', desc: '单选、判断答对自动下一题，答错停留；上一题 / 下一题按钮可在整套题中连续切换。' },
  { title: '练习 / 考试双统计', desc: '刷题量与考试量分页查看，在线考试、自己组卷和管理员数据全部纳入。' },
  { title: '题目级答题分析', desc: '按题目查看作答人数、正确率和错答分布，便于重点讲解与出题。' },
  { title: '多模式学习', desc: '答题、背题、读题三种模式，支持收藏、笔记、画重点和关键词搜题。' },
  { title: '组卷与题库', desc: '错题、收藏、自选组卷，支持 Excel / CSV 批量导入和 A 到 J 多选项。' }
]

const history = [
  { version: 'V2.0', date: '2026-11-12', content: '全新版本：学员注册审核、答对自动跳题与按钮连续切题、刷题/考试双统计（含考试、自己组卷、管理员）、题目级答题分析、收藏笔记标注、错题组卷、夜间模式与设置页完善。' },
  { version: 'V1.1', date: '2026-11-11', content: '统计拆分、管理员纳入统计、自己组卷、错题组卷、顺序记忆、批量导入、10 选项、品牌升级。' },
  { version: 'V1.0', date: '2026-11-09', content: '题库、刷题、错题本、在线考试、后台管理、学习资源等基础功能上线。' }
]
</script>

<style scoped>
.about-page {
  max-width: 980px;
}
.about-card {
  border-radius: 10px;
}
.about-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 18px;
  border-bottom: 1px solid #ebeef5;
}
.about-logo {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  object-fit: cover;
}
.about-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2d3d;
}
.about-sub {
  margin-top: 5px;
  font-size: 12px;
  color: #8a94a6;
  letter-spacing: 0.5px;
}
.version-tag {
  margin-left: auto;
  font-size: 14px;
  padding: 0 12px;
  height: 30px;
}
.about-desc {
  margin-top: 20px;
}
.section-title {
  margin: 24px 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
  padding-left: 9px;
  border-left: 3px solid #409eff;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
}
.feature-item {
  display: flex;
  gap: 9px;
  padding: 10px 12px;
  background: #f6f8fb;
  border-radius: 8px;
}
.feature-dot {
  width: 7px;
  height: 7px;
  margin-top: 4px;
  border-radius: 50%;
  background: #409eff;
  flex: none;
}
.feature-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.feature-desc {
  margin-top: 3px;
  font-size: 12px;
  color: #7a8798;
  line-height: 1.55;
}
.about-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 22px;
  padding-top: 14px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #a3adbb;
}
</style>
