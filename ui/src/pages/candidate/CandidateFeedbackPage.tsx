import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function CandidateFeedbackPage() {
  return (
    <div>
      <PageHeader
        title="Interview Feedback"
        description="AI-written summary delivered after your interview - highlighting strong answers, areas to improve, and focus points for future interviews."
      />

      <div className="mb-6 rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5">
        <p className="text-sm text-slate-400">
          Feedback is generated from your actual session responses, not generic advice. Available after
          the recruiter completes the evaluation workflow.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Strong answers"
          description="What you did well during the interview."
          columns={1}
        />
        <PlaceholderPanel
          title="Areas to improve"
          description="Specific topics and skills to focus on."
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Preparation recommendations"
          description="Actionable guidance before your next interview."
          columns={1}
        />
      </div>
    </div>
  )
}
