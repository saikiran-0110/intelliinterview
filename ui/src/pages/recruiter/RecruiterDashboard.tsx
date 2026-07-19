import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listCvs, listJobSpecs } from '../../api/analysis'
import { listReports } from '../../api/reports'
import { listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { StatCard } from '../../components/ui/StatCard'
import type { InterviewReportSummary } from '../../types/reports'
import type { SessionSummary } from '../../types/sessions'

const quickActions = [
  { label: 'Upload CV and job spec', path: '/recruiter/analysis' },
  { label: 'Review gap analysis', path: '/recruiter/gap-analysis' },
  { label: 'Plan interview questions', path: '/recruiter/questions' },
  { label: 'Start new session', path: '/recruiter/sessions/new' },
]

export function RecruiterDashboard() {
  const [openSessions, setOpenSessions] = useState(0)
  const [completedReports, setCompletedReports] = useState(0)
  const [cvCount, setCvCount] = useState(0)
  const [roleCount, setRoleCount] = useState(0)
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [reports, setReports] = useState<InterviewReportSummary[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [sessionItems, reportItems, cvs, jobs] = await Promise.all([
          listSessions(),
          listReports(),
          listCvs(),
          listJobSpecs(),
        ])
        setSessions(sessionItems.slice(0, 5))
        setReports(reportItems.slice(0, 5))
        setOpenSessions(
          sessionItems.filter((item) => item.status === 'SCHEDULED' || item.status === 'IN_PROGRESS').length,
        )
        setCompletedReports(reportItems.length)
        setCvCount(cvs.length)
        setRoleCount(jobs.length)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      }
    }
    load()
  }, [])

  return (
    <div>
      <PageHeader
        title="Recruiter Dashboard"
        description="Upload documents, prepare interviews, launch AI sessions, and review structured evaluation reports from one place."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Open sessions" value={String(openSessions)} tone="brand" />
        <StatCard label="Completed reports" value={String(completedReports)} />
        <StatCard label="CVs analysed" value={String(cvCount)} />
        <StatCard label="Active roles" value={String(roleCount)} tone="accent" />
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((action) => (
          <Link key={action.path} to={action.path}>
            <Card hover className="h-full">
              <p className="text-sm font-semibold text-white">{action.label}</p>
              <p className="mt-2 text-xs text-slate-500">Open page</p>
            </Card>
          </Link>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Recent interview sessions</h3>
            <Link to="/recruiter/sessions" className="text-xs font-semibold text-teal-300">
              View all
            </Link>
          </div>
          {sessions.length === 0 ? (
            <p className="text-sm text-slate-500">No sessions yet.</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session) => (
                <Link
                  key={session.id}
                  to={`/recruiter/sessions/${session.id}`}
                  className="block rounded-xl border border-border bg-surface/60 p-3 hover:border-teal-500/30"
                >
                  <p className="text-sm font-medium text-white">
                    {session.candidate_name} - {session.job_title}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{session.status}</p>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Latest evaluation reports</h3>
            <Link to="/recruiter/reports" className="text-xs font-semibold text-teal-300">
              View all
            </Link>
          </div>
          {reports.length === 0 ? (
            <p className="text-sm text-slate-500">No reports yet.</p>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <Link
                  key={report.id}
                  to={`/recruiter/reports/${report.id}`}
                  className="block rounded-xl border border-border bg-surface/60 p-3 hover:border-teal-500/30"
                >
                  <p className="text-sm font-medium text-white">
                    {report.candidate_name} - {report.job_title}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {report.overall_score}/10 - {report.recommendation.replaceAll('_', ' ')}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
