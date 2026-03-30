import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor: attach token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: handle 401
api.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
    return Promise.reject(err.response?.data || err)
  }
)

// Auth
export const authApi = {
  login: (data) => api.post('/auth/login', data),
  refresh: (data) => api.post('/auth/refresh', data),
}

// Dashboard
export const dashboardApi = {
  overview: () => api.get('/dashboard/overview'),
  scoreDistribution: () => api.get('/dashboard/score-distribution'),
  trends: () => api.get('/dashboard/docking-trends'),
  topEnterprises: () => api.get('/dashboard/top-enterprises'),
}

// Enterprises
export const enterpriseApi = {
  list: (params) => api.get('/enterprises', { params }),
  get: (id) => api.get(`/enterprises/${id}`),
  create: (data) => api.post('/enterprises', data),
  getScore: (id) => api.get(`/enterprises/${id}/score`),
  updateScore: (id, data) => api.post(`/enterprises/${id}/score`, data),
  delete: (id) => api.delete(`/enterprises/${id}`),
}

// Experts
export const expertApi = {
  list: (params) => api.get('/experts', { params }),
  get: (id) => api.get(`/experts/${id}`),
  create: (data) => api.post('/experts', data),
  updateScore: (id, data) => api.post(`/experts/${id}/score`, data),
}

// Regions
export const regionApi = {
  list: (params) => api.get('/regions', { params }),
  create: (data) => api.post('/regions', data),
  match: (regionId, enterpriseId) => api.get(`/regions/${regionId}/match`, { params: { enterprise_id: enterpriseId } }),
  topEnterprises: (regionId, params) => api.get(`/regions/${regionId}/top-enterprises`, { params }),
}

// Members
export const memberApi = {
  getContribution: (enterpriseId) => api.get(`/members/${enterpriseId}/contribution`),
  recordContribution: (data) => api.post('/members/contribution/record', data),
  leaderboard: (params) => api.get('/members/contribution/leaderboard', { params }),
}

// Dockings
export const dockingApi = {
  list: (params) => api.get('/dockings', { params }),
  create: (data) => api.post('/dockings', data),
  get: (id) => api.get(`/dockings/${id}`),
  updateStatus: (id, data) => api.patch(`/dockings/${id}/status`, data),
}

// Users
export const userApi = {
  list: (params) => api.get('/users', { params }),
  create: (data) => api.post('/users', data),
  getMe: () => api.get('/users/me'),
  update: (id, data) => api.put(`/users/${id}`, data),
}

export default api
