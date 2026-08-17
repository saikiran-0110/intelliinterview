import { type FormEvent, useState } from 'react'
import { getStoredUser, setAuth, type StoredUser } from '../../api/client'
import { updateProfile } from '../../api/optional'
import type { AuthResponse } from '../../types/analysis'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'

export function RecruiterProfilePage() {
  const [user, setUser] = useState<StoredUser | null>(getStoredUser())
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [phone, setPhone] = useState(user?.phone || '')
  const [company, setCompany] = useState(user?.company || '')
  const [jobTitle, setJobTitle] = useState(user?.job_title || '')
  const [location, setLocation] = useState(user?.location || '')
  const [linkedin, setLinkedin] = useState(user?.linkedin_url || '')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  async function handleProfile(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const updated = (await updateProfile({
        full_name: fullName,
        phone: phone || undefined,
        company: company || undefined,
        job_title: jobTitle || undefined,
        location: location || undefined,
        linkedin_url: linkedin || undefined,
      })) as AuthResponse
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
      })
      setUser(getStoredUser())
      setStatus('Profile updated.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
    }
  }

  return (
    <div>
      <PageHeader
        title="My Profile"
        description="Manage your recruiter account, company details, and contact information."
      />
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-800">{status}</p>}

      <Card className="animate-fade-up max-w-2xl">
        <h3 className="text-lg font-semibold text-ink">Recruiter details</h3>
        <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={handleProfile}>
          <p className="sm:col-span-2 text-sm text-muted">{user?.email}</p>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field" required placeholder="Full name" />
          <input value={phone} onChange={(e) => setPhone(e.target.value)} className="input-field" placeholder="Phone" />
          <input value={company} onChange={(e) => setCompany(e.target.value)} className="input-field" placeholder="Company" />
          <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="input-field" placeholder="Job title" />
          <input value={location} onChange={(e) => setLocation(e.target.value)} className="input-field" placeholder="Location" />
          <input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} className="input-field" placeholder="LinkedIn URL" />
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary">
              Save profile
            </button>
          </div>
        </form>
      </Card>
    </div>
  )
}
