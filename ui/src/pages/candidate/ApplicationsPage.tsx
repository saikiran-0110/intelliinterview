import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function ApplicationsPage() {
  return (
    <div>
      <PageHeader
        title="Job Applications"
        description="Browse available software engineering roles, apply with your CV, and track application status from your personal dashboard."
        action={
          <button
            type="button"
            disabled
            className="rounded-xl border border-border px-4 py-2 text-sm font-medium text-slate-500"
          >
            Browse open roles
          </button>
        }
      />

      <PlaceholderPanel
        title="Available positions"
        description="Open software engineering roles within the organisation."
        items={[
          { label: 'Role listing', hint: 'Title ,  Team ,  Apply button' },
          { label: 'Role listing', hint: 'Title ,  Team ,  Apply button' },
        ]}
        columns={2}
      />

      <div className="mt-6">
        <PlaceholderPanel
          title="My applications"
          description="Track status of each submitted application."
          items={[
            { label: 'Application row', hint: 'Role ,  Status ,  Date applied' },
            { label: 'Application row', hint: 'Role ,  Status ,  Date applied' },
          ]}
          columns={1}
        />
      </div>
    </div>
  )
}
