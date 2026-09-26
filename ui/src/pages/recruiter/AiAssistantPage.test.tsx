import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiAssistantPage } from './AiAssistantPage'

vi.mock('../../api/analysis', () => ({
  listJobSpecs: vi.fn(),
}))

vi.mock('../../api/optional', () => ({
  getNextActions: vi.fn(),
  queryAssistant: vi.fn(),
}))

import { listJobSpecs } from '../../api/analysis'
import { getNextActions } from '../../api/optional'

const mockedListJobs = vi.mocked(listJobSpecs)
const mockedNextActions = vi.mocked(getNextActions)

describe('AiAssistantPage next actions panel', () => {
  beforeEach(() => {
    mockedListJobs.mockReset()
    mockedNextActions.mockReset()
    mockedListJobs.mockResolvedValue([])
  })

  it('renders next actions returned by the API', async () => {
    mockedNextActions.mockResolvedValue({
      generated_from: 'pipeline-rules',
      items: [
        {
          id: 'sessions-unconfirmed',
          priority: 0,
          title: '2 scheduled interviews awaiting confirmation',
          detail: 'These candidates have not confirmed their interview slot yet.',
          cta_label: 'Open scheduling',
          cta_path: '/recruiter/scheduling',
        },
      ],
    })

    render(
      <MemoryRouter>
        <AiAssistantPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('2 scheduled interviews awaiting confirmation')).toBeInTheDocument()
    expect(screen.getByText('Blocked')).toBeInTheDocument()
    expect(screen.getByText('Open scheduling')).toBeInTheDocument()
  })

  it('hides the panel and does not crash the page when the fetch fails', async () => {
    mockedNextActions.mockRejectedValue(new Error('network error'))

    render(
      <MemoryRouter>
        <AiAssistantPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('AI Assistant')).toBeInTheDocument()
    expect(screen.queryByText('Next actions')).not.toBeInTheDocument()
  })
})
