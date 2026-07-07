"""Application settings — edit values here directly (no .env file)."""


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
    upload_max_size_mb: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
