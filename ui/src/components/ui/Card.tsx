type CardProps = {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-teal-200/80 bg-gradient-to-br from-white/90 via-[#f3fbf8] to-[#e7f5ff]/70 p-6 shadow-md shadow-teal-900/5 backdrop-blur-sm ${
        hover
          ? 'transition-all duration-200 hover:-translate-y-0.5 hover:border-teal-400 hover:shadow-lg hover:shadow-teal-200/50'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
