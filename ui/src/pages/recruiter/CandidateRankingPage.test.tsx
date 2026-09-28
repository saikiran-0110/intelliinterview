import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { CandidateRankingPage } from './CandidateRankingPage'

vi.mock('../../api/analysis', () => ({
  listJobSpecs: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  listRecruiterApplications: vi.fn(),
  rankCandidates: vi.fn(),
  updateApplicationStage: vi.fn(),
}))

import { listJobSpecs } from '../../api/analysis'
import { listRecruiterApplications, rankCandidates } from '../../api/optional'

const mockedListJobs = vi.mocked(listJobSpecs)
const mockedListApps = vi.mocked(listRecruiterApplications)
const mockedRank = vi.mocked(rankCandidates)

describe('CandidateRankingPage already-shortlisted section', () => {
  beforeEach(() => {
    mockedListJobs.mockReset()
    mockedListApps.mockReset()
    mockedRank.mockReset()
    mockedListJobs.mockResolvedValue([{ id: 'job-1', title: 'Platform Engineer' } as never])
    mockedRank.mockResolvedValue({ job_spec_id: 'job-1', job_title: 'Platform Engineer', candidates: [] })
  })

  it('hides Plan questions/Create session once the candidate has completed their interview', async () => {
    mockedListApps.mockResolvedValue([
      {
        id: 'app-1',
        job_spec_id: 'job-1',
        candidate_name: 'Alex Morgan',
        stage: 'INTERVIEW',
        gap_analysis_id: 'analysis-1',
        has_completed_interview: true,
      } as never,
    ])

    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <CandidateRankingPage />
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'Rank applicants' }))

    expect(await screen.findByText('Interview completed · View report')).toBeInTheDocument()
    expect(screen.queryByText('Plan questions')).not.toBeInTheDocument()
    expect(screen.queryByText('Create session')).not.toBeInTheDocument()
  })

  it('still shows Plan questions/Create session for shortlisted candidates without a completed interview', async () => {
    mockedListApps.mockResolvedValue([
      {
        id: 'app-2',
        job_spec_id: 'job-1',
        candidate_name: 'Jordan Lee',
        stage: 'SHORTLISTED',
        gap_analysis_id: 'analysis-2',
        has_completed_interview: false,
      } as never,
    ])

    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <CandidateRankingPage />
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'Rank applicants' }))

    expect(await screen.findByText('Plan questions')).toBeInTheDocument()
    expect(screen.getByText('Create session')).toBeInTheDocument()
  })
})
