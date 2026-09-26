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
    User,
    UserRole,
)

SHORTLISTED_STAGES = {
    PipelineStage.SHORTLISTED,
    PipelineStage.INTERVIEW,
    PipelineStage.OFFER,
    PipelineStage.HIRED,
}


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

    def analyze_organisation(self, db: Session, company: str | None, caller_id: UUID) -> dict:
        """Aggregate the existing per-recruiter analyze() across every recruiter sharing a
        company name, plus one organisation-only check: cross-recruiter shortlist-rate
        divergence. Reuses analyze() rather than duplicating its logic."""
        normalized_company = (company or "").strip()
        base_notes = [
            "Monitoring uses role, match-score bands, and interview score patterns only.",
            "No demographic attributes are inferred from CV text.",
            "Alerts are advisory and do not block hiring decisions.",
            "Organisation view aggregates recruiters sharing a company name; it infers no demographics.",
        ]

        if not normalized_company:
            alerts = self.analyze(db, caller_id)
            return {
                "company": None,
                "recruiter_count": 1,
                "insufficient_sample": True,
                "alerts": [
                    {
                        "recruiter_label": "You",
                        "alert_type": a.alert_type,
                        "severity": a.severity,
                        "title": a.title,
                        "description": a.description,
                        "metric_payload": a.metric_payload or {},
                    }
                    for a in alerts
                ],
                "recruiter_figures": [],
                "notes": [
                    "No company is set on this account, so this view covers only your own pipeline "
                    "(an organisation of one).",
                    *base_notes,
                ],
            }

        recruiters = [
            user
            for user in db.query(User).filter(User.role == UserRole.RECRUITER).all()
            if (user.company or "").strip().lower() == normalized_company.lower()
        ]
        if caller_id not in {r.id for r in recruiters}:
            caller = db.get(User, caller_id)
            if caller:
                recruiters.append(caller)

        ordered = sorted(recruiters, key=lambda u: str(u.id))
        anon_labels = {user.id: f"Recruiter {chr(65 + i)}" for i, user in enumerate(ordered)}

        def label_for(user_id: UUID) -> str:
            return "You" if user_id == caller_id else anon_labels[user_id]

        aggregated_alerts: list[dict] = []
        eligible_rates: list[tuple[UUID, float, int]] = []
        total_scored = 0

        for recruiter in ordered:
            recruiter_alerts = self.analyze(db, recruiter.id)
            label = label_for(recruiter.id)
            for alert in recruiter_alerts:
                aggregated_alerts.append(
                    {
                        "recruiter_label": label,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "title": alert.title,
                        "description": alert.description,
                        "metric_payload": alert.metric_payload or {},
                    }
                )

            applications = db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter.id).all()
            scored = [app for app in applications if app.match_score is not None]
            total_scored += len(scored)
            if len(scored) >= 6:
                shortlisted = [app for app in scored if app.stage in SHORTLISTED_STAGES]
                rate = len(shortlisted) / len(scored)
                eligible_rates.append((recruiter.id, rate, len(scored)))

        insufficient_sample = len(ordered) < 2 or total_scored < 15

        recruiter_figures = [
            {"label": label_for(rid), "shortlist_rate": round(rate, 2), "scored_applications": count}
            for rid, rate, count in eligible_rates
        ]

        if not insufficient_sample and len(eligible_rates) >= 3:
            rates = [rate for _, rate, _ in eligible_rates]
            spread = max(rates) - min(rates)
            if spread >= 0.40:
                aggregated_alerts.insert(
                    0,
                    {
                        "recruiter_label": "Organisation",
                        "alert_type": "cross_recruiter_shortlist_divergence",
                        "severity": BiasAlertSeverity.MEDIUM,
                        "title": "Shortlist rates diverge sharply across recruiters",
                        "description": (
                            f"Shortlist rates across {len(eligible_rates)} recruiters with enough "
                            f"scored applications range from {min(rates):.0%} to {max(rates):.0%}, "
                            "a spread of 40 percentage points or more. This does not identify which "
                            "recruiters are outliers - review shortlisting criteria with the team."
                        ),
                        "metric_payload": {
                            "recruiter_count": len(eligible_rates),
                            "min_rate": round(min(rates), 2),
                            "max_rate": round(max(rates), 2),
                            "spread": round(spread, 2),
                        },
                    },
                )

        notes = list(base_notes)
        if insufficient_sample:
            notes.insert(
                0,
                "Not enough organisation-wide data yet (need at least 2 recruiters and 15 scored "
                "applications) for the cross-recruiter divergence check.",
            )

        return {
            "company": company,
            "recruiter_count": len(ordered),
            "insufficient_sample": insufficient_sample,
            "alerts": aggregated_alerts,
            "recruiter_figures": recruiter_figures,
            "notes": notes,
        }
