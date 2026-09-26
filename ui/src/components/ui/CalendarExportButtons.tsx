import { useEffect, useState } from 'react'
import { downloadCalendarIcs, getCalendarLinks } from '../../api/desirable'
import type { CalendarLinks } from '../../types/desirable'

type Props = {
  sessionId: string
  scheduledAt: string | null
}

/** Shown on any session with a confirmed slot: download .ics, or open a Google/Outlook add-event link. */
export function CalendarExportButtons({ sessionId, scheduledAt }: Props) {
  const [links, setLinks] = useState<CalendarLinks | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!scheduledAt) {
      setLinks(null)
      return
    }
    getCalendarLinks(sessionId)
      .then(setLinks)
      .catch(() => setLinks(null))
  }, [sessionId, scheduledAt])

  if (!scheduledAt || !links) return null

  async function handleDownload() {
    try {
      const blob = await downloadCalendarIcs(sessionId)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'interview.ics'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download calendar file')
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={handleDownload}
        className="min-h-11 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-sky-700"
      >
        Download .ics
      </button>
      <a
        href={links.google_url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex min-h-11 items-center rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-sky-700"
      >
        Add to Google Calendar
      </a>
      <a
        href={links.outlook_url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex min-h-11 items-center rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-sky-700"
      >
        Add to Outlook
      </a>
      {error && <p className="text-xs text-rose-600">{error}</p>}
    </div>
  )
}
