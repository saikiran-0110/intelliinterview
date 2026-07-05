import { useEffect, useState } from 'react'

type HealthStatus = {
  status: string
  application: string
  timestamp: string
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Backend unavailable')
        }
        return response.json()
      })
      .then((data: HealthStatus) => setHealth(data))
      .catch(() => setError('Start the FastAPI backend on port 8080 to connect.'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">CO7201 Project</p>
            <h1 className="text-2xl font-semibold">IntelliInterview</h1>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              health?.status === 'UP'
                ? 'bg-emerald-500/15 text-emerald-300'
                : 'bg-amber-500/15 text-amber-300'
            }`}
          >
            {health?.status === 'UP' ? 'API Connected' : 'API Pending'}
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        <section className="mb-12 max-w-3xl">
          <h2 className="mb-4 text-4xl font-bold leading-tight">
            AI-assisted interviews for software engineering roles
          </h2>
          <p className="text-lg text-slate-300">
            Prepare CV gap analysis, run live AI interviews with text and voice, and generate
            structured recruiter reports — built with React, FastAPI, PostgreSQL, and GPT-4o.
          </p>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <p className="mb-2 text-sm font-medium text-cyan-400">Recruiter portal</p>
            <h3 className="mb-3 text-xl font-semibold">Prepare and review interviews</h3>
            <ul className="mb-6 space-y-2 text-sm text-slate-300">
              <li>Upload CV and job specification</li>
              <li>Configure AI + custom question sets</li>
              <li>Launch sessions and view reports</li>
            </ul>
            <button
              type="button"
              className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
            >
              Recruiter login (coming soon)
            </button>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <p className="mb-2 text-sm font-medium text-violet-400">Candidate portal</p>
            <h3 className="mb-3 text-xl font-semibold">Join your scheduled session</h3>
            <ul className="mb-6 space-y-2 text-sm text-slate-300">
              <li>Access assigned interview sessions</li>
              <li>Answer via text or speech-to-text</li>
              <li>Listen to questions with text-to-speech</li>
            </ul>
            <button
              type="button"
              className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400"
            >
              Candidate login (coming soon)
            </button>
          </article>
        </section>

        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h3 className="mb-2 text-lg font-semibold">System status</h3>
          {health ? (
            <p className="text-sm text-slate-300">
              {health.application} is {health.status.toLowerCase()} — last checked{' '}
              {new Date(health.timestamp).toLocaleString()}
            </p>
          ) : (
            <p className="text-sm text-amber-300">{error ?? 'Checking backend connection...'}</p>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
