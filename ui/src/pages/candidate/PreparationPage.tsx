import { useEffect, useState } from 'react'
import {
  deletePreparationPack,
  generatePreparation,
  listMyCvs,
  listOpenJobs,
  listPreparation,
  updatePreparationProgress,
} from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv } from '../../types/analysis'
import type { OpenJob, PreparationPack } from '../../types/optional'

export function PreparationPage() {
  const [jobs, setJobs] = useState<OpenJob[]>([])
  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [packs, setPacks] = useState<PreparationPack[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [selectedCvId, setSelectedCvId] = useState('')
  const [active, setActive] = useState<PreparationPack | null>(null)
  const [expandedModule, setExpandedModule] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  async function load(preferredPackId?: string) {
    try {
      const [openJobs, myCvs, myPacks] = await Promise.all([
        listOpenJobs(),
        listMyCvs(),
        listPreparation(),
      ])
      setJobs(openJobs)
      setCvs(myCvs)
      setPacks(myPacks)
      if (!selectedJobId && openJobs[0]) setSelectedJobId(openJobs[0].id)
      if (!selectedCvId && myCvs[0]) setSelectedCvId(myCvs[0].id)
      const preferred =
        (preferredPackId && myPacks.find((pack) => pack.id === preferredPackId)) ||
        myPacks.find((pack) => pack.id === active?.id) ||
        myPacks[0] ||
        null
      setActive(preferred)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preparation data')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleGenerate() {
    if (!selectedJobId) return
    setError(null)
    setStatus(null)
    setGenerating(true)
    try {
      const pack = await generatePreparation(selectedJobId, selectedCvId || undefined)
      setActive(pack)
      setStatus('Advanced preparation pack generated. Track progress as you study.')
      await load(pack.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preparation pack')
    } finally {
      setGenerating(false)
    }
  }

  async function handleToggle(itemId: string, completed: boolean) {
    if (!active) return
    setError(null)
    try {
      const updated = await updatePreparationProgress(active.id, itemId, completed)
      setActive(updated)
      setPacks((current) => current.map((pack) => (pack.id === updated.id ? updated : pack)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update progress')
    }
  }

  async function handleDelete(packId: string) {
    setError(null)
    setStatus(null)
    try {
      await deletePreparationPack(packId)
      setStatus('Preparation pack deleted.')
      if (active?.id === packId) setActive(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete preparation pack')
    }
  }

  const completed = new Set(active?.completed_item_ids || [])

  return (
    <div>
      <PageHeader
        title="Interview Preparation"
        description="Generate an advanced study plan with technical deep-dives, practice drills, and a progress checklist tailored to the role and your CV."
      />
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && <p className="mb-4 text-sm text-sky-700">{status}</p>}

      <Card className="mb-6">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs text-slate-500">Target role</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="mt-2 input-field"
            >
              {jobs.length === 0 && <option value="">No open roles</option>}
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500">CV</label>
            <select
              value={selectedCvId}
              onChange={(e) => setSelectedCvId(e.target.value)}
              className="mt-2 input-field"
            >
              {cvs.length === 0 && <option value="">Upload a resume first</option>}
              {cvs.map((cv) => (
                <option key={cv.id} value={cv.id}>
                  {cv.original_filename}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={!selectedJobId || !selectedCvId || generating}
          className="mt-4 min-h-11 w-full rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-ink disabled:opacity-50 sm:w-auto"
        >
          {generating ? 'Generating advanced pack…' : 'Generate advanced practice pack'}
        </button>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-ink">Saved packs</h3>
          <div className="mt-3 space-y-2">
            {packs.length === 0 && (
              <p className="text-sm text-muted">No saved packs yet. Generate one to start preparing.</p>
            )}
            {packs.map((pack) => (
              <div
                key={pack.id}
                className={`rounded-xl border p-3 ${
                  active?.id === pack.id ? 'border-sky-300 bg-sky-50/70' : 'border-border'
                }`}
              >
                <button
                  type="button"
                  onClick={() => setActive(pack)}
                  className="block w-full text-left"
                >
                  <p className="text-sm font-semibold text-ink">{pack.job_title}</p>
                  <p className="mt-1 text-xs text-muted">
                    {pack.progress_percent}% complete · {new Date(pack.created_at).toLocaleDateString()}
                  </p>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-sky-500"
                      style={{ width: `${pack.progress_percent}%` }}
                    />
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(pack.id)}
                  className="mt-2 text-xs font-semibold text-rose-600"
                >
                  Delete pack
                </button>
              </div>
            ))}
          </div>
        </Card>

        {active && (
          <div className="space-y-4 lg:col-span-2">
            <Card>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-ink">{active.job_title}</h3>
                  <p className="mt-1 text-xs text-muted">
                    Focus: {active.focus_areas.join(', ') || 'n/a'} · {active.progress_percent}% complete
                  </p>
                </div>
                <span className="rounded-lg bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-800">
                  {active.model_version || 'baseline'}
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-700">{active.guidance}</p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-teal-500 transition-all"
                  style={{ width: `${active.progress_percent}%` }}
                />
              </div>
            </Card>

            <Card>
              <h4 className="text-sm font-semibold text-sky-700">Preparation checklist</h4>
              <p className="mt-1 text-xs text-muted">Mark tasks complete as you finish each preparation part.</p>
              <div className="mt-3 space-y-2">
                {(active.checklist_items || []).map((item) => {
                  const done = completed.has(item.id)
                  return (
                    <label
                      key={item.id}
                      className="flex cursor-pointer gap-3 rounded-xl border border-border bg-surface/50 p-3"
                    >
                      <input
                        type="checkbox"
                        checked={done}
                        onChange={(e) => handleToggle(item.id, e.target.checked)}
                        className="mt-1"
                      />
                      <span className="flex-1">
                        <span className={`block text-sm ${done ? 'text-slate-400 line-through' : 'text-ink'}`}>
                          {item.label}
                        </span>
                        <span className="mt-1 block text-xs text-muted">
                          {item.category}
                          {item.technical_hint ? ` · ${item.technical_hint}` : ''}
                        </span>
                      </span>
                    </label>
                  )
                })}
              </div>
            </Card>

            <Card>
              <h4 className="text-sm font-semibold text-sky-700">Technical study modules</h4>
              <div className="mt-3 space-y-2">
                {(active.study_modules || []).map((module) => {
                  const done = completed.has(module.id)
                  const open = expandedModule === module.id
                  return (
                    <div key={module.id} className="rounded-xl border border-border p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <button
                          type="button"
                          onClick={() => setExpandedModule(open ? null : module.id)}
                          className="flex-1 text-left"
                        >
                          <p className={`text-sm font-semibold ${done ? 'text-slate-400' : 'text-ink'}`}>
                            {module.title}
                          </p>
                          <p className="mt-1 text-xs text-muted">
                            {module.topic} · ~{module.estimated_minutes} min · {open ? 'Hide details' : 'Show technical details'}
                          </p>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggle(module.id, !done)}
                          className="rounded-lg border border-border px-2.5 py-1 text-xs font-semibold text-sky-700"
                        >
                          {done ? 'Mark incomplete' : 'Mark complete'}
                        </button>
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{module.summary}</p>
                      {open && (
                        <div className="mt-3 rounded-lg border border-sky-100 bg-sky-50/70 p-3 text-sm text-slate-700">
                          <p className="text-xs font-semibold uppercase tracking-wide text-sky-800">
                            Technical details
                          </p>
                          <p className="mt-2 whitespace-pre-wrap">{module.technical_details}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </Card>

            <Card>
              <h4 className="text-sm font-semibold text-sky-700">Practice drills</h4>
              <div className="mt-3 space-y-3">
                {(active.practice_questions || []).map((item, index) => {
                  const done = completed.has(item.id)
                  return (
                    <div key={item.id} className="rounded-xl border border-border p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                            Q{index + 1} · {item.difficulty} · {item.topic}
                          </p>
                          <p className={`mt-1 text-sm font-medium ${done ? 'text-slate-400 line-through' : 'text-ink'}`}>
                            {item.question}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleToggle(item.id, !done)}
                          className="rounded-lg border border-border px-2.5 py-1 text-xs font-semibold text-sky-700"
                        >
                          {done ? 'Undo' : 'Completed'}
                        </button>
                      </div>
                      {item.technical_context && (
                        <p className="mt-2 text-xs text-slate-600">
                          <span className="font-semibold text-sky-800">Technical context: </span>
                          {item.technical_context}
                        </p>
                      )}
                      {item.talking_points?.length > 0 && (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-600">
                          {item.talking_points.map((point) => (
                            <li key={point}>{point}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
