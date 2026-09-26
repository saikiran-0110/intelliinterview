import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApplicationsPage } from './ApplicationsPage'

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual<typeof import('../../api/client')>('../../api/client')
  return {
    ...actual,
    apiRequest: vi.fn().mockResolvedValue({
      user_id: '1',
      email: 'candidate@example.com',
      full_name: 'Candidate One',
      role: 'CANDIDATE',
      token: 'token',
    }),
  }
})

vi.mock('../../api/optional', () => ({
  listOpenJobs: vi.fn(),
  listMyCvs: vi.fn(),
  listMyApplications: vi.fn(),
  uploadMyCv: vi.fn(),
  deleteMyCv: vi.fn(),
  previewJobMatch: vi.fn(),
  applyForJob: vi.fn(),
  formatSalaryGbp: vi.fn(() => 'Salary on request'),
}))

import { listMyApplications, listMyCvs, listOpenJobs } from '../../api/optional'

const mockedListOpenJobs = vi.mocked(listOpenJobs)
const mockedListMyCvs = vi.mocked(listMyCvs)
const mockedListMyApplications = vi.mocked(listMyApplications)

describe('ApplicationsPage open-role search and filter', () => {
  beforeEach(() => {
    mockedListOpenJobs.mockReset()
    mockedListMyCvs.mockReset()
    mockedListMyApplications.mockReset()
    mockedListMyCvs.mockResolvedValue([])
    mockedListMyApplications.mockResolvedValue([])
    mockedListOpenJobs.mockResolvedValue([
      {
        id: 'job-1',
        title: 'Senior Backend Engineer',
        description: 'Python and FastAPI role.',
        location: 'London, UK',
        work_mode: 'HYBRID',
        is_open: true,
        created_at: new Date().toISOString(),
      } as never,
      {
        id: 'job-2',
        title: 'Remote Frontend Developer',
        description: 'React role.',
        location: 'Remote',
        work_mode: 'REMOTE',
        is_open: true,
        created_at: new Date().toISOString(),
      } as never,
    ])
  })

  it('filters open roles by search text', async () => {
    const user = userEvent.setup()
    render(<ApplicationsPage />)

    // Job titles also appear as <option> text in the "Check role match" select, so
    // scope these queries to the job card heading specifically.
    expect(await screen.findByRole('heading', { name: 'Senior Backend Engineer' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Remote Frontend Developer' })).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText(/Search open roles/i), 'React')

    expect(screen.queryByRole('heading', { name: 'Senior Backend Engineer' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Remote Frontend Developer' })).toBeInTheDocument()
  })

  it('filters open roles by work mode', async () => {
    const user = userEvent.setup()
    render(<ApplicationsPage />)

    expect(await screen.findByRole('heading', { name: 'Senior Backend Engineer' })).toBeInTheDocument()

    await user.selectOptions(screen.getByDisplayValue('Any work mode'), 'REMOTE')

    expect(screen.queryByRole('heading', { name: 'Senior Backend Engineer' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Remote Frontend Developer' })).toBeInTheDocument()
  })
})
