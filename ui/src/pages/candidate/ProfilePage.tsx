import { type FormEvent, useEffect, useState } from 'react'
import { getStoredUser, setAuth, type StoredUser } from '../../api/client'
import {
  deleteMyPhoto,
  getUserPhotoBlob,
  listMyCvs,
  updateProfile,
  uploadMyCv,
  uploadMyPhoto,
  deleteMyCv,
} from '../../api/optional'
import type { AuthResponse } from '../../types/analysis'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv } from '../../types/analysis'

export function ProfilePage() {
  const [user, setUser] = useState<StoredUser | null>(getStoredUser())
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [phone, setPhone] = useState(user?.phone || '')
  const [jobTitle, setJobTitle] = useState(user?.job_title || '')
  const [location, setLocation] = useState(user?.location || '')
  const [linkedin, setLinkedin] = useState(user?.linkedin_url || '')
  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
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

  useEffect(() => {
    if (!user?.has_profile_photo || !user.user_id) {
      setPhotoUrl(null)
      return
    }
    let objectUrl: string | null = null
    getUserPhotoBlob(user.user_id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        setPhotoUrl(objectUrl)
      })
      .catch(() => setPhotoUrl(null))
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [user?.has_profile_photo, user?.user_id])

  function applyAuthResponse(updated: AuthResponse) {
    setAuth(updated.token, {
      user_id: updated.user_id,
      email: updated.email,
      full_name: updated.full_name,
      role: updated.role,
      phone: updated.phone,
      company: updated.company,
      job_title: updated.job_title,
      location: updated.location,
      linkedin_url: updated.linkedin_url,
      email_verified: updated.email_verified,
      has_profile_photo: updated.has_profile_photo,
    })
    setUser(getStoredUser())
  }

  async function handleProfile(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const updated = (await updateProfile({
        full_name: fullName,
        phone: phone || undefined,
        job_title: jobTitle || undefined,
        location: location || undefined,
        linkedin_url: linkedin || undefined,
      })) as AuthResponse
      applyAuthResponse(updated)
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
      setStatus('Resume uploaded.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume')
    }
  }

  async function handleDeleteCv(cvId: string) {
    setError(null)
    setStatus(null)
    try {
      await deleteMyCv(cvId)
      setStatus('Resume removed.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove resume')
    }
  }

  async function handlePhotoUpload(event: FormEvent) {
    event.preventDefault()
    if (!photoFile) return
    setError(null)
    setStatus(null)
    try {
      const updated = (await uploadMyPhoto(photoFile)) as AuthResponse
      applyAuthResponse(updated)
      setPhotoFile(null)
      setStatus('Profile picture updated.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload profile picture')
    }
  }

  async function handlePhotoDelete() {
    setError(null)
    setStatus(null)
    try {
      const updated = (await deleteMyPhoto()) as AuthResponse
      applyAuthResponse(updated)
      setStatus('Profile picture removed.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove profile picture')
    }
  }

  return (
    <div>
      <PageHeader
        title="My Profile"
        description="Keep your contact details current and upload the resume used for matching and applications."
      />
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-800">{status}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="animate-fade-up">
          <h3 className="text-lg font-semibold text-ink">Profile picture</h3>
          <p className="mt-1 text-xs text-muted">
            Used by recruiters to visually verify your identity against your interview recording.
          </p>
          <div className="mt-4 flex items-center gap-4">
            {photoUrl ? (
              <img
                src={photoUrl}
                alt="Profile"
                className="h-20 w-20 shrink-0 rounded-full border border-border object-cover"
              />
            ) : (
              <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-xs text-muted">
                No photo
              </div>
            )}
            <form className="flex min-w-0 flex-1 flex-col gap-2" onSubmit={handlePhotoUpload}>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setPhotoFile(e.target.files?.[0] || null)}
                className="w-full text-sm text-muted"
              />
              <div className="flex gap-3">
                <button type="submit" disabled={!photoFile} className="btn-primary disabled:opacity-50">
                  Upload photo
                </button>
                {user?.has_profile_photo && (
                  <button type="button" onClick={handlePhotoDelete} className="text-sm font-semibold text-rose-600">
                    Remove
                  </button>
                )}
              </div>
            </form>
          </div>
        </Card>

        <Card className="animate-fade-up">
          <h3 className="text-lg font-semibold text-ink">Account details</h3>
          <form className="mt-4 space-y-3" onSubmit={handleProfile}>
            <p className="text-sm text-muted">{user?.email}</p>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field" required placeholder="Full name" />
            <input value={phone} onChange={(e) => setPhone(e.target.value)} className="input-field" placeholder="Phone" />
            <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="input-field" placeholder="Target role / title" />
            <input value={location} onChange={(e) => setLocation(e.target.value)} className="input-field" placeholder="Location" />
            <input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} className="input-field" placeholder="LinkedIn URL" />
            <button type="submit" className="btn-primary">
              Save profile
            </button>
          </form>
        </Card>

        <Card className="animate-fade-up-delay-1">
          <h3 className="text-lg font-semibold text-ink">Resume</h3>
          <form className="mt-4 space-y-3" onSubmit={handleUpload}>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-muted"
              required
            />
            <button type="submit" disabled={!file} className="btn-primary disabled:opacity-50">
              Upload resume
            </button>
          </form>
          <div className="mt-4 space-y-2">
            {cvs.length === 0 && <p className="text-sm text-muted">No resumes uploaded yet.</p>}
            {cvs.map((cv) => (
              <div
                key={cv.id}
                className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-teal-200 bg-teal-50/50 px-3 py-2 text-xs text-muted"
              >
                <span className="min-w-0 truncate">
                  {cv.original_filename} · {new Date(cv.created_at).toLocaleString()}
                </span>
                <button
                  type="button"
                  onClick={() => handleDeleteCv(cv.id)}
                  className="min-h-11 shrink-0 font-semibold text-rose-600"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
