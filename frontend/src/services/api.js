/**
 * API Service
 * Handles all HTTP requests to the backend.
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token, refresh_token: newRefreshToken } = response.data
          
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', newRefreshToken)

          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login/user'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// ==================== Auth API ====================

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  verifyAdmin: async () => {
    const response = await api.get('/auth/verify-admin')
    return response.data
  },
}

// ==================== Chat API ====================

export const chatAPI = {
  sendMessage: async (message, sessionId = null) => {
    const response = await api.post('/chat/query', {
      message,
      session_id: sessionId,
    })
    return response.data
  },

  getSessions: async (page = 1, pageSize = 50, includeArchived = false) => {
    const response = await api.get('/chat/sessions', {
      params: { page, page_size: pageSize, include_archived: includeArchived },
    })
    return response.data
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/chat/sessions/${sessionId}`)
    return response.data
  },

  updateSessionTitle: async (sessionId, title) => {
    const response = await api.put(`/chat/sessions/${sessionId}/title`, null, {
      params: { title },
    })
    return response.data
  },

  archiveSession: async (sessionId) => {
    const response = await api.delete(`/chat/sessions/${sessionId}`)
    return response.data
  },

  getAgentInfo: async () => {
    const response = await api.get('/chat/agents/info')
    return response.data
  },
}

// ==================== Document API ====================

export const documentAPI = {
  upload: async (file, documentType, title, description, tags) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    if (title) formData.append('title', title)
    if (description) formData.append('description', description)
    if (tags && tags.length > 0) formData.append('tags', tags.join(','))

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  list: async (page = 1, pageSize = 50) => {
    const response = await api.get('/documents/', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  get: async (documentId) => {
    const response = await api.get(`/documents/${documentId}`)
    return response.data
  },

  delete: async (documentId) => {
    const response = await api.delete(`/documents/${documentId}`)
    return response.data
  },
}

// ==================== Health API ====================

export const healthAPI = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },

  detailed: async () => {
    const response = await api.get('/health/detailed')
    return response.data
  },
}

export default api

