import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { recruiterNav } from '../../config/navigation'
import { Sidebar } from './Sidebar'

describe('Sidebar', () => {
  it('renders brand, nav items and portal links', () => {
    render(
      <MemoryRouter>
        <Sidebar
          title="Recruiter Portal"
          subtitle="Hire end to end"
          items={recruiterNav}
          accent="teal"
          homePath="/recruiter/jobs"
        />
      </MemoryRouter>,
    )
    expect(screen.getByText('IntelliInterview')).toBeInTheDocument()
    expect(screen.getByText('Recruiter Portal')).toBeInTheDocument()
    expect(screen.getByText('Hiring Board')).toBeInTheDocument()
    expect(screen.getByText('Back to portal home')).toBeInTheDocument()
    expect(screen.getByText('Public landing page')).toHaveAttribute('href', '/')
  })
})
