"""Application settings - non-secret values are edited here directly (no .env file).
Secrets (openai_api_key, smtp_password) are read from environment variables - see the
OPENAI_API_KEY and SMTP_APP_PASSWORD entries below - so they never sit in source control.
Set them locally with (PowerShell): setx OPENAI_API_KEY "sk-..." and
setx SMTP_APP_PASSWORD "your-gmail-app-password", then open a new terminal."""

import os


class Settings:
    app_name: str = "IntelliInterview"
    app_env: str = "development"

    # Local PostgreSQL (install pgvector extension manually: CREATE EXTENSION vector;)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/intelliinterview"

    jwt_secret: str = "change-this-secret-key-to-at-least-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    # Read from the environment - never hardcode a real key here (this file is committed).
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o"
    # Pinned so the same text always embeds to the same vector - this feeds the
    # deterministic match score, unlike chat completions which vary between runs.
    openai_embedding_model: str = "text-embedding-3-small"
    # Starting guess for text-embedding-3-small; see scripts/calibrate_semantic_threshold.py
    # to recompute from real CV/job data before trusting this in production.
    semantic_match_threshold: float = 0.45
    # Live interview proctoring: candidate video frames are checked for looking-away /
    # prohibited objects (see app/services/proctoring.py). This many violations disqualifies
    # the session. Checks fail open (no warning) if no API key is configured or the call fails.
    proctoring_warning_limit: int = 3
    upload_max_size_mb: int = 10
    # ~1GB headroom for a 45-minute webm interview recording (video+audio at typical
    # MediaRecorder default bitrates run roughly 700MB-900MB for that length).
    recording_max_size_mb: int = 1024
    frontend_base_url: str = "http://localhost:5173"

    # Gmail SMTP (App Password). OTP codes are always printed to the backend console as well.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "Intellinterview@gmail.com"
    # Read from the environment - never hardcode a real app password here (this file is committed).
    smtp_password: str = os.environ.get("SMTP_APP_PASSWORD", "")
    smtp_from_email: str = "Intellinterview@gmail.com"
    smtp_use_tls: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
