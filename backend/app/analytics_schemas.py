from pydantic import BaseModel


class RoleApplicationCount(BaseModel):
    job_title: str
    count: int


class PipelineStageCount(BaseModel):
    stage: str
    count: int


class OpenPositionProgress(BaseModel):
    job_spec_id: str
    job_title: str
    applications: int
    interviews: int
    completed_interviews: int
    hired: int
    progress_percent: float


class AnalyticsOverviewResponse(BaseModel):
    total_roles: int
    total_applications: int
    total_sessions: int
    completed_reports: int
    applications_per_role: list[RoleApplicationCount]
    pipeline_stages: list[PipelineStageCount]
    open_positions: list[OpenPositionProgress]
