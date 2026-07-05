import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function CandidateRankingPage() {
  return (
    <div>
      <PageHeader
        title="Candidate Ranking & Match Scoring"
        description="Automatically score applicants against a job description with a plain-language match breakdown to support shortlisting before scheduling an interview."
      />

      <PlaceholderPanel
        title="Ranked candidate list"
        description="Sorted by match score with expandable breakdown per applicant."
        items={[
          { label: 'Candidate row', hint: 'Match % ,  Strong ,  Partial ,  Gap summary' },
          { label: 'Candidate row', hint: 'Match % ,  Strong ,  Partial ,  Gap summary' },
          { label: 'Candidate row', hint: 'Match % ,  Strong ,  Partial ,  Gap summary' },
        ]}
        columns={1}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Match score breakdown"
          description="Plain-language explanation of why a candidate ranks at a given position."
          columns={1}
        />
        <PlaceholderPanel
          title="Shortlist actions"
          description="Move top candidates to interview scheduling pipeline."
          columns={1}
        />
      </div>
    </div>
  )
}
