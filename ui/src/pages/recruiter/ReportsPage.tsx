import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listReports } from '../../api/reports'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { InterviewReportSummary } from '../../types/reports'

function recommendationLabel(value: string) {
  return value.replaceAll('_', ' ')
}

export function ReportsPage() {
  const [reports, setReports] = useState<InterviewReportSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const items = await listReports()
        setReports(items)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div>
      <PageHeader
        title="Evaluation Reports"
        description="Detailed post-interview assessments covering technical fit, communication, problem-solving, and role alignment with evidence-linked observations."
      />

      {loading && <p className="text-sm text-slate-400">Loading reports...</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}

      {!loading && reports.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">
            No reports yet. Complete an AI interview session to generate an evaluation report.
          </p>
          <Link to="/recruiter/sessions" className="mt-3 inline-block text-sm font-semibold text-teal-300">
            Go to interview sessions
          </Link>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reports.map((report) => (
            <Card key={report.id} hover>
              <p className="text-xs uppercase tracking-wider text-slate-500">{report.job_title}</p>
              <h3 className="mt-1 text-lg font-semibold text-white">{report.candidate_name}</h3>
              <p className="mt-2 text-sm text-slate-400">
                Overall {report.overall_score}/10 - {recommendationLabel(report.recommendation)}
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-400">
                <span>Tech {report.technical_fit_score}</span>
                <span>Comm {report.communication_score}</span>
                <span>Solve {report.problem_solving_score}</span>
                <span>Align {report.role_alignment_score}</span>
              </div>
              <Link
                to={`/recruiter/reports/${report.id}`}
                className="mt-4 inline-block text-sm font-semibold text-teal-300 hover:text-teal-200"
              >
                View full report
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
