import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import { loadSiteSettings } from './utils/site'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: () => import('./views/Login.vue') },
  {
    path: '/',
    component: () => import('./layouts/Layout.vue'),
    children: [
      { path: 'dashboard', component: () => import('./views/Dashboard.vue') },
      { path: 'questions', component: () => import('./views/QuestionList.vue') },
      { path: 'questions/import', component: () => import('./views/QuestionImport.vue') },
      { path: 'practice-stats', redirect: '/practice-stats/practice' },
      { path: 'practice-stats/practice', component: () => import('./views/PracticeStats.vue'), props: { mode: 'practice' } },
      { path: 'practice-stats/exam', component: () => import('./views/PracticeStats.vue'), props: { mode: 'exam' } },
      { path: 'categories', component: () => import('./views/CategoryList.vue') },
      { path: 'exams', component: () => import('./views/ExamList.vue') },
      { path: 'users', component: () => import('./views/UserList.vue') },
      { path: 'videos', component: () => import('./views/VideoList.vue') },
      { path: 'books', component: () => import('./views/BookList.vue') },
      { path: 'notices', component: () => import('./views/NoticeList.vue') },
      { path: 'settings', component: () => import('./views/SiteSettings.vue') },
      { path: 'about', component: () => import('./views/About.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (to.path === '/login') return true
  if (!localStorage.getItem('adminToken')) {
    return { path: '/login' }
  }
  return true
})

const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.use(router)
app.use(ElementPlus)
loadSiteSettings()
app.mount('#app')
