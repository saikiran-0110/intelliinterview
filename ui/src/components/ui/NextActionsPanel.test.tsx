import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextActionsPanel } from './NextActionsPanel'

vi.mock('../../api/optional', () => ({
  getNextActions: vi.fn(),
}))

import { getNextActions } from '../../api/optional'

const mockedNextActions = vi.mocked(getNextActions)

describe('NextActionsPanel', () => {
  beforeEach(() => {
    mockedNextActions.mockReset()
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
        <NextActionsPanel />
      </MemoryRouter>,
    )

    expect(await screen.findByText('2 scheduled interviews awaiting confirmation')).toBeInTheDocument()
    expect(screen.getByText('Blocked')).toBeInTheDocument()
    expect(screen.getByText('Open scheduling')).toBeInTheDocument()
  })

  it('renders nothing when nothing is blocked', async () => {
    mockedNextActions.mockResolvedValue({
      generated_from: 'pipeline-rules',
      items: [{ id: 'nothing-blocked', priority: 4, title: 'Nothing is blocked right now', detail: '', cta_label: null, cta_path: null }],
    })

    const { container } = render(
      <MemoryRouter>
        <NextActionsPanel />
      </MemoryRouter>,
    )

    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing and does not crash when the fetch fails', async () => {
    mockedNextActions.mockRejectedValue(new Error('network error'))

    const { container } = render(
      <MemoryRouter>
        <NextActionsPanel />
      </MemoryRouter>,
    )

    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(container).toBeEmptyDOMElement()
  })
})
