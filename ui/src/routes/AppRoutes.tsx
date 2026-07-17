import { Navigate, Route, Routes } from 'react-router-dom'
import { CandidateLayout } from '../components/layout/CandidateLayout'
import { PublicLayout } from '../components/layout/PublicLayout'
import { RecruiterLayout } from '../components/layout/RecruiterLayout'
import { ApplicationsPage } from '../pages/candidate/ApplicationsPage'
import { CandidateDashboard } from '../pages/candidate/CandidateDashboard'
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
import { CvJobAnalysisPage } from '../pages/recruiter/CvJobAnalysisPage'
import { GapAnalysisPage } from '../pages/recruiter/GapAnalysisPage'
import { InterviewSessionsPage } from '../pages/recruiter/InterviewSessionsPage'
import { JobsPipelinePage } from '../pages/recruiter/JobsPipelinePage'
import { NewSessionPage } from '../pages/recruiter/NewSessionPage'
import { QuestionPlanningPage } from '../pages/recruiter/QuestionPlanningPage'
import { ReportDetailPage } from '../pages/recruiter/ReportDetailPage'
import { ReportsPage } from '../pages/recruiter/ReportsPage'
import { RecruiterDashboard } from '../pages/recruiter/RecruiterDashboard'
import { SchedulingPage } from '../pages/recruiter/SchedulingPage'
import { SessionDetailPage } from '../pages/recruiter/SessionDetailPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="recruiter/login" element={<LoginPage role="recruiter" />} />
        <Route path="candidate/login" element={<LoginPage role="candidate" />} />
      </Route>

      <Route path="recruiter" element={<RecruiterLayout />}>
        <Route index element={<RecruiterDashboard />} />
        <Route path="analysis" element={<CvJobAnalysisPage />} />
        <Route path="gap-analysis" element={<GapAnalysisPage />} />
        <Route path="questions" element={<QuestionPlanningPage />} />
        <Route path="sessions" element={<InterviewSessionsPage />} />
        <Route path="sessions/new" element={<NewSessionPage />} />
        <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="reports/sample" element={<ReportDetailPage />} />
        <Route path="scheduling" element={<SchedulingPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="bias" element={<BiasDetectionPage />} />
        <Route path="assistant" element={<AiAssistantPage />} />
        <Route path="ranking" element={<CandidateRankingPage />} />
        <Route path="jobs" element={<JobsPipelinePage />} />
      </Route>

      <Route path="candidate" element={<CandidateLayout />}>
        <Route index element={<CandidateDashboard />} />
        <Route path="sessions" element={<MySessionsPage />} />
        <Route path="interview" element={<LiveInterviewPage />} />
        <Route path="feedback" element={<CandidateFeedbackPage />} />
        <Route path="preparation" element={<PreparationPage />} />
        <Route path="applications" element={<ApplicationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
