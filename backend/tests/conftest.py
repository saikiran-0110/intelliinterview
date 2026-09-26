import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

settings.jwt_secret = "test-secret-key-with-minimum-32-characters"
settings.openai_api_key = ""  # tests exercise the deterministic baseline, never live OpenAI


@pytest.fixture(autouse=True)
def disable_real_smtp(monkeypatch):
    class DisabledSmtp:
        def __init__(self, *args, **kwargs):
            raise OSError("SMTP disabled in tests")

    monkeypatch.setattr("app.services.email.smtplib.SMTP", DisabledSmtp)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
