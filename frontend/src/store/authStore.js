import { create } from 'zustand'
import { authApi } from '../services/api'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user_info') || 'null'),
  token: localStorage.getItem('access_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (username, password) => {
    const data = await authApi.login({ username, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_info', JSON.stringify({
      id: data.user_id, username: data.username, role: data.role
    }))
    set({
      token: data.access_token,
      user: { id: data.user_id, username: data.username, role: data.role },
      isAuthenticated: true
    })
    return data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    set({ token: null, user: null, isAuthenticated: false })
  }
}))

export default useAuthStore
