type CardProps = {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-border bg-surface-raised p-6 shadow-lg shadow-black/20 ${
        hover ? 'transition-colors hover:border-teal-500/30 hover:bg-surface-overlay' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
