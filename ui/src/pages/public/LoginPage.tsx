import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerRecruiter, login } from '../../api/analysis'
import { setAuth } from '../../api/client'
import { Card } from '../../components/ui/Card'

type LoginPageProps = {
  role: 'recruiter' | 'candidate'
}

export function LoginPage({ role }: LoginPageProps) {
  const navigate = useNavigate()
  const isRecruiter = role === 'recruiter'
  const portalPath = isRecruiter ? '/recruiter' : '/candidate'

  const [email, setEmail] = useState(isRecruiter ? 'recruiter@example.com' : 'candidate@example.com')
  const [password, setPassword] = useState('password123')
  const [fullName, setFullName] = useState('Demo Recruiter')
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)

    try {
      if (!isRecruiter) {
        setError('Candidate login will be enabled in a later module. Use the recruiter portal for analysis.')
        return
      }

      const response =
        mode === 'register'
          ? await registerRecruiter(email, password, fullName)
          : await login(email, password)

      setAuth(response.token, {
        user_id: response.user_id,
        email: response.email,
        full_name: response.full_name,
        role: response.role,
      })
      navigate(portalPath)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

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
            {isRecruiter
              ? 'Sign in to upload CVs, manage job specifications, and run gap analysis.'
              : 'Candidate access for interview sessions.'}
          </p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          {mode === 'register' && isRecruiter && (
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-400">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-slate-100"
                required
              />
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-slate-100"
              required
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-slate-100"
              required
              minLength={8}
            />
          </div>

          {error && <p className="text-sm text-rose-300">{error}</p>}

          <button
            type="submit"
            disabled={loading || !isRecruiter}
            className={`w-full rounded-xl py-2.5 text-sm font-semibold transition ${
              isRecruiter
                ? 'bg-teal-500 text-slate-950 hover:bg-teal-400 disabled:bg-teal-500/50'
                : 'bg-violet-500/50 text-white'
            }`}
          >
            {loading ? 'Please wait...' : mode === 'register' ? 'Create recruiter account' : 'Sign in'}
          </button>
        </form>

        {isRecruiter && (
          <button
            type="button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="mt-4 w-full text-sm text-slate-400 hover:text-slate-200"
          >
            {mode === 'login' ? 'Need an account? Register as recruiter' : 'Already registered? Sign in'}
          </button>
        )}
      </Card>
    </div>
  )
}
