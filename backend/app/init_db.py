"""Create database tables and apply additive column upgrades for existing DBs."""

from sqlalchemy import inspect, text

from app.database import Base, engine
import app.models  # noqa: F401 - register models with SQLAlchemy metadata


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
    (
        "language",
        "ALTER TABLE interview_sessions "
        "ADD COLUMN IF NOT EXISTS language VARCHAR(10) NOT NULL DEFAULT 'en-GB'",
    ),
]

JOB_SPEC_COLUMN_UPGRADES = [
    (
        "is_open",
        "ALTER TABLE job_specifications "
        "ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT TRUE",
    ),
    (
        "department",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS department VARCHAR(120)",
    ),
    (
        "location",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS location VARCHAR(255)",
    ),
    (
        "employment_type",
        "ALTER TABLE job_specifications "
        "ADD COLUMN IF NOT EXISTS employment_type VARCHAR(40) NOT NULL DEFAULT 'FULL_TIME'",
    ),
    (
        "work_mode",
        "ALTER TABLE job_specifications "
        "ADD COLUMN IF NOT EXISTS work_mode VARCHAR(40) NOT NULL DEFAULT 'HYBRID'",
    ),
    (
        "salary_min_gbp",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS salary_min_gbp DOUBLE PRECISION",
    ),
    (
        "salary_max_gbp",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS salary_max_gbp DOUBLE PRECISION",
    ),
    (
        "years_experience_min",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS years_experience_min INTEGER",
    ),
    (
        "closing_date",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS closing_date DATE",
    ),
    (
        "benefits",
        "ALTER TABLE job_specifications ADD COLUMN IF NOT EXISTS benefits TEXT",
    ),
]

APPLICATION_COLUMN_UPGRADES = [
    (
        "contact_full_name",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS contact_full_name VARCHAR(120)",
    ),
    (
        "contact_email",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)",
    ),
    (
        "contact_phone",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(40)",
    ),
    (
        "contact_linkedin",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS contact_linkedin VARCHAR(255)",
    ),
    (
        "current_location",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS current_location VARCHAR(255)",
    ),
    (
        "expected_salary_gbp",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS expected_salary_gbp DOUBLE PRECISION",
    ),
    (
        "right_to_work_uk",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS right_to_work_uk BOOLEAN",
    ),
    (
        "cover_note",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS cover_note TEXT",
    ),
]

USER_COLUMN_UPGRADES = [
    ("phone", "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(40)"),
    ("company", "ALTER TABLE users ADD COLUMN IF NOT EXISTS company VARCHAR(120)"),
    ("job_title", "ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(120)"),
    ("location", "ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255)"),
    ("linkedin_url", "ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(255)"),
    (
        "email_verified",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE",
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

PREPARATION_COLUMN_UPGRADES = [
    (
        "study_modules",
        "ALTER TABLE preparation_packs ADD COLUMN IF NOT EXISTS study_modules JSON",
    ),
    (
        "checklist_items",
        "ALTER TABLE preparation_packs ADD COLUMN IF NOT EXISTS checklist_items JSON",
    ),
    (
        "completed_item_ids",
        "ALTER TABLE preparation_packs ADD COLUMN IF NOT EXISTS completed_item_ids JSON",
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
    _add_missing_columns("job_applications", APPLICATION_COLUMN_UPGRADES)
    _add_missing_columns("users", USER_COLUMN_UPGRADES)
    _add_missing_columns("preparation_packs", PREPARATION_COLUMN_UPGRADES)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    _upgrade_existing_tables()
    print("Database tables created/updated.")


if __name__ == "__main__":
    main()
