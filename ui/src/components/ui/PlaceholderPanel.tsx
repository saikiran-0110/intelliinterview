import { Card } from './Card'

type PlaceholderItem = {
  label: string
  hint?: string
}

type PlaceholderPanelProps = {
  title: string
  description?: string
  items?: PlaceholderItem[]
  columns?: 1 | 2 | 3
}

export function PlaceholderPanel({
  title,
  description,
  items = [],
  columns = 2,
}: PlaceholderPanelProps) {
  const gridCols = columns === 1 ? 'grid-cols-1' : columns === 3 ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2'

  return (
    <Card>
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-ink">{title}</h3>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>

      {items.length > 0 ? (
        <div className={`grid gap-4 ${gridCols}`}>
          {items.map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-dashed border-border bg-surface/60 p-4"
            >
              <p className="text-sm font-medium text-ink">{item.label}</p>
              {item.hint && <p className="mt-1 text-xs text-slate-500">{item.hint}</p>}
              <div className="mt-3 h-8 rounded-lg bg-surface-overlay/80" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex min-h-32 items-center justify-center rounded-xl border border-dashed border-border bg-surface/40">
          <p className="text-sm text-slate-500">Feature UI placeholder - not yet implemented</p>
        </div>
      )}
    </Card>
  )
}
