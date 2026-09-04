import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createSession, getSession, listSessions, startSession, submitAnswer } from './sessions'
import { generateQuestions, listQuestionPlans, updateQuestion } from './questions'
import { generateReport, getReport, listReports } from './reports'
import { formatSalaryGbp, listOpenJobs, previewJobMatch, queryAssistant } from './optional'
import { getAnalyticsOverview, listNotifications, proposeSlots } from './desirable'
import { getGapAnalysis, login, runGapAnalysis, startLogin, verifyOtp } from './analysis'

vi.mock('./client', () => ({
  apiRequest: vi.fn(),
}))

import { apiRequest } from './client'

const mockedRequest = vi.mocked(apiRequest)

describe('api wrappers', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedRequest.mockResolvedValue({ ok: true })
  })

  it('createSession posts plan, email and follow-up limit', async () => {
    await createSession('plan-1', 'alex@example.com', 2)
    expect(mockedRequest).toHaveBeenCalledWith('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({
        question_plan_id: 'plan-1',
        candidate_email: 'alex@example.com',
        follow_up_limit: 2,
      }),
    })
  })

  it('lists, loads, starts and answers sessions', async () => {
    await listSessions()
    await getSession('s1')
    await startSession('s1')
    await submitAnswer('s1', 'I used FastAPI')
    expect(mockedRequest).toHaveBeenNthCalledWith(1, '/api/sessions')
    expect(mockedRequest).toHaveBeenNthCalledWith(2, '/api/sessions/s1')
    expect(mockedRequest).toHaveBeenNthCalledWith(3, '/api/sessions/s1/start', { method: 'POST' })
    expect(mockedRequest.mock.calls[3][1]).toMatchObject({ method: 'POST' })
  })

  it('question and report helpers hit the expected paths', async () => {
    await generateQuestions('gap-1')
    await listQuestionPlans()
    await updateQuestion('q1', { approved: false })
    await listReports()
    await getReport('r1')
    await generateReport('s1')
    expect(mockedRequest).toHaveBeenCalledWith('/api/questions/generate', expect.any(Object))
    expect(mockedRequest).toHaveBeenCalledWith('/api/questions/q1', expect.objectContaining({ method: 'PATCH' }))
    expect(mockedRequest).toHaveBeenCalledWith('/api/reports/generate/s1', { method: 'POST' })
  })

  it('formats GBP salaries and builds optional requests', async () => {
    expect(formatSalaryGbp(65000, 85000)).toContain('65,000')
    expect(formatSalaryGbp(65000, 85000)).toContain('85,000')
    expect(formatSalaryGbp(70000)).toMatch(/^From /)
    expect(formatSalaryGbp(null, 90000)).toMatch(/^Up to /)
    expect(formatSalaryGbp()).toBe('Salary on request')

    await listOpenJobs()
    await previewJobMatch('job-1', 'cv-1')
    await queryAssistant('Who should I shortlist?')
    expect(mockedRequest).toHaveBeenCalledWith('/api/job-specs/open')
    expect(mockedRequest).toHaveBeenCalledWith('/api/assistant/query', expect.any(Object))
  })

  it('scheduling, analytics and auth helpers send json bodies', async () => {
    await proposeSlots('s1', 3, 30)
    await listNotifications()
    await getAnalyticsOverview()
    await startLogin('user@test.com')
    await verifyOtp('user@test.com', '123456', 'LOGIN')
    await login('user@test.com', 'password123')
    await runGapAnalysis('cv-1', 'job-1')
    await getGapAnalysis('gap-1')
    expect(mockedRequest).toHaveBeenCalledWith('/api/scheduling/propose', expect.any(Object))
    expect(mockedRequest).toHaveBeenCalledWith('/api/auth/otp/verify', expect.any(Object))
    expect(mockedRequest).toHaveBeenCalledWith('/api/analysis/gap', expect.any(Object))
  })
})
