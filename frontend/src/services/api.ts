import axios from 'axios'
import { config } from '../config'
import { useAuthStore } from '../stores/authStore'

// Create axios instance
export const api = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login', { username, password })
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Rooms API
export const roomsAPI = {
  create: async (name: string, scheduled_start?: string) => {
    const response = await api.post('/rooms/create', { name, scheduled_start })
    return response.data
  },
  join: async (room_id: string, display_name?: string) => {
    const response = await api.post('/rooms/join', { room_id, display_name })
    return response.data
  },
  list: async (status?: string) => {
    const response = await api.get('/rooms/', { params: { status } })
    return response.data
  },
  get: async (room_id: string) => {
    const response = await api.get(`/rooms/${room_id}`)
    return response.data
  },
}
