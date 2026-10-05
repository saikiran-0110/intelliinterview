"""Application settings - edit values here directly (no .env file)."""


class Settings:
    app_name: str = "IntelliInterview"
    app_env: str = "development"

    # Local PostgreSQL (install pgvector extension manually: CREATE EXTENSION vector;)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/intelliinterview"

    jwt_secret: str = "change-this-secret-key-to-at-least-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    # Pinned so the same text always embeds to the same vector - this feeds the
    # deterministic match score, unlike chat completions which vary between runs.
    openai_embedding_model: str = "text-embedding-3-small"
    # Starting guess for text-embedding-3-small; see scripts/calibrate_semantic_threshold.py
    # to recompute from real CV/job data before trusting this in production.
    semantic_match_threshold: float = 0.45
    upload_max_size_mb: int = 10
    # ~1GB headroom for a 45-minute webm interview recording (video+audio at typical
    # MediaRecorder default bitrates run roughly 700MB-900MB for that length).
    recording_max_size_mb: int = 1024
    frontend_base_url: str = "http://localhost:5173"

    # Gmail SMTP (App Password). OTP codes are always printed to the backend console as well.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "Intellinterview@gmail.com"
    smtp_password: str = "REDACTED-SMTP-APP-PASSWORD-ROTATE-IF-STILL-ACTIVE"
    smtp_from_email: str = "Intellinterview@gmail.com"
    smtp_use_tls: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
