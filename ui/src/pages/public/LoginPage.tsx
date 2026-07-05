import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'

type LoginPageProps = {
  role: 'recruiter' | 'candidate'
}

export function LoginPage({ role }: LoginPageProps) {
  const isRecruiter = role === 'recruiter'
  const portalPath = isRecruiter ? '/recruiter' : '/candidate'
  const accent = isRecruiter ? 'teal' : 'violet'

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="pointer-events-none absolute inset-0">
        <div
          className={`absolute left-1/2 top-1/3 h-80 w-80 -translate-x-1/2 rounded-full blur-3xl ${
            isRecruiter ? 'bg-teal-500/10' : 'bg-violet-500/10'
          }`}
        />
      </div>

      <Card className="relative w-full max-w-md">
        <Link to="/" className="text-xs font-medium text-slate-500 hover:text-slate-300">
          Back to home
        </Link>

        <div className="mt-6">
          <p className={`text-sm font-semibold ${isRecruiter ? 'text-teal-400' : 'text-violet-400'}`}>
            {isRecruiter ? 'Recruiter' : 'Candidate'} login
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white">Sign in to IntelliInterview</h1>
          <p className="mt-2 text-sm text-slate-400">
            Authentication is not implemented yet. Use the button below to enter the portal.
          </p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={(e) => e.preventDefault()}>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Email</label>
            <input
              type="email"
              placeholder={isRecruiter ? 'recruiter@company.com' : 'candidate@email.com'}
              disabled
              className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-slate-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              disabled
              className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-slate-500"
            />
          </div>
          <button
            type="button"
            disabled
            className="w-full rounded-xl border border-border bg-surface-overlay py-2.5 text-sm font-medium text-slate-500"
          >
            Sign in (coming soon)
          </button>
        </form>

        <Link
          to={portalPath}
          className={`mt-4 flex w-full items-center justify-center rounded-xl py-3 text-sm font-semibold transition ${
            isRecruiter
              ? 'bg-teal-500 text-slate-950 hover:bg-teal-400'
              : 'bg-violet-500 text-white hover:bg-violet-400'
          }`}
        >
          Enter {isRecruiter ? 'recruiter' : 'candidate'} portal
        </Link>

        <p className="mt-6 text-center text-xs text-slate-600">
          JWT auth with role-based access ,  {accent} portal
        </p>
      </Card>
    </div>
  )
}
