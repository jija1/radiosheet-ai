import { create } from 'zustand'

import type { AuthState, User } from '../types/auth'

function parseJwt(token: string): { sub: string; email: string } | null {
  try {
    const base64 = token.split('.')[1]
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json) as { sub: string; email: string }
  } catch {
    return null
  }
}

function hydrateUser(): User | null {
  try {
    const raw = localStorage.getItem('auth_user')
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthState>()((set) => ({
  token: localStorage.getItem('auth_token'),
  user: hydrateUser(),
  isAuthenticated: !!localStorage.getItem('auth_token'),

  login: (token: string) => {
    const payload = parseJwt(token)
    const user: User | null = payload ? { id: payload.sub, email: payload.email } : null
    localStorage.setItem('auth_token', token)
    if (user) localStorage.setItem('auth_user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))
