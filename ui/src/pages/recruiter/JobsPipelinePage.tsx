import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

const pipelineStages = ['Applied', 'Screening', 'Shortlisted', 'Interview', 'Offer', 'Hired']

export function JobsPipelinePage() {
  return (
    <div>
      <PageHeader
        title="Jobs & Hiring Pipeline"
        description="Post job roles, view received applications, update candidate stages, and download CVs from a single interface."
        action={
          <button
            type="button"
            disabled
            className="rounded-xl border border-border px-4 py-2 text-sm font-medium text-slate-500"
          >
            Post new role
          </button>
        }
      />

      <PlaceholderPanel
        title="Open job roles"
        description="Active postings with application counts and pipeline summary."
        items={[
          { label: 'Role card', hint: 'Title ,  Applications ,  Stage counts' },
          { label: 'Role card', hint: 'Title ,  Applications ,  Stage counts' },
        ]}
        columns={2}
      />

      <div className="mt-6">
        <PlaceholderPanel
          title="Hiring pipeline board"
          description="Kanban-style view to move candidates between stages."
          items={pipelineStages.map((stage) => ({
            label: stage,
            hint: 'Candidate cards ,  Drag to move',
          }))}
          columns={3}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Applications inbox"
          description="Recent applications with CV download and quick actions."
          columns={1}
        />
        <PlaceholderPanel
          title="Post a job role"
          description="Form for title, description, requirements, and visibility."
          columns={1}
        />
      </div>
    </div>
  )
}
