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

import { getReport } from '../../api/reports'
import { getRecordingBlob } from '../../api/sessions'

const mockedGetReport = vi.mocked(getReport)
const mockedGetRecordingBlob = vi.mocked(getRecordingBlob)

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
} as never

describe('ReportDetailPage print/export', () => {
  beforeEach(() => {
    mockedGetReport.mockReset()
    mockedGetRecordingBlob.mockReset()
    mockedGetReport.mockResolvedValue(sampleReport)
    mockedGetRecordingBlob.mockRejectedValue(new Error('no recording'))
    vi.stubGlobal('print', vi.fn())
  })

  it('renders a Print / Export PDF button that calls window.print', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/recruiter/reports/report-1']}>
        <Routes>
          <Route path="/recruiter/reports/:reportId" element={<ReportDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const printButton = await screen.findByRole('button', { name: 'Print / Export PDF' })
    await user.click(printButton)

    expect(window.print).toHaveBeenCalledTimes(1)
  })
})
