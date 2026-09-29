import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/desirable'
import type { AppNotification } from '../../types/desirable'

const POLL_INTERVAL_MS = 30000

function toRelativePath(link: string): string {
  if (!link.startsWith('http')) return link
  try {
    return new URL(link).pathname
  } catch {
    return link
  }
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/** Shared notification bell for both recruiter and candidate headers. Polls periodically
 * so new notifications show up without a manual refresh. */
export function NotificationBell() {
  const navigate = useNavigate()
  const [items, setItems] = useState<AppNotification[]>([])
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  async function load() {
    try {
      const result = await listNotifications()
      setItems(Array.isArray(result) ? result : [])
    } catch {
      // Silent: the bell is a convenience, never block the rest of the app on it.
    }
  }

  useEffect(() => {
    load()
    const timer = window.setInterval(load, POLL_INTERVAL_MS)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unreadCount = items.filter((item) => !item.is_read).length
  const recent = items.slice(0, 10)

  async function handleSelect(item: AppNotification) {
    setOpen(false)
    if (!item.is_read) {
      setItems((current) => current.map((n) => (n.id === item.id ? { ...n, is_read: true } : n)))
      try {
        await markNotificationRead(item.id)
      } catch {
        // Non-critical; the next poll will reconcile state either way.
      }
    }
    if (item.link) {
      navigate(toRelativePath(item.link))
    }
  }

  async function handleMarkAllRead() {
    setItems((current) => current.map((n) => ({ ...n, is_read: true })))
    try {
      await markAllNotificationsRead()
    } catch {
      // Non-critical; the next poll will reconcile state either way.
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={unreadCount > 0 ? `${unreadCount} unread notifications` : 'Notifications'}
        className="relative flex min-h-11 min-w-11 items-center justify-center rounded-full border border-border bg-surface text-lg"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1 text-[11px] font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 max-w-[90vw] rounded-2xl border border-border bg-surface-raised shadow-lg">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <p className="text-sm font-semibold text-ink">Notifications</p>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs font-semibold text-teal-700 hover:text-teal-800"
              >
                Mark all as read
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {recent.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted">No notifications yet.</p>
            ) : (
              recent.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleSelect(item)}
                  className={`block w-full border-b border-border/60 px-4 py-3 text-left last:border-b-0 hover:bg-surface-overlay ${
                    item.is_read ? '' : 'bg-sky-50/60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-sm ${item.is_read ? 'font-medium text-slate-700' : 'font-semibold text-ink'}`}>
                      {item.title}
                    </p>
                    {!item.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-sky-600" />}
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-muted">{item.body}</p>
                  <p className="mt-1 text-[11px] text-slate-400">{timeAgo(item.created_at)}</p>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
