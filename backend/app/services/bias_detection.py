"""Detect potential unbalanced shortlisting and scoring patterns (no demographics)."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    BiasAlert,
    BiasAlertSeverity,
    InterviewReport,
    JobApplication,
    JobSpecification,
    PipelineStage,
)


class BiasDetectionService:
    def analyze(self, db: Session, recruiter_id: UUID) -> list[BiasAlert]:
        applications = db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter_id).all()
        reports = db.query(InterviewReport).filter(InterviewReport.recruiter_id == recruiter_id).all()
        alerts: list[BiasAlert] = []

        # Alert 1: shortlist rate vs match score bands looks inverted.
        with_scores = [app for app in applications if app.match_score is not None]
        if len(with_scores) >= 6:
            high = [app for app in with_scores if (app.match_score or 0) >= 70]
            low = [app for app in with_scores if (app.match_score or 0) < 50]
            high_shortlisted = [
                app for app in high if app.stage in {PipelineStage.SHORTLISTED, PipelineStage.INTERVIEW, PipelineStage.OFFER, PipelineStage.HIRED}
            ]
            low_shortlisted = [
                app for app in low if app.stage in {PipelineStage.SHORTLISTED, PipelineStage.INTERVIEW, PipelineStage.OFFER, PipelineStage.HIRED}
            ]
            high_rate = len(high_shortlisted) / len(high) if high else 0
            low_rate = len(low_shortlisted) / len(low) if low else 0
            if low and high and low_rate - high_rate >= 0.35:
                alerts.append(
                    self._upsert_alert(
                        db,
                        recruiter_id,
                        alert_type="shortlist_match_inversion",
                        severity=BiasAlertSeverity.HIGH,
                        title="Shortlisting may not align with match scores",
                        description=(
                            "Candidates in lower match-score bands were shortlisted more often than "
                            "higher-match candidates in the current window. Review shortlisting decisions."
                        ),
                        payload={
                            "high_band_shortlist_rate": round(high_rate, 2),
                            "low_band_shortlist_rate": round(low_rate, 2),
                            "sample_size": len(with_scores),
                        },
                    )
                )

        # Alert 2: interview overall scores unusually low-variance (possible rubber-stamping).
        scores = [report.overall_score for report in reports]
        if len(scores) >= 5:
            spread = pstdev(scores)
            if spread < 0.4:
                alerts.append(
                    self._upsert_alert(
                        db,
                        recruiter_id,
                        alert_type="score_low_variance",
                        severity=BiasAlertSeverity.MEDIUM,
                        title="Interview scores show unusually low variation",
                        description=(
                            "Recent interview overall scores are tightly clustered. "
                            "This may indicate insufficient differentiation between candidates."
                        ),
                        payload={"score_count": len(scores), "stdev": round(spread, 3), "mean": round(mean(scores), 2)},
                    )
                )

        # Alert 3: one role dominates shortlists heavily versus applications share.
        by_role_apps: dict[UUID, int] = defaultdict(int)
        by_role_shortlists: dict[UUID, int] = defaultdict(int)
        for app in applications:
            by_role_apps[app.job_spec_id] += 1
            if app.stage in {PipelineStage.SHORTLISTED, PipelineStage.INTERVIEW, PipelineStage.OFFER, PipelineStage.HIRED}:
                by_role_shortlists[app.job_spec_id] += 1
        total_apps = sum(by_role_apps.values())
        total_shortlists = sum(by_role_shortlists.values())
        if total_apps >= 8 and total_shortlists >= 4:
            for job_id, shortlist_count in by_role_shortlists.items():
                app_share = by_role_apps[job_id] / total_apps
                shortlist_share = shortlist_count / total_shortlists
                if shortlist_share - app_share >= 0.4:
                    job = db.get(JobSpecification, job_id)
                    alerts.append(
                        self._upsert_alert(
                            db,
                            recruiter_id,
                            alert_type="role_shortlist_concentration",
                            severity=BiasAlertSeverity.MEDIUM,
                            title="Shortlists concentrated on one role",
                            description=(
                                f"Shortlisting is disproportionately concentrated on "
                                f"{job.title if job else 'one role'} relative to application volume."
                            ),
                            payload={
                                "job_spec_id": str(job_id),
                                "application_share": round(app_share, 2),
                                "shortlist_share": round(shortlist_share, 2),
                            },
                        )
                    )

        # Keep at least an info alert when sample is small so UI is not empty.
        if not alerts:
            alerts.append(
                self._upsert_alert(
                    db,
                    recruiter_id,
                    alert_type="insufficient_sample",
                    severity=BiasAlertSeverity.LOW,
                    title="Not enough data for strong bias signals",
                    description=(
                        "Continue collecting shortlisting and interview outcomes. "
                        "Bias monitoring uses role/match/score patterns only - no demographic inference."
                    ),
                    payload={"applications": len(applications), "reports": len(reports)},
                )
            )

        return alerts

    def _upsert_alert(
        self,
        db: Session,
        recruiter_id: UUID,
        *,
        alert_type: str,
        severity: BiasAlertSeverity,
        title: str,
        description: str,
        payload: dict,
    ) -> BiasAlert:
        existing = (
            db.query(BiasAlert)
            .filter(
                BiasAlert.recruiter_id == recruiter_id,
                BiasAlert.alert_type == alert_type,
                BiasAlert.acknowledged.is_(False),
            )
            .order_by(BiasAlert.created_at.desc())
            .first()
        )
        if existing:
            existing.severity = severity
            existing.title = title
            existing.description = description
            existing.metric_payload = payload
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        alert = BiasAlert(
            recruiter_id=recruiter_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            metric_payload=payload,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def list_alerts(self, db: Session, recruiter_id: UUID) -> list[BiasAlert]:
        return (
            db.query(BiasAlert)
            .filter(BiasAlert.recruiter_id == recruiter_id)
            .order_by(BiasAlert.created_at.desc())
            .all()
        )

    def acknowledge(self, db: Session, alert: BiasAlert) -> BiasAlert:
        from datetime import datetime, timezone

        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
