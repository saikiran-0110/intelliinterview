import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'

vi.mock('../../api/desirable', () => ({
  getAnalyticsOverview: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  getNextActions: vi.fn(),
}))

import { getAnalyticsOverview } from '../../api/desirable'
import { getNextActions } from '../../api/optional'

const mockedAnalytics = vi.mocked(getAnalyticsOverview)
const mockedNextActions = vi.mocked(getNextActions)

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedAnalytics.mockReset()
    mockedNextActions.mockReset()
    mockedNextActions.mockResolvedValue({ generated_from: 'pipeline-rules', items: [] })
  })

  it('shows key stats and quick links', async () => {
    mockedAnalytics.mockResolvedValue({
      total_roles: 3,
      total_applications: 12,
      total_sessions: 5,
      completed_reports: 2,
      applications_per_role: [],
      pipeline_stages: [],
      open_positions: [],
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('3')).toBeInTheDocument()
    expect(screen.getByText('Open roles')).toBeInTheDocument()
    expect(screen.getByText('Hiring Board')).toBeInTheDocument()
    expect(screen.getByText('Candidate Ranking')).toBeInTheDocument()
  })

  it('renders quick links even when analytics fails to load', async () => {
    mockedAnalytics.mockRejectedValue(new Error('network error'))

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Hiring Board')).toBeInTheDocument()
  })
})
