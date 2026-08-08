const TOKEN_KEY = 'intelliinterview_token'
const USER_KEY = 'intelliinterview_user'

export type StoredUser = {
  user_id: string
  email: string
  full_name: string
  role: 'RECRUITER' | 'CANDIDATE'
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAuth(token: string, user: StoredUser) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): StoredUser | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as StoredUser
  } catch {
    return null
  }
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function redirectToLogin() {
  const path = window.location.pathname
  if (path.startsWith('/recruiter') && !path.includes('/login')) {
    window.location.assign('/recruiter/login')
  } else if (path.startsWith('/candidate') && !path.includes('/login')) {
    window.location.assign('/candidate/login')
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit & { raw?: boolean } = {},
): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  const { raw, ...fetchOptions } = options

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (!(fetchOptions.body instanceof FormData) && !headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, { ...fetchOptions, headers })
  if (!response.ok) {
    let message = 'Request failed'
    try {
      const payload = await response.json()
      message = payload.detail ?? payload.message ?? message
      if (Array.isArray(message)) {
        message = message.map((item) => item.msg ?? String(item)).join(', ')
      }
    } catch {
      message = response.statusText || message
    }

    if (response.status === 401 && !path.startsWith('/api/auth/login') && !path.startsWith('/api/auth/register')) {
      clearAuth()
      redirectToLogin()
    }

    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  if (raw) {
    return (await response.blob()) as T
  }

  return response.json() as Promise<T>
}
