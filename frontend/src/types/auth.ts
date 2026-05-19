export interface User {
  id: string
  email: string
  display_name?: string | null
}

export interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
  setDisplayName: (display_name: string | null) => void
}
