import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from './Badge'
import { Card } from './Card'
import { PageHeader } from './PageHeader'
import { PlaceholderPanel } from './PlaceholderPanel'
import { StatCard } from './StatCard'

describe('shared UI components', () => {
  it('renders badge children', () => {
    render(<Badge variant="success">Shortlisted</Badge>)
    expect(screen.getByText('Shortlisted')).toBeInTheDocument()
  })

  it('renders card content and optional hover class', () => {
    const { container } = render(
      <Card hover className="extra">
        Body
      </Card>,
    )
    expect(screen.getByText('Body')).toBeInTheDocument()
    expect(container.firstChild).toHaveClass('extra')
  })

  it('renders page header action slot', () => {
    render(<PageHeader title="Hiring Board" description="Open roles" action={<button type="button">New role</button>} />)
    expect(screen.getByRole('heading', { name: 'Hiring Board' })).toBeInTheDocument()
    expect(screen.getByText('Open roles')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New role' })).toBeInTheDocument()
  })

  it('renders stat card change text', () => {
    render(<StatCard label="Open roles" value="4" change="+1 this week" tone="brand" />)
    expect(screen.getByText('Open roles')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('+1 this week')).toBeInTheDocument()
  })

  it('renders placeholder items or empty state', () => {
    const { rerender } = render(
      <PlaceholderPanel title="Coming soon" description="Not wired yet" items={[{ label: 'Charts', hint: 'Soon' }]} />,
    )
    expect(screen.getByText('Coming soon')).toBeInTheDocument()
    expect(screen.getByText('Charts')).toBeInTheDocument()
    rerender(<PlaceholderPanel title="Empty" />)
    expect(screen.getByText(/Feature UI placeholder/)).toBeInTheDocument()
  })
})
