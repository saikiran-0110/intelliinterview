import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  apiRequest,
  clearAuth,
  getStoredUser,
  getToken,
  setAuth,
  type StoredUser,
} from './client'

const sampleUser: StoredUser = {
  user_id: 'user-1',
  email: 'recruiter@example.com',
  full_name: 'Recruiter One',
  role: 'RECRUITER',
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('auth storage', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it('stores and reads token and user', () => {
    expect(getToken()).toBeNull()
    expect(getStoredUser()).toBeNull()
    setAuth('token-123', sampleUser)
    expect(getToken()).toBe('token-123')
    expect(getStoredUser()).toEqual(sampleUser)
  })

  it('clears stored auth', () => {
    setAuth('token-123', sampleUser)
    clearAuth()
    expect(getToken()).toBeNull()
    expect(getStoredUser()).toBeNull()
  })

  it('returns null when stored user json is invalid', () => {
    localStorage.setItem('intelliinterview_user', '{not-json')
    expect(getStoredUser()).toBeNull()
  })
})

describe('apiRequest', () => {
  afterEach(() => {
    localStorage.clear()
    vi.unstubAllGlobals()
  })

  it('attaches bearer token and parses json', async () => {
    setAuth('abc', sampleUser)
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    const payload = await apiRequest<{ ok: boolean }>('/api/health', { method: 'GET' })
    expect(payload).toEqual({ ok: true })
    const headers = fetchMock.mock.calls[0][1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer abc')
  })

  it('sets json content type for string bodies but not FormData', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({}))
      .mockResolvedValueOnce(jsonResponse({}))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('/api/jobs', { method: 'POST', body: JSON.stringify({ title: 'Role' }) })
    expect((fetchMock.mock.calls[0][1].headers as Headers).get('Content-Type')).toBe('application/json')

    const form = new FormData()
    form.append('file', new Blob(['cv']))
    await apiRequest('/api/cvs/upload', { method: 'POST', body: form })
    expect((fetchMock.mock.calls[1][1].headers as Headers).has('Content-Type')).toBe(false)
  })

  it('returns undefined for 204 responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(apiRequest('/api/cvs/1', { method: 'DELETE' })).resolves.toBeUndefined()
  })

  it('returns a blob when raw is true', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(new Blob(['file']), { status: 200 })),
    )
    const blob = await apiRequest<Blob>('/api/cvs/1/download', { raw: true })
    expect(blob).toBeInstanceOf(Blob)
  })

  it('maps validation array details into an ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: [{ msg: 'email invalid' }, { msg: 'too short' }] }, 422),
      ),
    )
    await expect(apiRequest('/api/auth/login', { method: 'POST', body: '{}' })).rejects.toMatchObject({
      message: 'email invalid, too short',
      status: 422,
    })
  })

  it('clears auth and redirects recruiter 401s to login', async () => {
    setAuth('expired', sampleUser)
    const assign = vi.fn()
    vi.stubGlobal('location', { pathname: '/recruiter/jobs', assign })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'Token expired' }, 401)))

    await expect(apiRequest('/api/sessions')).rejects.toBeInstanceOf(ApiError)
    expect(getToken()).toBeNull()
    expect(assign).toHaveBeenCalledWith('/recruiter/login')
  })

  it('redirects candidate 401s to candidate login', async () => {
    setAuth('expired', { ...sampleUser, role: 'CANDIDATE' })
    const assign = vi.fn()
    vi.stubGlobal('location', { pathname: '/candidate/applications', assign })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ message: 'unauthorized' }, 401)))

    await expect(apiRequest('/api/applications/me')).rejects.toBeInstanceOf(ApiError)
    expect(assign).toHaveBeenCalledWith('/candidate/login')
  })
})
