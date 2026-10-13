type CardProps = {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-border bg-surface-raised/90 p-6 shadow-md shadow-ink/5 backdrop-blur-sm ${
        hover
          ? 'transition-all duration-200 hover:-translate-y-0.5 hover:border-border-subtle hover:shadow-lg'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
