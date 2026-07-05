import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function LiveInterviewPage() {
  return (
    <div>
      <PageHeader
        title="Live AI Interview"
        description="AI-conducted session with role-specific questions, follow-ups, and real-time response capture. Supports text input, speech-to-text, and text-to-speech."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-border bg-surface-raised p-6">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">AI Interviewer</p>
              <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs text-emerald-300">
                Session placeholder
              </span>
            </div>
            <div className="min-h-24 rounded-xl border border-dashed border-border bg-surface/60 p-4">
              <p className="text-sm text-slate-400">
                Question area - AI asks prepared role-specific questions with optional TTS playback.
              </p>
            </div>
          </div>

          <PlaceholderPanel
            title="Conversation transcript"
            description="Live chat history of questions, follow-ups, and your responses."
            items={[
              { label: 'AI: Question 1', hint: 'Role-specific technical question' },
              { label: 'You: Response', hint: 'Text or STT transcription' },
              { label: 'AI: Follow-up', hint: 'Bounded adaptive follow-up' },
            ]}
            columns={1}
          />
        </div>

        <div className="space-y-6">
          <PlaceholderPanel
            title="Your response"
            description="Type your answer or use voice input."
            items={[
              { label: 'Text input area', hint: 'Primary response channel' },
              { label: 'Speech-to-text', hint: 'Mic ,  Review transcription before submit' },
            ]}
            columns={1}
          />
          <PlaceholderPanel
            title="Session controls"
            items={[
              { label: 'Text-to-speech toggle', hint: 'Listen to questions' },
              { label: 'Submit answer', hint: 'Send to GPT-4o evaluation' },
              { label: 'Session progress', hint: 'Question 1 of N' },
            ]}
            columns={1}
          />
        </div>
      </div>
    </div>
  )
}
