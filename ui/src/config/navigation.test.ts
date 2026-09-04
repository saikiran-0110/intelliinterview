import { describe, expect, it } from 'vitest'
import { candidateNav, recruiterNav } from './navigation'

describe('navigation config', () => {
  it('lists recruiter destinations in hiring order', () => {
    expect(recruiterNav[0]).toMatchObject({ label: 'Hiring Board', path: '/recruiter/jobs' })
    expect(recruiterNav.map((item) => item.path)).toEqual([
      '/recruiter/jobs',
      '/recruiter/ranking',
      '/recruiter/questions',
      '/recruiter/sessions',
      '/recruiter/scheduling',
      '/recruiter/reports',
      '/recruiter/analytics',
      '/recruiter/bias',
      '/recruiter/assistant',
      '/recruiter/profile',
    ])
  })

  it('lists candidate destinations with applications first', () => {
    expect(candidateNav[0]).toMatchObject({ label: 'Applications', path: '/candidate/applications' })
    expect(candidateNav.map((item) => item.path)).toContain('/candidate/interview')
    expect(candidateNav.every((item) => item.label && item.path)).toBe(true)
  })
})
