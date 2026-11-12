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
          @click="openVideo(video)"
        >
          <div class="row-icon">
            <van-icon name="video-o" size="18" />
          </div>
          <div class="row-main">
            <div class="row-title">{{ video.title }}</div>
            <div v-if="video.description || video.duration" class="row-sub">
              <span v-if="video.duration">{{ formatDuration(video.duration) }}</span>
              <span v-if="video.duration && video.description"> · </span>
              <span v-if="video.description">{{ video.description }}</span>
            </div>
          </div>
          <van-icon name="arrow" class="row-arrow" />
        </div>
      </div>
    </div>

    <van-empty v-else description="暂无视频资源" />

    <van-popup
      v-model:show="showPlayer"
      position="bottom"
      round
      closeable
      class="video-popup"
      @closed="closePlayer"
    >
      <div v-if="currentVideo" class="video-wrap">
        <div class="video-head">{{ currentVideo.title }}</div>
        <video
          :src="currentVideo.video_url"
          class="video-player"
          controls
          autoplay
          playsinline
          preload="metadata"
        ></video>
        <div v-if="currentVideo.description" class="video-desc">{{ currentVideo.description }}</div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { mediaApi } from '../api'

const videos = ref([])
const showPlayer = ref(false)
const currentVideo = ref(null)

const formatDuration = (seconds) => {
  const total = Number(seconds) || 0
  if (!total) return ''
  const min = Math.floor(total / 60)
  const sec = total % 60
  return `${min}:${String(sec).padStart(2, '0')}`
}

const isDirectVideo = (url) => {
  if (String(url).startsWith('/api/uploads/')) return true
  return /\.(mp4|m4v|webm|ogg|ogv)(\?|#|$)/i.test(String(url))
}

const openVideo = (video) => {
  const url = String(video.video_url || '').trim()
  if (!url) {
    showToast('该视频暂未上传文件')
    return
  }
  if (!isDirectVideo(url)) {
    window.open(url, '_blank', 'noopener')
    return
  }
  currentVideo.value = video
  showPlayer.value = true
}

const closePlayer = () => {
  currentVideo.value = null
}

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
  cursor: pointer;
}
.row:active {
  background: var(--card-bg-sub);
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
.video-popup {
  background: var(--card-bg);
  padding-bottom: env(safe-area-inset-bottom);
}
.video-wrap {
  padding: 16px 16px 20px;
}
.video-head {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  padding-right: 32px;
  margin-bottom: 12px;
}
.video-player {
  display: block;
  width: 100%;
  max-height: 60vh;
  background: #000;
  border-radius: 10px;
}
.video-desc {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
