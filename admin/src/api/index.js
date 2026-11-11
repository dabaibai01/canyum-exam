import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('adminToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminInfo')
      if (window.location.pathname !== '/login') {
        window.location.replace('/login')
      }
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ========== 认证接口 ==========
export const authApi = {
  login: (data) => api.post('/auth/login', data)
}

// ========== 题库接口 ==========
export const questionApi = {
  getCategories: (type = 'question', showAll = false) => api.get('/questions/categories', { params: { type, show_all: showAll } }),
  getQuestionList: (params) => api.get('/questions/list', { params }),
  getQuestionPage: (params) => api.get('/questions/page', { params }),
  getQuestion: (id) => api.get(`/questions/${id}`),
  createQuestion: (data) => api.post('/questions/', data),
  updateQuestion: (id, data) => api.put(`/questions/${id}`, data),
  deleteQuestion: (id) => api.delete(`/questions/${id}`),
  createCategory: (data) => api.post('/questions/categories', data),
  updateCategory: (id, data) => api.put(`/questions/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/questions/categories/${id}`),
  importQuestions: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/questions/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  }
}

// ========== 上传接口 ==========
export const uploadApi = {
  image: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    })
  }
}

// ========== 统计接口 ==========
export const statsApi = {
  getDashboard: () => api.get('/stats/dashboard'),
  getPracticeUsers: (params) => api.get('/stats/practice-users', { params }),
  getExamUsers: (params) => api.get('/stats/exam-users', { params })
}

// ========== 用户接口 ==========
export const userApi = {
  getUserList: (params) => api.get('/users/list', { params }),
  getUser: (id) => api.get(`/users/${id}`),
  createUser: (data) => api.post('/users/', data),
  updateUser: (id, data) => api.put(`/users/${id}`, data),
  deleteUser: (id) => api.delete(`/users/${id}`),
  changePassword: (data) => api.post('/users/change-password', data)
}

// ========== 考试接口 ==========
export const examApi = {
  getExamList: (params) => api.get('/exams/list', { params }),
  getAvailableQuestions: (categoryId) => api.get('/exams/available', { params: { category_id: categoryId } }),
  getExamQuestions: (id) => api.get(`/exams/${id}/questions`),
  getExam: (id) => api.get(`/exams/${id}`),
  createExam: (data) => api.post('/exams/', data),
  updateExam: (id, data) => api.put(`/exams/${id}`, data),
  deleteExam: (id) => api.delete(`/exams/${id}`),
  getExamResults: (id) => api.get(`/exams/${id}/results`)
}

// ========== 媒体接口 ==========
export const mediaApi = {
  getVideos: (params) => api.get('/media/videos', { params }),
  createVideo: (data) => api.post('/media/videos', data),
  updateVideo: (id, data) => api.put(`/media/videos/${id}`, data),
  deleteVideo: (id) => api.delete(`/media/videos/${id}`),
  getBooks: (params) => api.get('/media/books', { params }),
  createBook: (data) => api.post('/media/books', data),
  updateBook: (id, data) => api.put(`/media/books/${id}`, data),
  deleteBook: (id) => api.delete(`/media/books/${id}`)
}

// ========== 公告接口 ==========
export const noticeApi = {
  getList: (params) => api.get('/notices/list', { params }),
  getNotice: (id) => api.get(`/notices/${id}`),
  createNotice: (data) => api.post('/notices/', data),
  updateNotice: (id, data) => api.put(`/notices/${id}`, data),
  deleteNotice: (id) => api.delete(`/notices/${id}`)
}

// ========== 站点设置 ==========
export const siteApi = {
  get: () => api.get('/site'),
  update: (data) => api.put('/site', data),
  uploadLogo: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/site/logo', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    })
  }
}

export default api
