import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ReportDetailPage } from './ReportDetailPage'

vi.mock('../../api/reports', () => ({
  getReport: vi.fn(),
}))

vi.mock('../../api/sessions', () => ({
  getRecordingBlob: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  getUserPhotoBlob: vi.fn(),
  updateApplicationStage: vi.fn(),
}))

import { getReport } from '../../api/reports'
import { getRecordingBlob } from '../../api/sessions'
import { getUserPhotoBlob, updateApplicationStage } from '../../api/optional'

const mockedGetReport = vi.mocked(getReport)
const mockedGetRecordingBlob = vi.mocked(getRecordingBlob)
const mockedGetUserPhotoBlob = vi.mocked(getUserPhotoBlob)
const mockedUpdateApplicationStage = vi.mocked(updateApplicationStage)

const sampleReport = {
  id: 'report-1',
  session_id: 'session-1',
  candidate_name: 'Alex Morgan',
  candidate_email: 'alex@example.com',
  job_title: 'Senior Backend Engineer',
  plan_title: 'Plan',
  technical_fit_score: 8,
  communication_score: 7,
  problem_solving_score: 7.5,
  role_alignment_score: 8,
  overall_score: 7.6,
  recommendation: 'HIRE',
  recommendation_summary: 'Strong candidate overall.',
  strengths: ['Clear communicator'],
  weaknesses: [],
  evidence_items: [],
  dimension_notes: null,
  model_version: 'gpt-4o',
  generated_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
  application_id: 'application-1',
  application_stage: 'INTERVIEW',
  candidate_user_id: 'candidate-1',
  candidate_has_photo: false,
} as never

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/recruiter/reports/report-1']}>
      <Routes>
        <Route path="/recruiter/reports/:reportId" element={<ReportDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ReportDetailPage print/export', () => {
  beforeEach(() => {
    mockedGetReport.mockReset()
    mockedGetRecordingBlob.mockReset()
    mockedGetUserPhotoBlob.mockReset()
    mockedUpdateApplicationStage.mockReset()
    mockedGetReport.mockResolvedValue(sampleReport)
    mockedGetRecordingBlob.mockRejectedValue(new Error('no recording'))
    mockedGetUserPhotoBlob.mockRejectedValue(new Error('no photo'))
    vi.stubGlobal('print', vi.fn())
  })

  it('renders a Print / Export PDF button that calls window.print', async () => {
    const user = userEvent.setup()
    renderPage()

    const printButton = await screen.findByRole('button', { name: 'Print / Export PDF' })
    await user.click(printButton)

    expect(window.print).toHaveBeenCalledTimes(1)
  })
})

describe('ReportDetailPage hiring decision', () => {
  beforeEach(() => {
    mockedGetReport.mockReset()
    mockedGetRecordingBlob.mockReset()
    mockedGetUserPhotoBlob.mockReset()
    mockedUpdateApplicationStage.mockReset()
    mockedGetReport.mockResolvedValue(sampleReport)
    mockedGetRecordingBlob.mockRejectedValue(new Error('no recording'))
    mockedGetUserPhotoBlob.mockRejectedValue(new Error('no photo'))
  })

  it('shows the current stage and lets a recruiter advance the candidate', async () => {
    const user = userEvent.setup()
    mockedUpdateApplicationStage.mockResolvedValue({ ...sampleReport, stage: 'OFFER' } as never)
    renderPage()

    expect(await screen.findByText('Hiring decision')).toBeInTheDocument()
    expect(screen.getByText('Interview')).toBeInTheDocument()

    const message = screen.getByPlaceholderText("Optional message to include in the candidate's email")
    await user.type(message, 'Great fit for the team')

    const advanceButton = screen.getByRole('button', { name: 'Advance to next stage' })
    await user.click(advanceButton)

    expect(mockedUpdateApplicationStage).toHaveBeenCalledWith('application-1', 'OFFER', 'Great fit for the team')
    expect(await screen.findByText(/Candidate notified by email: Next stage\./)).toBeInTheDocument()
  })

  it('lets a recruiter reject the candidate', async () => {
    const user = userEvent.setup()
    mockedUpdateApplicationStage.mockResolvedValue({ ...sampleReport, stage: 'REJECTED' } as never)
    renderPage()

    const rejectButton = await screen.findByRole('button', { name: 'Reject' })
    await user.click(rejectButton)

    expect(mockedUpdateApplicationStage).toHaveBeenCalledWith('application-1', 'REJECTED', undefined)
    expect(await screen.findByText(/Candidate notified by email: Rejected\./)).toBeInTheDocument()
  })

  it('does not offer a hire/offer action for this screening-only tool', async () => {
    renderPage()
    await screen.findByText('Hiring decision')
    expect(screen.queryByRole('button', { name: /hire/i })).not.toBeInTheDocument()
  })

  it('does not render the hiring decision panel without a linked application', async () => {
    mockedGetReport.mockResolvedValue({ ...sampleReport, application_id: null } as never)
    renderPage()

    await screen.findByText('Strengths')
    expect(screen.queryByText('Hiring decision')).not.toBeInTheDocument()
  })
})
