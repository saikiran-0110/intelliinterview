import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    CandidateCv,
    JobApplication,
    JobSpecification,
    PipelineStage,
    User,
    UserRole,
)
from app.services.bias_detection import BiasDetectionService
from app.services.security import hash_password
from tests.helpers import auth_headers, register_recruiter


def _make_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _make_recruiter(db, email: str, company: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Recruiter",
        role=UserRole.RECRUITER,
        company=company,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_applications(db, recruiter: User, job: JobSpecification, candidate: User, total: int, shortlisted: int):
    for index in range(total):
        stage = PipelineStage.SHORTLISTED if index < shortlisted else PipelineStage.APPLIED
        app = JobApplication(
            job_spec_id=job.id,
            candidate_user_id=candidate.id,
            recruiter_id=recruiter.id,
            stage=stage,
            match_score=60.0,
        )
        db.add(app)
    db.commit()


def test_three_recruiters_with_divergent_shortlist_rates_produce_alert():
    db = _make_session()
    recruiter_a = _make_recruiter(db, "org-a@example.com", "Acme Corp")
    recruiter_b = _make_recruiter(db, "org-b@example.com", "Acme Corp")
    recruiter_c = _make_recruiter(db, "org-c@example.com", "Acme Corp")
    candidate = User(
        email="org-candidate@example.com",
        password_hash=hash_password("password123"),
        full_name="Candidate",
        role=UserRole.CANDIDATE,
        email_verified=True,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    job = JobSpecification(title="Engineer", description="Role", created_by=recruiter_a.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    _make_applications(db, recruiter_a, job, candidate, total=8, shortlisted=2)  # rate 0.25
    _make_applications(db, recruiter_b, job, candidate, total=8, shortlisted=6)  # rate 0.75
    _make_applications(db, recruiter_c, job, candidate, total=6, shortlisted=3)  # rate 0.5

    service = BiasDetectionService()
    result = service.analyze_organisation(db, "Acme Corp", caller_id=recruiter_a.id)

    assert result["recruiter_count"] == 3
    assert result["insufficient_sample"] is False
    divergence = next(
        (a for a in result["alerts"] if a["alert_type"] == "cross_recruiter_shortlist_divergence"), None
    )
    assert divergence is not None
    assert divergence["recruiter_label"] == "Organisation"
    assert divergence["metric_payload"]["spread"] >= 0.40

    labels = {figure["label"] for figure in result["recruiter_figures"]}
    assert "You" in labels
    assert not any(label in {"org-b@example.com", "org-c@example.com"} for label in labels)
    db.close()


def test_single_recruiter_gets_insufficient_sample_note(client):
    recruiter_token = register_recruiter(client, email="org-solo@example.com")
    response = client.get("/api/bias/organisation", headers=auth_headers(recruiter_token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["insufficient_sample"] is True
    assert payload["company"] is None
    assert payload["notes"]


def test_recruiter_cannot_see_another_companys_data(client):
    company_x_token = register_recruiter(client, email="org-x@example.com")
    client.patch(
        "/api/auth/me",
        headers=auth_headers(company_x_token),
        json={"full_name": "Recruiter X", "company": "Company X"},
    )
    company_y_token = register_recruiter(client, email="org-y@example.com")
    client.patch(
        "/api/auth/me",
        headers=auth_headers(company_y_token),
        json={"full_name": "Recruiter Y", "company": "Company Y"},
    )

    response_x = client.get("/api/bias/organisation", headers=auth_headers(company_x_token))
    assert response_x.status_code == 200
    assert response_x.json()["company"] == "Company X"
    assert response_x.json()["recruiter_count"] == 1


def test_organisation_bias_requires_auth(client):
    response = client.get("/api/bias/organisation")
    assert response.status_code == 401
