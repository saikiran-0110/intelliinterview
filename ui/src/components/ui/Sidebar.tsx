import { NavLink } from 'react-router-dom'
import type { NavItem } from '../../config/navigation'

type SidebarProps = {
  title: string
  subtitle: string
  items: NavItem[]
  accent: 'teal' | 'violet'
  homePath: string
}

const accentActive = {
  teal: 'bg-teal-500/15 text-teal-200 border-teal-500/30',
  violet: 'bg-violet-500/15 text-violet-200 border-violet-500/30',
}

export function Sidebar({ title, subtitle, items, accent, homePath }: SidebarProps) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-surface-raised">
      <div className="border-b border-border px-5 py-5">
        <NavLink to={homePath} className="group block">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 group-hover:text-slate-400">
            IntelliInterview
          </p>
          <h2 className="mt-1 text-lg font-bold text-white">{title}</h2>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </NavLink>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {items.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === homePath}
                className={({ isActive }) =>
                  `flex flex-col rounded-xl border px-3 py-2.5 text-sm transition-colors ${
                    isActive
                      ? accentActive[accent]
                      : 'border-transparent text-slate-400 hover:border-border hover:bg-surface-overlay hover:text-slate-200'
                  }`
                }
              >
                <span className="font-medium">{item.label}</span>
                {item.description && (
                  <span className="mt-0.5 text-xs opacity-70">{item.description}</span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-border px-5 py-4">
        <NavLink
          to="/"
          className="text-xs font-medium text-slate-500 transition-colors hover:text-slate-300"
        >
          Back to home
        </NavLink>
      </div>
    </aside>
  )
}
