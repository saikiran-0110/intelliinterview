import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { setAuth } from '../api/client'
import { AppRoutes } from './AppRoutes'

describe('AppRoutes', () => {
  it('renders the public landing page', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'IntelliInterview' })).toBeInTheDocument()
  })

  it('renders recruiter and candidate login pages', () => {
    const { unmount } = render(
      <MemoryRouter initialEntries={['/recruiter/login']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(screen.getByText('Recruiter access')).toBeInTheDocument()
    unmount()

    render(
      <MemoryRouter initialEntries={['/candidate/login']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(screen.getByText('Candidate access')).toBeInTheDocument()
  })

  it('redirects unknown paths to landing', () => {
    render(
      <MemoryRouter initialEntries={['/does-not-exist']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'IntelliInterview' })).toBeInTheDocument()
  })

  it('sends unauthenticated recruiters to login', async () => {
    render(
      <MemoryRouter initialEntries={['/recruiter/jobs']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    await waitFor(() => {
      expect(screen.getByText('Recruiter access')).toBeInTheDocument()
    })
  })

  it('keeps an authenticated recruiter in the portal', async () => {
    setAuth('token', {
      user_id: '1',
      email: 'recruiter@example.com',
      full_name: 'Recruiter One',
      role: 'RECRUITER',
    })
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input)
        const body =
          path === '/api/auth/me'
            ? {
                user_id: '1',
                email: 'recruiter@example.com',
                full_name: 'Recruiter One',
                role: 'RECRUITER',
                token: 'token',
                email_verified: true,
              }
            : []
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    render(
      <MemoryRouter initialEntries={['/recruiter/jobs']}>
        <AppRoutes />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Recruiter Portal')).toBeInTheDocument()
    expect(screen.getByText('Recruiter One')).toBeInTheDocument()
  })
})
