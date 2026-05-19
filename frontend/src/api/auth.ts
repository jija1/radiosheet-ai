import client from './client'

interface TokenResponse {
  access_token: string
  token_type: string
}

export async function apiRegister(email: string, password: string): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/api/v1/auth/register', {
    email,
    password,
  })
  return data
}

export async function apiLogin(email: string, password: string): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/api/v1/auth/login', {
    email,
    password,
  })
  return data
}
