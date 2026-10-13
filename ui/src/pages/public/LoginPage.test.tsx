import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'

vi.mock('../../api/analysis', () => ({
  startLogin: vi.fn(),
  startRegister: vi.fn(),
  verifyOtp: vi.fn(),
}))

import { startLogin, startRegister, verifyOtp } from '../../api/analysis'
import { getStoredUser, getToken } from '../../api/client'

const mockedStartLogin = vi.mocked(startLogin)
const mockedStartRegister = vi.mocked(startRegister)
const mockedVerifyOtp = vi.mocked(verifyOtp)

describe('LoginPage', () => {
  beforeEach(() => {
    mockedStartLogin.mockReset()
    mockedStartRegister.mockReset()
    mockedVerifyOtp.mockReset()
    localStorage.clear()
  })

  it('sends a login OTP then verifies a recruiter account', async () => {
    const user = userEvent.setup()
    mockedStartLogin.mockResolvedValue({
      message: 'Login code sent',
      email: 'recruiter@example.com',
      purpose: 'LOGIN',
      expires_in_minutes: 10,
    })
    mockedVerifyOtp.mockResolvedValue({
      user_id: 'u1',
      email: 'recruiter@example.com',
      full_name: 'Recruiter One',
      role: 'RECRUITER',
      token: 'jwt-token',
      email_verified: true,
    })

    render(
      <MemoryRouter>
        <LoginPage role="recruiter" />
      </MemoryRouter>,
    )

    expect(screen.getByText('Recruiter access')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Email address'), 'recruiter@example.com')
    await user.click(screen.getByRole('button', { name: 'Send login OTP' }))

    await screen.findByLabelText('6-digit code')
    expect(mockedStartLogin).toHaveBeenCalledWith('recruiter@example.com')

    await user.type(screen.getByLabelText('6-digit code'), '123456')
    await user.click(screen.getByRole('button', { name: 'Verify & continue' }))

    await waitFor(() => {
      expect(getToken()).toBe('jwt-token')
      expect(getStoredUser()?.role).toBe('RECRUITER')
    })
  })

  it('switches to register and shows recruiter company field', async () => {
    const user = userEvent.setup()
    mockedStartRegister.mockResolvedValue({
      message: 'Verification code sent',
      email: 'new@example.com',
      purpose: 'REGISTER',
      expires_in_minutes: 10,
    })

    render(
      <MemoryRouter>
        <LoginPage role="recruiter" />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: /Need an account/i }))
    expect(screen.getByLabelText('Company')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Full name'), 'New Recruiter')
    await user.type(screen.getByLabelText('Phone number'), '+447700900111')
    await user.type(screen.getByLabelText('Company'), 'Acme')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.type(screen.getByLabelText('Email address'), 'new@example.com')
    await user.click(screen.getByRole('button', { name: 'Send registration OTP' }))

    await screen.findByLabelText('6-digit code')
    expect(mockedStartRegister).toHaveBeenCalled()
  })

  it('shows an error when login OTP cannot be sent', async () => {
    const user = userEvent.setup()
    mockedStartLogin.mockRejectedValue(new Error('No account found for this email'))

    render(
      <MemoryRouter>
        <LoginPage role="candidate" />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Email address'), 'missing@example.com')
    await user.click(screen.getByRole('button', { name: 'Send login OTP' }))
    expect(await screen.findByText('No account found for this email')).toBeInTheDocument()
  })
})
