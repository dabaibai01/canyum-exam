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
    const token = localStorage.getItem('token')
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
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      if (window.location.pathname !== '/login') {
        const redirect = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.replace(`/login?redirect=${redirect}`)
      }
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ========== 认证接口 ==========
export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data)
}

// ========== 题库接口 ==========
export const questionApi = {
  getCategories: (type = 'question') => api.get('/questions/categories', { params: { type } }),
  getQuestionList: (params) => api.get('/questions/list', { params }),
  getQuestion: (id) => api.get(`/questions/${id}`),
  getRandomQuestions: (categoryId, count = 10, mode = 'random', offset = 0) =>
    api.get(`/questions/random/${categoryId}`, { params: { count, mode, offset } }),
  createQuestion: (data) => api.post('/questions', data)
}

// ========== 刷题接口 ==========
export const practiceApi = {
  submitAnswer: (data) => api.post('/practice/submit', data),
  getWrongList: (params) => api.get('/practice/wrong/list', { params }),
  getWrongQuestions: (params) => api.get('/practice/wrong/questions', { params }),
  getWrongDetail: (questionId) => api.get(`/practice/wrong/${questionId}/detail`),
  markMastered: (questionId) => api.post(`/practice/wrong/${questionId}/master`),
  deleteWrong: (questionId) => api.delete(`/practice/wrong/${questionId}`),
  getStats: () => api.get('/practice/stats'),
  getMarks: (questionIds) => api.get('/practice/marks', { params: { question_ids: questionIds } }),
  saveMark: (questionId, data) => api.put(`/practice/marks/${questionId}`, data),
  getFavorites: (params) => api.get('/practice/favorites', { params }),
  getFavoriteQuestions: (params) => api.get('/practice/favorites/questions', { params }),
  searchQuestions: (params) => api.get('/practice/search', { params })
}

// ========== 公告接口 ==========
export const noticeApi = {
  getHome: (limit = 5) => api.get('/notices/home', { params: { limit } })
}

// ========== 考试接口 ==========
export const examApi = {
  getExamList: (params) => api.get('/exams/list', { params }),
  getMyExams: (params) => api.get('/exams/my-exams', { params }),
  getMyAttempts: () => api.get('/exams/my-attempts'),
  getExamAttempts: (id) => api.get(`/exams/${id}/attempts`),
  getExam: (id) => api.get(`/exams/${id}`),
  getExamQuestions: (id) => api.get(`/exams/${id}/questions`),
  submitExam: (id, answers) => api.post(`/exams/${id}/submit`, answers),
  createExam: (data) => api.post('/exams', data),
  getAvailableQuestions: (categoryId = 0) => api.get('/exams/available', { params: { category_id: categoryId } }),
  createSelfExam: (data) => api.post('/exams/self-compose', data)
}

// ========== 媒体接口 ==========
export const mediaApi = {
  getVideos: (params) => api.get('/media/videos', { params }),
  getVideo: (id) => api.get(`/media/videos/${id}`),
  getBooks: (params) => api.get('/media/books', { params }),
  getBook: (id) => api.get(`/media/books/${id}`)
}

// ========== 站点设置 ==========
export const siteApi = {
  get: () => api.get('/site')
}

export default api
