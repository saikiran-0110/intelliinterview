import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiAssistantPage } from './AiAssistantPage'

vi.mock('../../api/analysis', () => ({
  listJobSpecs: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  queryAssistant: vi.fn(),
}))

import { listJobSpecs } from '../../api/analysis'

const mockedListJobs = vi.mocked(listJobSpecs)

describe('AiAssistantPage', () => {
  beforeEach(() => {
    mockedListJobs.mockReset()
    mockedListJobs.mockResolvedValue([])
  })

  it('renders the assistant without a next-actions panel (moved to the dashboard)', async () => {
    render(
      <MemoryRouter>
        <AiAssistantPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('AI Assistant')).toBeInTheDocument()
    expect(screen.queryByText('Next actions')).not.toBeInTheDocument()
  })
})
