import { Navigate, Route, Routes } from 'react-router-dom'
import { CandidateLayout } from '../components/layout/CandidateLayout'
import { PublicLayout } from '../components/layout/PublicLayout'
import { RecruiterLayout } from '../components/layout/RecruiterLayout'
import { ApplicationsPage } from '../pages/candidate/ApplicationsPage'
import { CandidateFeedbackPage } from '../pages/candidate/CandidateFeedbackPage'
import { LiveInterviewPage } from '../pages/candidate/LiveInterviewPage'
import { MySessionsPage } from '../pages/candidate/MySessionsPage'
import { PreparationPage } from '../pages/candidate/PreparationPage'
import { ProfilePage } from '../pages/candidate/ProfilePage'
import { LandingPage } from '../pages/public/LandingPage'
import { LoginPage } from '../pages/public/LoginPage'
import { AiAssistantPage } from '../pages/recruiter/AiAssistantPage'
import { AnalyticsPage } from '../pages/recruiter/AnalyticsPage'
import { BiasDetectionPage } from '../pages/recruiter/BiasDetectionPage'
import { CandidateRankingPage } from '../pages/recruiter/CandidateRankingPage'
import { DashboardPage } from '../pages/recruiter/DashboardPage'
import { InterviewSessionsPage } from '../pages/recruiter/InterviewSessionsPage'
import { JobsPipelinePage } from '../pages/recruiter/JobsPipelinePage'
import { NewSessionPage } from '../pages/recruiter/NewSessionPage'
import { QuestionPlanningPage } from '../pages/recruiter/QuestionPlanningPage'
import { ReportDetailPage } from '../pages/recruiter/ReportDetailPage'
import { ReportsPage } from '../pages/recruiter/ReportsPage'
import { SchedulingPage } from '../pages/recruiter/SchedulingPage'
import { SessionDetailPage } from '../pages/recruiter/SessionDetailPage'
import { RecruiterProfilePage } from '../pages/recruiter/RecruiterProfilePage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="recruiter/login" element={<LoginPage role="recruiter" />} />
        <Route path="candidate/login" element={<LoginPage role="candidate" />} />
      </Route>

      <Route path="recruiter" element={<RecruiterLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="jobs" element={<JobsPipelinePage />} />
        <Route path="ranking" element={<CandidateRankingPage />} />
        <Route path="assistant" element={<AiAssistantPage />} />
        <Route path="scheduling" element={<SchedulingPage />} />
        <Route path="sessions" element={<InterviewSessionsPage />} />
        <Route path="sessions/new" element={<NewSessionPage />} />
        <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
        <Route path="questions" element={<QuestionPlanningPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="reports/:reportId" element={<ReportDetailPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="bias" element={<BiasDetectionPage />} />
        <Route path="profile" element={<RecruiterProfilePage />} />
        {/* Legacy analysis routes redirect into the live hiring flow */}
        <Route path="analysis" element={<Navigate to="/recruiter/jobs" replace />} />
        <Route path="gap-analysis" element={<Navigate to="/recruiter/ranking" replace />} />
      </Route>

      <Route path="candidate" element={<CandidateLayout />}>
        <Route index element={<Navigate to="applications" replace />} />
        <Route path="applications" element={<ApplicationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="preparation" element={<PreparationPage />} />
        <Route path="sessions" element={<MySessionsPage />} />
        <Route path="interview" element={<LiveInterviewPage />} />
        <Route path="interview/:sessionId" element={<LiveInterviewPage />} />
        <Route path="feedback" element={<CandidateFeedbackPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
