"""Create database tables and apply additive column upgrades for existing DBs."""

from sqlalchemy import inspect, text

from app.database import Base, engine
import app.models  # noqa: F401 — register models with SQLAlchemy metadata


SESSION_COLUMN_UPGRADES = [
    (
        "confirmation_status",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS confirmation_status VARCHAR(40) NOT NULL DEFAULT 'PENDING'",
    ),
    (
        "duration_minutes",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS duration_minutes INTEGER NOT NULL DEFAULT 45",
    ),
    (
        "timezone",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'",
    ),
    (
        "confirmed_at",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE",
    ),
    (
        "candidate_note",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS candidate_note TEXT",
    ),
]

JOB_SPEC_COLUMN_UPGRADES = [
    (
        "is_open",
        "ALTER TABLE job_specifications "
        "ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT TRUE",
    ),
]

CV_COLUMN_UPGRADES = [
    (
        "file_data",
        "ALTER TABLE candidate_cvs ADD COLUMN IF NOT EXISTS file_data BYTEA",
    ),
    (
        "content_type",
        "ALTER TABLE candidate_cvs ADD COLUMN IF NOT EXISTS content_type VARCHAR(120)",
    ),
]


def _add_missing_columns(table_name: str, upgrades: list[tuple[str, str]]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    with engine.begin() as conn:
        for column_name, ddl in upgrades:
            if column_name not in existing_columns:
                conn.execute(text(ddl))
                print(f"Added column {table_name}.{column_name}")


def _upgrade_existing_tables() -> None:
    _add_missing_columns("interview_sessions", SESSION_COLUMN_UPGRADES)
    _add_missing_columns("job_specifications", JOB_SPEC_COLUMN_UPGRADES)
    _add_missing_columns("candidate_cvs", CV_COLUMN_UPGRADES)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    _upgrade_existing_tables()
    print("Database tables created/updated.")


if __name__ == "__main__":
    main()
