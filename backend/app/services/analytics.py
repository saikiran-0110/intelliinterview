"""Aggregate hiring activity for recruiter analytics."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    InterviewReport,
    InterviewSession,
    InterviewSessionStatus,
    JobApplication,
    JobSpecification,
    PipelineStage,
)


class AnalyticsService:
    def overview(self, db: Session, recruiter_id: UUID) -> dict:
        jobs = (
            db.query(JobSpecification)
            .filter(JobSpecification.created_by == recruiter_id)
            .order_by(JobSpecification.created_at.desc())
            .all()
        )
        applications = db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter_id).all()
        sessions = db.query(InterviewSession).filter(InterviewSession.recruiter_id == recruiter_id).all()
        reports = db.query(InterviewReport).filter(InterviewReport.recruiter_id == recruiter_id).all()

        apps_by_role: dict[str, int] = defaultdict(int)
        for app in applications:
            job = next((item for item in jobs if item.id == app.job_spec_id), None)
            title = job.title if job else "Unknown role"
            apps_by_role[title] += 1

        # Include jobs with zero applications so open roles still appear.
        for job in jobs:
            apps_by_role.setdefault(job.title, 0)

        stage_counts: dict[str, int] = {stage.value: 0 for stage in PipelineStage}
        for app in applications:
            stage_counts[app.stage.value] = stage_counts.get(app.stage.value, 0) + 1

        # Sessions without applications still count toward interview stage.
        interview_sessions = [
            item for item in sessions if item.status in {InterviewSessionStatus.SCHEDULED, InterviewSessionStatus.IN_PROGRESS, InterviewSessionStatus.COMPLETED}
        ]
        if stage_counts[PipelineStage.INTERVIEW.value] == 0 and interview_sessions:
            stage_counts[PipelineStage.INTERVIEW.value] = len(
                {item.candidate_user_id for item in interview_sessions}
            )

        open_positions = []
        for job in jobs:
            role_apps = [app for app in applications if app.job_spec_id == job.id]
            role_sessions = [item for item in sessions if item.job_spec_id == job.id]
            completed = [item for item in role_sessions if item.status == InterviewSessionStatus.COMPLETED]
            hired = [app for app in role_apps if app.stage == PipelineStage.HIRED]
            progress = 0.0
            if hired:
                progress = 100.0
            elif completed:
                progress = 70.0
            elif role_sessions:
                progress = 45.0
            elif role_apps:
                progress = 25.0
            open_positions.append(
                {
                    "job_spec_id": str(job.id),
                    "job_title": job.title,
                    "applications": len(role_apps),
                    "interviews": len(role_sessions),
                    "completed_interviews": len(completed),
                    "hired": len(hired),
                    "progress_percent": progress,
                }
            )

        return {
            "total_roles": len(jobs),
            "total_applications": len(applications),
            "total_sessions": len(sessions),
            "completed_reports": len(reports),
            "applications_per_role": [
                {"job_title": title, "count": count} for title, count in sorted(apps_by_role.items())
            ],
            "pipeline_stages": [
                {"stage": stage, "count": count} for stage, count in stage_counts.items()
            ],
            "open_positions": open_positions,
        }
