import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function NewSessionPage() {
  return (
    <div>
      <PageHeader
        title="Create Interview Session"
        description="Link a candidate CV, job specification, and approved question plan to launch an AI interview session."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Session configuration"
          items={[
            { label: 'Select candidate CV', hint: 'From uploaded documents' },
            { label: 'Select job specification', hint: 'Target role' },
            { label: 'Select question plan', hint: 'AI + recruiter combined' },
            { label: 'Assign candidate user', hint: 'Portal access' },
          ]}
        />
        <PlaceholderPanel
          title="Session options"
          items={[
            { label: 'Enable text-to-speech', hint: 'Question delivery via TTS' },
            { label: 'Allow speech-to-text', hint: 'Voice answers with review' },
            { label: 'Follow-up limit', hint: 'Max follow-ups per question' },
            { label: 'Schedule date/time', hint: 'Links to scheduling module' },
          ]}
        />
      </div>

      <div className="mt-6 flex gap-3">
        <button
          type="button"
          disabled
          className="rounded-xl bg-teal-500/50 px-6 py-2.5 text-sm font-semibold text-slate-950"
        >
          Create session
        </button>
        <button
          type="button"
          disabled
          className="rounded-xl border border-border px-6 py-2.5 text-sm font-medium text-slate-500"
        >
          Save as draft
        </button>
      </div>
    </div>
  )
}
