import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function QuestionPlanningPage() {
  return (
    <div>
      <PageHeader
        title="Interview Question Planning"
        description="Generate tailored technical questions from gap analysis, then add recruiter custom questions to build a combined session plan."
        action={
          <button
            type="button"
            disabled
            className="rounded-xl border border-border px-4 py-2 text-sm font-medium text-slate-500"
          >
            Generate AI questions
          </button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="AI-generated questions"
          description="GPT-4o questions based on CV gaps and job-spec requirements."
          items={[
            { label: 'Technical depth question', hint: 'Source: AI ,  Topic from gap' },
            { label: 'Experience probe', hint: 'Source: AI ,  CV evidence' },
            { label: 'Problem-solving scenario', hint: 'Source: AI ,  Role-specific' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Recruiter custom questions"
          description="Add, reorder, and approve your own questions alongside AI suggestions."
          items={[
            { label: 'Add custom question', hint: 'Source: Recruiter' },
            { label: 'Question list editor', hint: 'Drag to reorder ,  Approve state' },
          ]}
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Combined session plan"
          description="Final ordered question set with source tags (AI / Recruiter) for the interview agent."
          items={[
            { label: 'Question 1', hint: 'AI ,  Approved' },
            { label: 'Question 2', hint: 'Recruiter ,  Approved' },
            { label: 'Question 3', hint: 'AI ,  Pending review' },
          ]}
          columns={3}
        />
      </div>
    </div>
  )
}
