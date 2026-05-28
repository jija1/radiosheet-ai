import axios, { AxiosError } from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const STATUS_FALLBACKS: Record<number, string> = {
  400: 'Invalid request',
  401: 'Incorrect email or password',
  403: "You don't have permission to do that",
  404: 'Not found',
  409: 'That already exists',
  429: 'Too many attempts — please wait a moment and try again',
  500: 'Something went wrong on the server',
}

interface FastapiValidationItem {
  msg?: string
}

function extractMessage(error: AxiosError): string {
  if (!error.response) {
    return 'Cannot reach the server. Check your connection and that the backend is running.'
  }

  const data = error.response.data as { detail?: unknown } | undefined
  const detail = data?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (Array.isArray(detail)) {
    const messages = (detail as FastapiValidationItem[])
      .map((item) => (typeof item?.msg === 'string' ? item.msg : ''))
      .filter(Boolean)
    if (messages.length > 0) return messages.join('; ')
  }

  return STATUS_FALLBACKS[error.response.status] ?? 'Something went wrong'
}

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const wrapped = new Error(extractMessage(error)) as Error & {
      status?: number
      original?: AxiosError
    }
    if (error.response) wrapped.status = error.response.status
    wrapped.original = error
    return Promise.reject(wrapped)
  },
)

export default client
