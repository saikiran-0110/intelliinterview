type BadgeVariant = 'default' | 'success' | 'warning' | 'info'

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-slate-500/15 text-slate-300 ring-slate-500/25',
  success: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/25',
  warning: 'bg-amber-500/15 text-amber-300 ring-amber-500/25',
  info: 'bg-sky-500/15 text-sky-300 ring-sky-500/25',
}

type BadgeProps = {
  children: React.ReactNode
  variant?: BadgeVariant
}

export function Badge({ children, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${variantStyles[variant]}`}
    >
      {children}
    </span>
  )
}
