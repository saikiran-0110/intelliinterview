type StatCardProps = {
  label: string
  value: string
  change?: string
  tone?: 'default' | 'brand' | 'accent' | 'warning'
}

const toneStyles = {
  default: 'text-white',
  brand: 'text-teal-300',
  accent: 'text-indigo-300',
  warning: 'text-amber-300',
}

export function StatCard({ label, value, change, tone = 'default' }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-surface-raised p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${toneStyles[tone]}`}>{value}</p>
      {change && <p className="mt-1 text-xs text-slate-500">{change}</p>}
    </div>
  )
}
