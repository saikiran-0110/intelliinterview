import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { setAuth } from '../../api/client'
import { RecruiterLayout } from './RecruiterLayout'
import { CandidateLayout } from './CandidateLayout'

function jsonOk(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('portal layouts', () => {
  it('redirects candidates without a session to login', async () => {
    render(
      <MemoryRouter initialEntries={['/candidate/applications']}>
        <Routes>
          <Route path="/candidate" element={<CandidateLayout />}>
            <Route path="applications" element={<div>Applications</div>} />
          </Route>
          <Route path="/candidate/login" element={<div>Candidate login</div>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByText('Candidate login')).toBeInTheDocument()
  })

  it('shows recruiter chrome after session validation and logs out', async () => {
    setAuth('token', {
      user_id: '1',
      email: 'recruiter@example.com',
      full_name: 'Recruiter One',
      role: 'RECRUITER',
    })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonOk({
          user_id: '1',
          email: 'recruiter@example.com',
          full_name: 'Recruiter One',
          role: 'RECRUITER',
          token: 'token',
          email_verified: true,
        }),
      ),
    )

    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/recruiter/jobs']}>
        <Routes>
          <Route path="/recruiter" element={<RecruiterLayout />}>
            <Route path="jobs" element={<div>Jobs outlet</div>} />
          </Route>
          <Route path="/recruiter/login" element={<div>Recruiter login</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Jobs outlet')).toBeInTheDocument()
    expect(screen.getByText('recruiter@example.com')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Log out' }))
    await waitFor(() => {
      expect(screen.getByText('Recruiter login')).toBeInTheDocument()
    })
  })
})
