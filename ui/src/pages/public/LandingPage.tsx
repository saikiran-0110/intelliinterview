import { Link } from 'react-router-dom'
import { Badge } from '../../components/ui/Badge'
import { Card } from '../../components/ui/Card'

const workflowSteps = [
  {
    phase: 'Before',
    title: 'CV & gap analysis',
    description: 'Parse CV and job spec, identify skill gaps, generate tailored questions.',
  },
  {
    phase: 'During',
    title: 'AI interview session',
    description: 'Live questioning with text, speech-to-text, and text-to-speech support.',
  },
  {
    phase: 'After',
    title: 'Structured evaluation',
    description: 'Evidence-linked reports across technical fit, communication, and role alignment.',
  },
]

const recruiterFlow = [
  'Upload CV and job specifications',
  'Review gap analysis and match scoring',
  'Plan AI-generated and custom interview questions',
  'Schedule and launch interview sessions',
  'Monitor live sessions and pipeline progress',
  'Read structured evaluation reports',
  'Use analytics, bias detection, and AI assistant',
]

const candidateFlow = [
  'Register and manage your profile & CV',
  'Browse roles and submit applications',
  'Confirm or reschedule interview slots',
  'Prepare with personalised practice questions',
  'Join live AI interviews via text or voice',
  'Review post-interview feedback and guidance',
]

export function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-32 top-0 h-96 w-96 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="absolute -right-32 top-32 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl" />
      </div>

      <header className="relative border-b border-border/60 bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold text-white">IntelliInterview</h1>
          </div>
          <div className="flex gap-3">
            <Link
              to="/recruiter/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              Recruiter login
            </Link>
            <Link
              to="/candidate/login"
              className="rounded-lg bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-teal-400"
            >
              Candidate login
            </Link>
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-6xl px-6 py-16">
        <section className="mb-20 max-w-3xl">
          <Badge variant="info">Software engineering recruitment</Badge>
          <h2 className="mt-4 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
            AI-assisted interviews from preparation to evaluation
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-slate-400">
            IntelliInterview supports recruiters and candidates through the technical interview stage -
            analysing CVs against job specifications, conducting role-specific AI interviews, and
            producing structured, evidence-linked assessment reports.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/recruiter"
              className="rounded-xl bg-teal-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-teal-500/20 transition hover:bg-teal-400"
            >
              Recruiter portal
            </Link>
            <Link
              to="/candidate"
              className="rounded-xl border border-border bg-surface-raised px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-violet-500/40 hover:bg-surface-overlay"
            >
              Candidate portal
            </Link>
          </div>
        </section>

        <section className="mb-20 grid gap-6 md:grid-cols-3">
          {workflowSteps.map((step) => (
            <Card key={step.phase} hover>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{step.phase} interview</p>
              <h3 className="mt-2 text-lg font-bold text-white">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{step.description}</p>
            </Card>
          ))}
        </section>

        <section className="mb-20">
          <h3 className="mb-6 text-2xl font-bold text-white">Two connected workflows</h3>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-teal-500/20">
              <p className="text-sm font-medium text-teal-400">Recruiter flow</p>
              <h4 className="mt-1 text-lg font-bold text-white">Hire with confidence</h4>
              <ul className="mt-4 space-y-2">
                {recruiterFlow.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-slate-400">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/recruiter"
                className="mt-5 inline-block text-sm font-semibold text-teal-300 hover:text-teal-200"
              >
                Enter recruiter portal
              </Link>
            </Card>

            <Card className="border-violet-500/20">
              <p className="text-sm font-medium text-violet-400">Candidate flow</p>
              <h4 className="mt-1 text-lg font-bold text-white">Interview with clarity</h4>
              <ul className="mt-4 space-y-2">
                {candidateFlow.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-slate-400">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/candidate"
                className="mt-5 inline-block text-sm font-semibold text-violet-300 hover:text-violet-200"
              >
                Enter candidate portal
              </Link>
            </Card>
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <Card className="border-teal-500/20 bg-gradient-to-br from-surface-raised to-teal-500/5">
            <p className="text-sm font-medium text-teal-400">For recruiters</p>
            <h3 className="mt-2 text-xl font-bold text-white">Prepare and review interviews</h3>
            <p className="mt-2 text-sm text-slate-400">
              Upload documents, review gap analysis, plan questions, launch sessions, and read
              structured evaluation reports - all from one dashboard.
            </p>
            <Link
              to="/recruiter"
              className="mt-5 inline-block text-sm font-semibold text-teal-300 hover:text-teal-200"
            >
              Open recruiter portal
            </Link>
          </Card>

          <Card className="border-violet-500/20 bg-gradient-to-br from-surface-raised to-violet-500/5">
            <p className="text-sm font-medium text-violet-400">For candidates</p>
            <h3 className="mt-2 text-xl font-bold text-white">Join your AI interview session</h3>
            <p className="mt-2 text-sm text-slate-400">
              Access scheduled sessions, respond via text or voice, listen to questions with TTS, and
              receive personalised feedback after completion.
            </p>
            <Link
              to="/candidate"
              className="mt-5 inline-block text-sm font-semibold text-violet-300 hover:text-violet-200"
            >
              Open candidate portal
            </Link>
          </Card>
        </section>
      </main>

      <footer className="relative border-t border-border py-8 text-center text-xs text-slate-600">
        IntelliInterview, University of Leicester
      </footer>
    </div>
  )
}
