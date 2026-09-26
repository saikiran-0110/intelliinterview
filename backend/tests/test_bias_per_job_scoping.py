from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import JobApplication, JobSpecification, PipelineStage, User, UserRole
from app.services.bias_detection import BiasDetectionService
from app.services.security import hash_password


def _make_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _make_applications(db, job, candidate, recruiter, *, score: float, shortlisted: bool, count: int):
    for _ in range(count):
        db.add(
            JobApplication(
                job_spec_id=job.id,
                candidate_user_id=candidate.id,
                recruiter_id=recruiter.id,
                stage=PipelineStage.SHORTLISTED if shortlisted else PipelineStage.APPLIED,
                match_score=score,
            )
        )
    db.commit()


def test_shortlist_inversion_is_scoped_per_job_not_pooled_across_roles():
    # A recruiter runs two roles. Job A (senior) is shortlisted correctly: high scorers
    # in, low scorers out. Job B (junior) has a real inversion: low scorers shortlisted,
    # high scorers passed over. Pooling both jobs' applications together (the old
    # behaviour) exactly cancels these two signals out - high_rate and low_rate both
    # land at 0.5, a 0 spread, so the real problem in Job B would never surface. Scoped
    # per job, it must be flagged, and only for Job B.
    db = _make_session()
    recruiter = User(
        email="scoped-recruiter@example.com",
        password_hash=hash_password("password123"),
        full_name="Recruiter",
        role=UserRole.RECRUITER,
        email_verified=True,
    )
    candidate = User(
        email="scoped-candidate@example.com",
        password_hash=hash_password("password123"),
        full_name="Candidate",
        role=UserRole.CANDIDATE,
        email_verified=True,
    )
    db.add_all([recruiter, candidate])
    db.commit()

    job_a = JobSpecification(title="Senior Role", description="d", created_by=recruiter.id)
    job_b = JobSpecification(title="Junior Role", description="d", created_by=recruiter.id)
    db.add_all([job_a, job_b])
    db.commit()

    # Job A: aligned, unbiased shortlisting.
    _make_applications(db, job_a, candidate, recruiter, score=85, shortlisted=True, count=3)
    _make_applications(db, job_a, candidate, recruiter, score=30, shortlisted=False, count=3)
    # Job B: real inversion - the low scorers are the ones getting shortlisted.
    _make_applications(db, job_b, candidate, recruiter, score=85, shortlisted=False, count=3)
    _make_applications(db, job_b, candidate, recruiter, score=30, shortlisted=True, count=3)

    service = BiasDetectionService()
    alerts = service.analyze(db, recruiter.id)

    inversion_alerts = [a for a in alerts if a.alert_type.startswith("shortlist_match_inversion:")]
    assert len(inversion_alerts) == 1
    assert str(job_b.id) in inversion_alerts[0].alert_type
    assert "Junior Role" in inversion_alerts[0].title
    assert str(job_a.id) not in inversion_alerts[0].alert_type
    db.close()


def test_role_concentration_alerts_do_not_clobber_each_other():
    # Two different roles both concentrated relative to their application share used to
    # share one alert_type ("role_shortlist_concentration"), so the second upsert would
    # silently overwrite the first role's persisted alert. Each concentrated role must
    # now get its own alert.
    db = _make_session()
    recruiter = User(
        email="concentration-recruiter@example.com",
        password_hash=hash_password("password123"),
        full_name="Recruiter",
        role=UserRole.RECRUITER,
        email_verified=True,
    )
    candidate = User(
        email="concentration-candidate@example.com",
        password_hash=hash_password("password123"),
        full_name="Candidate",
        role=UserRole.CANDIDATE,
        email_verified=True,
    )
    db.add_all([recruiter, candidate])
    db.commit()

    job_a = JobSpecification(title="Role A", description="d", created_by=recruiter.id)
    job_b = JobSpecification(title="Role B", description="d", created_by=recruiter.id)
    job_c = JobSpecification(title="Role C", description="d", created_by=recruiter.id)
    db.add_all([job_a, job_b, job_c])
    db.commit()

    # Role A: a small application share but a large share of all shortlists.
    _make_applications(db, job_a, candidate, recruiter, score=80, shortlisted=True, count=2)
    # Role B: the same disproportionate pattern.
    _make_applications(db, job_b, candidate, recruiter, score=80, shortlisted=True, count=2)
    # Role C: bulk of applications, none shortlisted, diluting A/B's application share
    # without adding to the shortlist count.
    _make_applications(db, job_c, candidate, recruiter, score=40, shortlisted=False, count=30)

    service = BiasDetectionService()
    alerts = service.analyze(db, recruiter.id)

    concentration_alerts = [a for a in alerts if a.alert_type.startswith("role_shortlist_concentration:")]
    flagged_job_ids = {a.metric_payload["job_spec_id"] for a in concentration_alerts}
    assert str(job_a.id) in flagged_job_ids
    assert str(job_b.id) in flagged_job_ids
    assert len(concentration_alerts) == len(flagged_job_ids)
    db.close()
