import { Link } from 'react-router-dom'
import { getStoredUser, getToken } from '../../api/client'
import { Badge } from '../../components/ui/Badge'
import { Card } from '../../components/ui/Card'

const flowSteps = [
  {
    step: '01',
    title: 'Open a role',
    description: 'Recruiters publish a job with salary in £, location, and requirements.',
  },
  {
    step: '02',
    title: 'Apply & match',
    description: 'Candidates upload a resume, check fit, and submit contact details.',
  },
  {
    step: '03',
    title: 'Shortlist & interview',
    description: 'Rank applicants, schedule slots, and run AI interviews end to end.',
  },
]

const recruiterFlow = [
  'Open a recruitment request with salary and role details',
  'Review applications and move candidates through the pipeline',
  'Rank matches and shortlist the strongest applicants',
  'Schedule interviews and run live AI sessions',
  'Read evaluation reports and track analytics',
]

const candidateFlow = [
  'Upload your resume and browse open roles',
  'Check your match score before you apply',
  'Submit an application with contact details',
  'Prepare with personalised practice questions',
  'Join the AI interview and review feedback',
]

export function LandingPage() {
  const token = getToken()
  const user = getStoredUser()
  const isLoggedIn = Boolean(token && user)
  const portalPath =
    user?.role === 'RECRUITER' ? '/recruiter/jobs' : user?.role === 'CANDIDATE' ? '/candidate/applications' : '/'
  const portalLabel = user?.role === 'RECRUITER' ? 'Go to Hiring Board' : 'Go to Applications'

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="animate-soft-float absolute -left-24 top-10 h-80 w-80 rounded-full bg-teal-200/40 blur-3xl" />
        <div
          className="animate-soft-float absolute -right-16 top-40 h-96 w-96 rounded-full bg-sky-200/40 blur-3xl"
          style={{ animationDelay: '1.2s' }}
        />
      </div>

      <header className="relative border-b border-border/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="font-display text-xl font-bold text-ink">IntelliInterview</h1>
            <p className="text-xs text-muted">Ready-to-use hiring for software roles</p>
          </div>
          <div className="flex gap-3">
            {isLoggedIn ? (
              <>
                <span className="hidden items-center text-sm text-muted sm:inline-flex">
                  Signed in as {user?.full_name || user?.email}
                </span>
                <Link to={portalPath} className="btn-primary !py-2">
                  {portalLabel}
                </Link>
              </>
            ) : (
              <>
                <Link to="/recruiter/login" className="btn-secondary !py-2">
                  Recruiter login
                </Link>
                <Link to="/candidate/login" className="btn-primary !py-2">
                  Candidate login
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-6xl px-6 py-16">
        <section className="animate-fade-up mb-20 max-w-3xl">
          <Badge variant="info">End-to-end recruiting</Badge>
          <h2 className="mt-4 font-display text-4xl font-extrabold leading-tight tracking-tight text-ink sm:text-5xl">
            From open role to hired - in one clear flow
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted">
            Post jobs with real salary bands, let candidates apply with a resume match, then shortlist,
            schedule, interview, and evaluate without leaving the platform.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            {isLoggedIn ? (
              <Link to={portalPath} className="btn-primary">
                Continue to your portal
              </Link>
            ) : (
              <>
                <Link to="/recruiter/login" className="btn-primary">
                  Start hiring
                </Link>
                <Link to="/candidate/login" className="btn-secondary">
                  Find roles & apply
                </Link>
              </>
            )}
          </div>
        </section>

        <section className="mb-20 grid gap-6 md:grid-cols-3">
          {flowSteps.map((step, index) => (
            <Card key={step.step} hover className={`animate-fade-up-delay-${Math.min(index + 1, 3)}`}>
              <p className="font-display text-sm font-bold text-teal-700">{step.step}</p>
              <h3 className="mt-2 text-lg font-bold text-ink">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{step.description}</p>
            </Card>
          ))}
        </section>

        <section className="mb-16 grid gap-6 lg:grid-cols-2">
          <Card className="border-teal-200 bg-gradient-to-br from-white to-teal-50/80">
            <p className="text-sm font-semibold text-teal-700">Recruiter flow</p>
            <h4 className="mt-1 font-display text-lg font-bold text-ink">Hiring Board first</h4>
            <ul className="mt-4 space-y-2">
              {recruiterFlow.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-muted">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                  {item}
                </li>
              ))}
            </ul>
            <Link
              to={isLoggedIn && user?.role === 'RECRUITER' ? '/recruiter/jobs' : '/recruiter/login'}
              className="mt-5 inline-block text-sm font-semibold text-teal-700 hover:text-teal-800"
            >
              {isLoggedIn && user?.role === 'RECRUITER' ? 'Open Hiring Board →' : 'Enter recruiter portal →'}
            </Link>
          </Card>

          <Card className="border-sky-200 bg-gradient-to-br from-white to-sky-50/80">
            <p className="text-sm font-semibold text-sky-700">Candidate flow</p>
            <h4 className="mt-1 font-display text-lg font-bold text-ink">Applications first</h4>
            <ul className="mt-4 space-y-2">
              {candidateFlow.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-muted">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-500" />
                  {item}
                </li>
              ))}
            </ul>
            <Link
              to={
                isLoggedIn && user?.role === 'CANDIDATE' ? '/candidate/applications' : '/candidate/login'
              }
              className="mt-5 inline-block text-sm font-semibold text-sky-700 hover:text-sky-800"
            >
              {isLoggedIn && user?.role === 'CANDIDATE'
                ? 'Open Applications →'
                : 'Enter candidate portal →'}
            </Link>
          </Card>
        </section>
      </main>

      <footer className="relative border-t border-border py-8 text-center text-xs text-muted">
        IntelliInterview · University of Leicester
      </footer>
    </div>
  )
}
