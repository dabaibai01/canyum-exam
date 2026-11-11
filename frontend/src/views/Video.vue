<template>
  <div class="page media-page">
    <van-nav-bar title="视频教学" />

    <div v-if="videos.length" class="section first">
      <div class="section-head">
        <span class="section-title">全部视频</span>
        <span class="section-more">{{ videos.length }} 个</span>
      </div>
      <div class="card list">
        <div
          v-for="(video, index) in videos"
          :key="video.id"
          class="row"
          :class="{ 'no-line': index === videos.length - 1 }"
        >
          <div class="row-icon">
            <van-icon name="video-o" size="18" />
          </div>
          <div class="row-main">
            <div class="row-title">{{ video.title }}</div>
            <div v-if="video.description" class="row-sub">{{ video.description }}</div>
          </div>
          <van-icon name="arrow" class="row-arrow" />
        </div>
      </div>
    </div>

    <van-empty v-else description="暂无视频资源" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { mediaApi } from '../api'

const videos = ref([])

const loadVideos = async () => {
  try {
    const res = await mediaApi.getVideos()
    videos.value = res
  } catch (error) {
    console.error('加载视频失败', error)
  }
}

onMounted(() => {
  loadVideos()
})
</script>

<style scoped>
.media-page {
  padding-bottom: 90px;
}
.section.first {
  margin-top: 12px;
}
.list {
  padding: 2px 0;
}
.row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  position: relative;
}
.row::after {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 0;
  height: 1px;
  background: var(--border-color);
}
.row.no-line::after {
  display: none;
}
.row-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--brand-light);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex: 0 0 38px;
}
.row-main {
  flex: 1;
  min-width: 0;
}
.row-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.row-sub {
  margin-top: 3px;
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.row-arrow {
  color: var(--text-tertiary);
  font-size: 12px;
  margin-left: 8px;
}
</style>
