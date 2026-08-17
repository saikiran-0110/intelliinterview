type StatCardProps = {
  label: string
  value: string
  change?: string
  tone?: 'default' | 'brand' | 'accent' | 'warning'
}

const toneStyles = {
  default: 'text-ink',
  brand: 'text-teal-700',
  accent: 'text-sky-700',
  warning: 'text-amber-600',
}

export function StatCard({ label, value, change, tone = 'default' }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-white p-5 shadow-sm transition-transform duration-200 hover:-translate-y-0.5">
      <p className="text-sm font-semibold uppercase tracking-wider text-muted">{label}</p>
      <p className={`mt-2 font-display text-4xl font-bold ${toneStyles[tone]}`}>{value}</p>
      {change && <p className="mt-1 text-sm text-muted">{change}</p>}
    </div>
  )
}
