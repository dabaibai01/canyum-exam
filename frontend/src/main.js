import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Vant from 'vant'
import 'vant/lib/index.css'
import App from './App.vue'
import { loadSiteSettings } from './utils/site'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: () => import('./views/Home.vue') },
  { path: '/login', component: () => import('./views/Login.vue') },
  { path: '/register', component: () => import('./views/Register.vue') },
  { path: '/change-password', component: () => import('./views/ChangePassword.vue') },
  { path: '/practice', component: () => import('./views/Practice.vue') },
  { path: '/practice/search', component: () => import('./views/PracticeSearch.vue') },
  { path: '/practice/start', component: () => import('./views/PracticeStart.vue') },
  { path: '/wrong', component: () => import('./views/WrongBook.vue') },
  { path: '/exam', component: () => import('./views/Exam.vue') },
  { path: '/exam/start', component: () => import('./views/ExamStart.vue') },
  { path: '/exam/records', component: () => import('./views/ExamRecords.vue') },
  { path: '/video', component: () => import('./views/Video.vue') },
  { path: '/book', component: () => import('./views/Book.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (to.path === '/login' || to.path === '/register') return true
  if (!localStorage.getItem('token')) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

const app = createApp(App)
app.use(router)
app.use(Vant)
loadSiteSettings()
app.mount('#app')
