import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function AiAssistantPage() {
  return (
    <div>
      <PageHeader
        title="AI Recruiter Assistant"
        description="Embedded chatbot that understands natural language queries - find best candidates for a role, summarise CVs, and return structured answers via a LangChain agent."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PlaceholderPanel
            title="Chat interface"
            description="Ask questions in natural language about candidates and roles."
            items={[
              { label: 'Message: "Find top candidates for Senior React role"', hint: 'User query' },
              { label: 'Structured response with candidate list', hint: 'Agent output' },
              { label: 'Message: "Summarise this CV"', hint: 'User query' },
            ]}
            columns={1}
          />
        </div>
        <PlaceholderPanel
          title="Suggested queries"
          description="Quick-start prompts for common recruiter tasks."
          items={[
            { label: 'Best match for role X', hint: 'Ranking query' },
            { label: 'CV summary', hint: 'Document query' },
            { label: 'Pipeline status', hint: 'Analytics query' },
          ]}
          columns={1}
        />
      </div>
    </div>
  )
}
