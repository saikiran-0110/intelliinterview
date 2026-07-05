import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function BiasDetectionPage() {
  return (
    <div>
      <PageHeader
        title="Bias Detection"
        description="Monitor shortlisting and interview scoring patterns over time. Alert recruiters when consistent patterns may suggest unfair or unbalanced decision-making."
      />

      <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5">
        <p className="text-sm font-medium text-amber-300">Fairness monitoring</p>
        <p className="mt-1 text-sm text-slate-400">
          Scoring rubrics tied to job requirements only. No demographic inference from CV text.
          AI output is advisory - recruiters review evidence behind each score.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Scoring pattern analysis"
          description="Distribution of scores across candidates and roles over time."
          columns={1}
        />
        <PlaceholderPanel
          title="Shortlisting patterns"
          description="Compare shortlist rates and criteria application consistency."
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Alerts & notifications"
          description="Flagged patterns requiring recruiter review."
          items={[
            { label: 'Alert slot', hint: 'Pattern type ,  Severity ,  Date range' },
            { label: 'Alert slot', hint: 'Recommended action' },
          ]}
          columns={1}
        />
      </div>
    </div>
  )
}
