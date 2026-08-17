import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { startLogin, startRegister, verifyOtp } from '../../api/analysis'
import { setAuth } from '../../api/client'
import { Card } from '../../components/ui/Card'

type LoginPageProps = {
  role: 'recruiter' | 'candidate'
}

type Step = 'details' | 'otp'

export function LoginPage({ role }: LoginPageProps) {
  const navigate = useNavigate()
  const isRecruiter = role === 'recruiter'
  const portalPath = isRecruiter ? '/recruiter/jobs' : '/candidate/applications'
  const apiRole = isRecruiter ? 'RECRUITER' : 'CANDIDATE'

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [step, setStep] = useState<Step>('details')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [company, setCompany] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [location, setLocation] = useState('')
  const [linkedin, setLinkedin] = useState('')
  const [otp, setOtp] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleDetails(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setStatus(null)
    setLoading(true)
    try {
      if (mode === 'register') {
        const response = await startRegister(apiRole, {
          email,
          password,
          full_name: fullName,
          phone,
          company: company || undefined,
          job_title: jobTitle || undefined,
          location: location || undefined,
          linkedin_url: linkedin || undefined,
        })
        setStatus(response.message)
      } else {
        const response = await startLogin(email)
        setStatus(response.message)
      }
      setStep('otp')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start verification')
    } finally {
      setLoading(false)
    }
  }

  async function handleOtp(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const purpose = mode === 'register' ? 'REGISTER' : 'LOGIN'
      const response = await verifyOtp(email, otp, purpose)
      if (isRecruiter && response.role !== 'RECRUITER') {
        throw new Error('This account is not a recruiter account.')
      }
      if (!isRecruiter && response.role !== 'CANDIDATE') {
        throw new Error('This account is not a candidate account.')
      }
      setAuth(response.token, {
        user_id: response.user_id,
        email: response.email,
        full_name: response.full_name,
        role: response.role,
        phone: response.phone,
        company: response.company,
        job_title: response.job_title,
        location: response.location,
        linkedin_url: response.linkedin_url,
        email_verified: response.email_verified,
      })
      navigate(portalPath)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-6 py-12">
      <div className="pointer-events-none absolute inset-0">
        <div
          className={`absolute left-1/2 top-1/3 h-80 w-80 -translate-x-1/2 rounded-full blur-3xl ${
            isRecruiter ? 'bg-teal-300/50' : 'bg-sky-300/50'
          }`}
        />
      </div>

      <Card className="animate-fade-up relative w-full max-w-lg">
        <Link to="/" className="text-xs font-medium text-muted hover:text-teal-800">
          Back to home
        </Link>

        <div className="mt-6">
          <p className={`text-sm font-semibold ${isRecruiter ? 'text-teal-800' : 'text-sky-800'}`}>
            {isRecruiter ? 'Recruiter' : 'Candidate'} access
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink">
            {step === 'otp'
              ? 'Enter verification code'
              : mode === 'login'
                ? 'Sign in with email OTP'
                : 'Create your account'}
          </h1>
          <p className="mt-2 text-sm text-muted">
            {step === 'otp'
              ? 'Enter the one-time code from your email. In development, copy it from the backend console.'
              : isRecruiter
                ? 'Register with company details, then verify by OTP.'
                : 'Register with contact details, then verify by OTP.'}
          </p>
        </div>

        {step === 'details' ? (
          <form className="mt-8 space-y-3" onSubmit={handleDetails}>
            {mode === 'register' && (
              <>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full name"
                  className="input-field"
                  required
                />
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Phone"
                  className="input-field"
                  required
                />
                {isRecruiter && (
                  <input
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="Company"
                    className="input-field"
                    required
                  />
                )}
                <input
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder={isRecruiter ? 'Your job title' : 'Current / target role'}
                  className="input-field"
                />
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Location"
                  className="input-field"
                />
                <input
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                  placeholder="LinkedIn URL (optional)"
                  className="input-field"
                />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password (account recovery)"
                  className="input-field"
                  required
                  minLength={8}
                />
              </>
            )}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="input-field"
              required
            />
            {error && <p className="text-sm text-rose-600">{error}</p>}
            {status && <p className="text-sm text-teal-800">{status}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading ? 'Sending code...' : mode === 'register' ? 'Send registration OTP' : 'Send login OTP'}
            </button>
          </form>
        ) : (
          <form className="mt-8 space-y-3" onSubmit={handleOtp}>
            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="6-digit OTP"
              className="input-field tracking-[0.3em]"
              required
            />
            {error && <p className="text-sm text-rose-600">{error}</p>}
            {status && <p className="text-sm text-teal-800">{status}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading ? 'Verifying...' : 'Verify & continue'}
            </button>
            <button
              type="button"
              className="btn-secondary w-full"
              onClick={() => {
                setStep('details')
                setOtp('')
                setStatus(null)
              }}
            >
              Back
            </button>
          </form>
        )}

        {step === 'details' && (
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError(null)
              setStatus(null)
            }}
            className="mt-4 w-full text-sm text-muted hover:text-ink"
          >
            {mode === 'login'
              ? `Need an account? Register as ${isRecruiter ? 'recruiter' : 'candidate'}`
              : 'Already registered? Sign in with OTP'}
          </button>
        )}
      </Card>
    </div>
  )
}
