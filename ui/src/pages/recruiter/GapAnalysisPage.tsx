import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function GapAnalysisPage() {
  return (
    <div>
      <PageHeader
        title="Gap Analysis"
        description="Structured comparison of candidate skills and experience against the selected job specification - showing strong matches, partial matches, and gaps."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        {['Strong match', 'Partial match', 'Gap identified'].map((label) => (
          <div key={label} className="rounded-2xl border border-border bg-surface-raised p-5 text-center">
            <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold text-slate-600">-</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Skills comparison"
          description="Programming languages, frameworks, and tools mapped to role requirements."
          items={[
            { label: 'Matched skills', hint: 'e.g. React, Python, PostgreSQL' },
            { label: 'Partially matched', hint: 'Related but not exact fit' },
            { label: 'Missing skills', hint: 'Required but not evidenced in CV' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Experience & qualifications"
          description="Years of experience, education, and project relevance."
          items={[
            { label: 'Experience alignment', hint: 'Seniority ,  Domain fit' },
            { label: 'Qualification check', hint: 'Degrees ,  Certifications' },
            { label: 'Evidence passages', hint: 'RAG-linked CV excerpts' },
          ]}
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Plain-language summary"
          description="Narrative gap analysis output for recruiter review before question planning."
          columns={1}
        />
      </div>
    </div>
  )
}
