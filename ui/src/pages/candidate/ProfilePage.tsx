import { type FormEvent, useEffect, useState } from 'react'
import { getStoredUser, setAuth, type StoredUser } from '../../api/client'
import { listMyCvs, updateProfile, uploadMyCv } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv } from '../../types/analysis'

export function ProfilePage() {
  const [user, setUser] = useState<StoredUser | null>(getStoredUser())
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  async function load() {
    try {
      const items = await listMyCvs()
      setCvs(items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile data')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleProfile(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const updated = (await updateProfile(fullName)) as StoredUser & { token: string }
      setAuth(updated.token, {
        user_id: updated.user_id,
        email: updated.email,
        full_name: updated.full_name,
        role: updated.role,
      })
      setUser(getStoredUser())
      setStatus('Profile updated.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!file) return
    setError(null)
    try {
      await uploadMyCv(file, fullName || user?.full_name)
      setFile(null)
      setStatus('CV uploaded.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload CV')
    }
  }

  return (
    <div>
      <PageHeader
        title="My Profile"
        description="Manage your account details and upload your CV for applications and interview preparation."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-violet-300">{status}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-white">Account</h3>
          <form className="mt-4 space-y-3" onSubmit={handleProfile}>
            <p className="text-sm text-slate-400">{user?.email}</p>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
              required
            />
            <button type="submit" className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white">
              Save name
            </button>
          </form>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white">Upload CV</h3>
          <form className="mt-4 space-y-3" onSubmit={handleUpload}>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-slate-300"
              required
            />
            <button
              type="submit"
              disabled={!file}
              className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              Upload CV
            </button>
          </form>
          <div className="mt-4 space-y-2">
            {cvs.map((cv) => (
              <div key={cv.id} className="rounded-lg border border-border px-3 py-2 text-xs text-slate-400">
                {cv.original_filename} · {new Date(cv.created_at).toLocaleString()}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
