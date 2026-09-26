import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NotificationBell } from './NotificationBell'

vi.mock('../../api/desirable', () => ({
  listNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
}))

import { listNotifications, markNotificationRead } from '../../api/desirable'

const mockedList = vi.mocked(listNotifications)
const mockedMarkRead = vi.mocked(markNotificationRead)

describe('NotificationBell', () => {
  beforeEach(() => {
    mockedList.mockReset()
    mockedMarkRead.mockReset()
  })

  it('shows an unread count badge and no crash when the response is not an array', async () => {
    // Defends against a layout-level fetch mock (elsewhere in the app) returning an
    // unrelated JSON shape - the bell must degrade to an empty list, not throw.
    mockedList.mockResolvedValue({ not: 'an array' } as never)
    render(
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>,
    )
    await waitFor(() => expect(mockedList).toHaveBeenCalled())
    expect(screen.queryByText(/unread/i)).not.toBeInTheDocument()
  })

  it('renders unread notifications with a badge and marks one read on click', async () => {
    mockedList.mockResolvedValue([
      {
        id: 'n1',
        title: 'Candidate confirmed interview',
        body: 'The candidate confirmed a slot.',
        link: '/recruiter/scheduling',
        channel: 'IN_APP',
        is_read: false,
        email_sent: false,
        related_session_id: null,
        created_at: new Date().toISOString(),
      },
    ])
    mockedMarkRead.mockResolvedValue({} as never)

    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/recruiter/jobs']}>
        <Routes>
          <Route path="/recruiter/jobs" element={<NotificationBell />} />
          <Route path="/recruiter/scheduling" element={<div>Scheduling page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    const bellButton = await screen.findByRole('button', { name: /1 unread notification/i })
    await user.click(bellButton)

    expect(await screen.findByText('Candidate confirmed interview')).toBeInTheDocument()
    await user.click(screen.getByText('Candidate confirmed interview'))

    expect(mockedMarkRead).toHaveBeenCalledWith('n1')
    expect(await screen.findByText('Scheduling page')).toBeInTheDocument()
  })

  it('handles a relative or absolute link the same way when navigating', async () => {
    mockedList.mockResolvedValue([
      {
        id: 'n2',
        title: 'Interview slots available',
        body: 'Please confirm a slot.',
        link: 'http://localhost:5173/candidate/sessions',
        channel: 'IN_APP',
        is_read: true,
        email_sent: true,
        related_session_id: null,
        created_at: new Date().toISOString(),
      },
    ])

    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/candidate/applications']}>
        <Routes>
          <Route path="/candidate/applications" element={<NotificationBell />} />
          <Route path="/candidate/sessions" element={<div>Sessions page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    const bellButton = await screen.findByRole('button', { name: 'Notifications' })
    await user.click(bellButton)
    await user.click(await screen.findByText('Interview slots available'))

    expect(await screen.findByText('Sessions page')).toBeInTheDocument()
  })
})
