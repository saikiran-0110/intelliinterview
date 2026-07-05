import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function PreparationPage() {
  return (
    <div>
      <PageHeader
        title="Interview Preparation"
        description="Personalised practice questions and brief preparation guidance based on your CV and the target job description."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Practice questions"
          description="AI-generated questions tailored to your profile and the role."
          items={[
            { label: 'Technical question', hint: 'Based on CV gap area' },
            { label: 'Experience question', hint: 'Based on job requirements' },
            { label: 'Scenario question', hint: 'Problem-solving practice' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Preparation guidance"
          description="Brief tips on topics to review before your scheduled session."
          items={[
            { label: 'Key topics to revise', hint: 'From gap analysis' },
            { label: 'Suggested reading', hint: 'Technologies ,  Concepts' },
          ]}
          columns={1}
        />
      </div>
    </div>
  )
}
