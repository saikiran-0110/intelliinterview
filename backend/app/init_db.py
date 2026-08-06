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


def _upgrade_existing_tables() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "interview_sessions" not in tables:
        return

    existing_columns = {col["name"] for col in inspector.get_columns("interview_sessions")}
    with engine.begin() as conn:
        for column_name, ddl in SESSION_COLUMN_UPGRADES:
            if column_name not in existing_columns:
                conn.execute(text(ddl))
                print(f"Added column interview_sessions.{column_name}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    _upgrade_existing_tables()
    print("Database tables created/updated.")


if __name__ == "__main__":
    main()
