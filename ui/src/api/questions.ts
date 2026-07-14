import { apiRequest } from './client'
import type { InterviewQuestion, QuestionPlan } from '../types/questions'

export function generateQuestions(gapAnalysisId: string) {
  return apiRequest<QuestionPlan>('/api/questions/generate', {
    method: 'POST',
    body: JSON.stringify({ gap_analysis_id: gapAnalysisId }),
  })
}

export function getPlanByAnalysis(analysisId: string) {
  return apiRequest<QuestionPlan>(`/api/questions/plans/by-analysis/${analysisId}`)
}

export function getPlan(planId: string) {
  return apiRequest<QuestionPlan>(`/api/questions/plans/${planId}`)
}

export function listQuestionPlans() {
  return apiRequest<QuestionPlan[]>('/api/questions/plans')
}

export function addCustomQuestion(planId: string, text: string, topic = 'custom') {
  return apiRequest<InterviewQuestion>('/api/questions/custom', {
    method: 'POST',
    body: JSON.stringify({ plan_id: planId, text, topic }),
  })
}

export function updateQuestion(
  questionId: string,
  payload: { text?: string; topic?: string; approved?: boolean },
) {
  return apiRequest<InterviewQuestion>(`/api/questions/${questionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function reorderQuestions(planId: string, questionIds: string[]) {
  return apiRequest<QuestionPlan>(`/api/questions/plans/${planId}/reorder`, {
    method: 'PUT',
    body: JSON.stringify({ question_ids: questionIds }),
  })
}

export function deleteQuestion(questionId: string) {
  return apiRequest<void>(`/api/questions/${questionId}`, {
    method: 'DELETE',
  })
}
