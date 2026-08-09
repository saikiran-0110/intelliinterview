import { useEffect, useState } from 'react'
import { generatePreparation, listMyCvs, listOpenJobs, listPreparation } from '../../api/optional'
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
  const [error, setError] = useState<string | null>(null)

  async function load() {
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
      if (!active && myPacks[0]) setActive(myPacks[0])
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
    try {
      const pack = await generatePreparation(selectedJobId, selectedCvId || undefined)
      setActive(pack)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preparation pack')
    }
  }

  return (
    <div>
      <PageHeader
        title="Interview Preparation"
        description="Generate personalised practice questions and guidance from the job description and your CV before the AI interview."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}

      <Card className="mb-6">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs text-slate-500">Target role</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
            >
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
              className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
            >
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
          className="mt-4 rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white"
        >
          Generate practice pack
        </button>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-white">Saved packs</h3>
          <div className="mt-3 space-y-2">
            {packs.map((pack) => (
              <button
                key={pack.id}
                type="button"
                onClick={() => setActive(pack)}
                className="block w-full rounded-xl border border-border p-3 text-left text-sm text-slate-300"
              >
                {pack.job_title}
              </button>
            ))}
          </div>
        </Card>

        {active && (
          <div className="space-y-4 lg:col-span-2">
            <Card>
              <h3 className="text-lg font-semibold text-white">{active.job_title}</h3>
              <p className="mt-3 text-sm text-slate-300">{active.guidance}</p>
              <p className="mt-3 text-xs text-slate-500">
                Focus areas: {active.focus_areas.join(', ') || 'n/a'}
              </p>
            </Card>
            <Card>
              <h4 className="text-sm font-semibold text-violet-300">Practice questions</h4>
              <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-300">
                {active.practice_questions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ol>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
