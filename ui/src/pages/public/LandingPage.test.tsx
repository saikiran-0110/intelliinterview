import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { setAuth } from '../../api/client'
import { LandingPage } from './LandingPage'

describe('LandingPage', () => {
  it('shows login links when logged out', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'IntelliInterview' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Recruiter login' })).toHaveAttribute('href', '/recruiter/login')
    expect(screen.getByRole('link', { name: 'Candidate login' })).toHaveAttribute('href', '/candidate/login')
    expect(screen.getByText('Open a role')).toBeInTheDocument()
    expect(screen.getByText('University of Leicester', { exact: false })).toBeInTheDocument()
  })

  it('shows portal shortcut when a recruiter is signed in', () => {
    setAuth('token', {
      user_id: '1',
      email: 'recruiter@example.com',
      full_name: 'Recruiter One',
      role: 'RECRUITER',
    })
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Signed in as Recruiter One')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Go to Hiring Board' })[0]).toHaveAttribute('href', '/recruiter/jobs')
    expect(screen.getByRole('link', { name: 'Continue to your portal' })).toBeInTheDocument()
  })
})
