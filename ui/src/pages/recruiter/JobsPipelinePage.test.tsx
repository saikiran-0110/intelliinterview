import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { JobsPipelinePage } from './JobsPipelinePage'

vi.mock('../../api/analysis', () => ({
  listJobSpecs: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  aiDraftJobSpec: vi.fn(),
  createJobSpec: vi.fn(),
  downloadCv: vi.fn(),
  formatSalaryGbp: vi.fn(() => 'Salary on request'),
  listRecruiterApplications: vi.fn(),
  setJobVisibility: vi.fn(),
  updateApplicationStage: vi.fn(),
}))

import { listJobSpecs } from '../../api/analysis'
import { aiDraftJobSpec, listRecruiterApplications } from '../../api/optional'

const mockedListJobs = vi.mocked(listJobSpecs)
const mockedListApps = vi.mocked(listRecruiterApplications)
const mockedAiDraft = vi.mocked(aiDraftJobSpec)

describe('JobsPipelinePage form labels', () => {
  beforeEach(() => {
    mockedListJobs.mockReset()
    mockedListApps.mockReset()
    mockedAiDraft.mockReset()
    mockedListJobs.mockResolvedValue([])
    mockedListApps.mockResolvedValue([])
  })

  it('keeps field labels and help text after AI fills the form', async () => {
    mockedAiDraft.mockResolvedValue({
      title: 'Senior Platform Engineer',
      description: 'Own cloud infrastructure and platform APIs.',
      department: 'Engineering',
      location: 'London, UK',
      employment_type: 'FULL_TIME',
      work_mode: 'HYBRID',
      salary_min_gbp: 75000,
      salary_max_gbp: 95000,
      years_experience_min: 5,
      benefits: 'Pension and private healthcare',
      model_version: 'baseline',
    })

    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <JobsPipelinePage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Role title')).toBeInTheDocument()
    expect(screen.getByText('Job title candidates will see on the hiring board')).toBeInTheDocument()

    await user.type(
      screen.getByPlaceholderText(/Senior backend engineer in London/i),
      'Senior platform engineer in London, hybrid, 5+ years Python',
    )
    await user.click(screen.getByRole('button', { name: 'Enhance & fill form with AI' }))

    expect(await screen.findByDisplayValue('Senior Platform Engineer')).toBeInTheDocument()
    expect(screen.getByDisplayValue('75000')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Pension and private healthcare')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Role title')).toBeInTheDocument()
      expect(screen.getByText('Department')).toBeInTheDocument()
      expect(screen.getByText('Location')).toBeInTheDocument()
      expect(screen.getByText('Employment type')).toBeInTheDocument()
      expect(screen.getByText('Work mode')).toBeInTheDocument()
      expect(screen.getByText('Min salary (£)')).toBeInTheDocument()
      expect(screen.getByText('Max salary (£)')).toBeInTheDocument()
      expect(screen.getByText('Min years experience')).toBeInTheDocument()
      expect(screen.getByText('Application closing date')).toBeInTheDocument()
      expect(screen.getByText('Job description')).toBeInTheDocument()
      expect(screen.getByText('Benefits')).toBeInTheDocument()
      expect(screen.getByText('Lower end of the advertised band')).toBeInTheDocument()
      expect(screen.getByText('Role summary, responsibilities, and requirements')).toBeInTheDocument()
    })
  })
})

describe('JobsPipelinePage search and filter', () => {
  beforeEach(() => {
    mockedListJobs.mockReset()
    mockedListApps.mockReset()
    mockedAiDraft.mockReset()
    mockedListJobs.mockResolvedValue([
      { id: 'job-1', title: 'Senior Backend Engineer', location: 'London, UK' } as never,
      { id: 'job-2', title: 'Frontend Developer', location: 'Bristol, UK' } as never,
    ])
    mockedListApps.mockResolvedValue([
      // Both scoped to job-1: the page auto-selects the first loaded job and scopes the
      // applications list to it, so both need to share a job_spec_id to appear together.
      {
        id: 'app-1',
        job_spec_id: 'job-1',
        job_title: 'Senior Backend Engineer',
        candidate_name: 'Alex Morgan',
        candidate_email: 'alex@example.com',
        stage: 'APPLIED',
      } as never,
      {
        id: 'app-2',
        job_spec_id: 'job-1',
        job_title: 'Senior Backend Engineer',
        candidate_name: 'Jamie Lee',
        candidate_email: 'jamie@example.com',
        stage: 'SHORTLISTED',
      } as never,
    ])
  })

  it('filters open roles by search text', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <JobsPipelinePage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Senior Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('Frontend Developer')).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText(/Search by title, location, or department/i), 'Bristol')

    expect(screen.queryByText('Senior Backend Engineer')).not.toBeInTheDocument()
    expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
  })

  it('filters applications by candidate search and by stage', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <JobsPipelinePage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Alex Morgan/)).toBeInTheDocument()
    expect(screen.getByText(/Jamie Lee/)).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText(/Search by candidate name or email/i), 'jamie')
    expect(screen.queryByText(/Alex Morgan/)).not.toBeInTheDocument()
    expect(screen.getByText(/Jamie Lee/)).toBeInTheDocument()

    await user.clear(screen.getByPlaceholderText(/Search by candidate name or email/i))
    await user.selectOptions(screen.getByDisplayValue('All stages'), 'APPLIED')
    expect(screen.getByText(/Alex Morgan/)).toBeInTheDocument()
    expect(screen.queryByText(/Jamie Lee/)).not.toBeInTheDocument()
  })
})
