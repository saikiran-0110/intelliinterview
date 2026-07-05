import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

const dimensions = [
  { name: 'Technical fit', score: '-/10' },
  { name: 'Communication', score: '-/10' },
  { name: 'Problem-solving', score: '-/10' },
  { name: 'Role alignment', score: '-/10' },
]

export function ReportDetailPage() {
  return (
    <div>
      <PageHeader
        title="Interview Evaluation Report"
        description="Structured assessment with scores, evidence linked to specific answers, strengths, weaknesses, and a recommendation summary."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {dimensions.map((dim) => (
          <div key={dim.name} className="rounded-2xl border border-border bg-surface-raised p-5">
            <p className="text-xs text-slate-500">{dim.name}</p>
            <p className="mt-1 text-2xl font-bold text-teal-300">{dim.score}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Strengths"
          description="Key positive observations from the interview."
          columns={1}
        />
        <PlaceholderPanel
          title="Areas for improvement"
          description="Weaknesses and development areas identified."
          columns={1}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Evidence by answer"
          description="Observations linked to specific Q&A pairs from the session transcript."
          items={[
            { label: 'Q1 response evidence', hint: 'Quote ,  Observation ,  Score impact' },
            { label: 'Q2 response evidence', hint: 'Quote ,  Observation ,  Score impact' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Recommendation summary"
          description="Concise hiring recommendation for the recruiter."
          columns={1}
        />
      </div>
    </div>
  )
}
