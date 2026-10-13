import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getNextActions } from '../../api/optional'
import { Card } from './Card'
import type { NextActionItem } from '../../types/optional'

/** Deterministic pipeline-rules panel. Fails silently - never blocks the page it sits on. */
export function NextActionsPanel() {
  const [nextActions, setNextActions] = useState<NextActionItem[] | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const result = await getNextActions()
        setNextActions(result.items)
      } catch {
        setNextActions(null)
      }
    }
    load()
  }, [])

  if (!nextActions || nextActions.length === 0 || nextActions[0]?.id === 'nothing-blocked') {
    return null
  }

  return (
    <Card className="mb-6">
      <h3 className="text-sm font-semibold text-ink">Next actions</h3>
      <ul className="mt-3 space-y-3">
        {nextActions.map((item) => (
          <li
            key={item.id}
            className="flex flex-col gap-2 rounded-xl border border-border p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <div className="flex items-center gap-2">
                {item.priority === 0 && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800">
                    Needs action
                  </span>
                )}
                <p className="text-sm font-semibold text-ink">{item.title}</p>
              </div>
              <p className="mt-1 text-xs text-muted">{item.detail}</p>
            </div>
            {item.cta_label && item.cta_path && (
              <Link
                to={item.cta_path}
                className="flex min-h-11 shrink-0 items-center justify-center rounded-xl border border-border px-3 py-2 text-center text-xs font-semibold text-sky-800"
              >
                {item.cta_label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </Card>
  )
}
