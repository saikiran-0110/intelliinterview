import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function CvJobAnalysisPage() {
  return (
    <div>
      <PageHeader
        title="CV & Job Specification Analysis"
        description="Upload candidate CV files (PDF/DOCX) and job specifications. Apache Tika extracts text for skills, experience, and qualifications parsing."
        action={
          <button
            type="button"
            disabled
            className="rounded-xl bg-teal-500/50 px-4 py-2 text-sm font-semibold text-slate-950"
          >
            Upload documents
          </button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Upload candidate CV"
          description="Drag and drop or browse PDF/DOCX files."
          items={[
            { label: 'File drop zone', hint: 'Apache Tika text extraction' },
            { label: 'Extracted fields preview', hint: 'Skills ,  Experience ,  Qualifications' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Select or upload job specification"
          description="Choose an existing role or upload a new job description."
          items={[
            { label: 'Job spec selector', hint: 'Title ,  Description ,  Requirements' },
            { label: 'Parsed requirements', hint: 'Technologies ,  Experience level' },
          ]}
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Document comparison trigger"
          description="Initiates pgvector semantic matching and structured gap analysis."
          items={[
            { label: 'Run analysis button', hint: 'CV vs job-spec comparison' },
            { label: 'Processing status', hint: 'Parsing ,  Embedding ,  Analysis' },
          ]}
        />
      </div>
    </div>
  )
}
