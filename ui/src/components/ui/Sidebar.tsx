import { NavLink } from 'react-router-dom'
import type { NavItem } from '../../config/navigation'

type SidebarProps = {
  title: string
  subtitle: string
  items: NavItem[]
  accent: 'teal' | 'sky'
  homePath: string
}

const accentActive = {
  teal: 'bg-teal-50 text-teal-900 border-teal-300 shadow-sm',
  sky: 'bg-sky-50 text-sky-900 border-sky-300 shadow-sm',
}

export function Sidebar({ title, subtitle, items, accent, homePath }: SidebarProps) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-teal-200/80 bg-gradient-to-b from-teal-50/95 to-sky-50/80 backdrop-blur">
      <div className="border-b border-teal-200/80 px-5 py-5">
        <NavLink to={homePath} className="group block">
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-teal-800 group-hover:text-teal-900">
            IntelliInterview
          </p>
          <h2 className="mt-1 font-display text-xl font-bold text-ink">{title}</h2>
          <p className="mt-1 text-sm text-muted">{subtitle}</p>
        </NavLink>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1.5">
          {items.map((item, index) => (
            <li
              key={item.path}
              className="animate-fade-up"
              style={{ animationDelay: `${index * 0.03}s` }}
            >
              <NavLink
                to={item.path}
                end={item.path === homePath}
                className={({ isActive }) =>
                  `flex flex-col rounded-xl border px-3.5 py-3 text-base transition-all duration-200 ${
                    isActive
                      ? accentActive[accent]
                      : 'border-transparent text-slate-700 hover:border-border hover:bg-surface-overlay hover:text-ink'
                  }`
                }
              >
                <span className="font-bold">{item.label}</span>
                {item.description && (
                  <span className="mt-0.5 text-sm font-medium opacity-80">{item.description}</span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-border px-5 py-4">
        <NavLink
          to="/"
          className="text-sm font-semibold text-muted transition-colors hover:text-teal-800"
        >
          Back to home
        </NavLink>
      </div>
    </aside>
  )
}
