export type NavItem = {
  label: string
  path: string
  description?: string
}

/** Recruiter hiring flow — schedule right after ranking; assistant near profile */
export const recruiterNav: NavItem[] = [
  { label: 'Hiring Board', path: '/recruiter/jobs', description: 'Open roles and manage applicants' },
  { label: 'Candidate Ranking', path: '/recruiter/ranking', description: 'Match scores and shortlisting' },
  { label: 'Scheduling', path: '/recruiter/scheduling', description: 'Propose and confirm interview slots' },
  { label: 'Interview Sessions', path: '/recruiter/sessions', description: 'Run live AI interviews' },
  { label: 'Question Planning', path: '/recruiter/questions', description: 'Review interview questions' },
  { label: 'Evaluation Reports', path: '/recruiter/reports', description: 'Post-interview assessments' },
  { label: 'Analytics', path: '/recruiter/analytics', description: 'Pipeline and hiring insights' },
  { label: 'Bias Detection', path: '/recruiter/bias', description: 'Fairness monitoring' },
  { label: 'AI Assistant', path: '/recruiter/assistant', description: 'Quick answers about your pipeline' },
  { label: 'My Profile', path: '/recruiter/profile', description: 'Account and company details' },
]

/** Candidate journey - Applications first */
export const candidateNav: NavItem[] = [
  { label: 'Applications', path: '/candidate/applications', description: 'Browse roles, match and apply' },
  { label: 'My Profile', path: '/candidate/profile', description: 'Resume and account details' },
  { label: 'Preparation', path: '/candidate/preparation', description: 'Practice before your interview' },
  { label: 'My Sessions', path: '/candidate/sessions', description: 'Upcoming and past interviews' },
  { label: 'Live Interview', path: '/candidate/interview', description: 'Join your AI interview room' },
  { label: 'Interview Feedback', path: '/candidate/feedback', description: 'Post-interview summary' },
]
