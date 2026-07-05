export type NavItem = {
  label: string
  path: string
  description?: string
}

export const recruiterNav: NavItem[] = [
  { label: 'Dashboard', path: '/recruiter', description: 'Overview and quick actions' },
  { label: 'CV & Job Analysis', path: '/recruiter/analysis', description: 'Upload CV and job specification' },
  { label: 'Gap Analysis', path: '/recruiter/gap-analysis', description: 'Skill and experience match breakdown' },
  { label: 'Question Planning', path: '/recruiter/questions', description: 'AI-generated and custom questions' },
  { label: 'Interview Sessions', path: '/recruiter/sessions', description: 'Start and manage live sessions' },
  { label: 'Evaluation Reports', path: '/recruiter/reports', description: 'Post-interview assessments' },
  { label: 'Scheduling', path: '/recruiter/scheduling', description: 'Slots and notifications' },
  { label: 'Analytics', path: '/recruiter/analytics', description: 'Hiring pipeline insights' },
  { label: 'Bias Detection', path: '/recruiter/bias', description: 'Fairness monitoring' },
  { label: 'AI Assistant', path: '/recruiter/assistant', description: 'Natural language queries' },
  { label: 'Candidate Ranking', path: '/recruiter/ranking', description: 'Match scoring and shortlisting' },
  { label: 'Jobs & Pipeline', path: '/recruiter/jobs', description: 'Post roles and manage applications' },
]

export const candidateNav: NavItem[] = [
  { label: 'Dashboard', path: '/candidate', description: 'Your interview overview' },
  { label: 'My Sessions', path: '/candidate/sessions', description: 'Scheduled and completed interviews' },
  { label: 'Live Interview', path: '/candidate/interview', description: 'AI-conducted session room' },
  { label: 'Interview Feedback', path: '/candidate/feedback', description: 'Post-interview summary' },
  { label: 'Preparation', path: '/candidate/preparation', description: 'Practice questions and guidance' },
  { label: 'Applications', path: '/candidate/applications', description: 'Apply for roles and track status' },
  { label: 'My Profile', path: '/candidate/profile', description: 'CV and account settings' },
]
