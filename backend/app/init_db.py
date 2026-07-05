"""Create database tables. Run once after configuring PostgreSQL in app/config.py."""

from app.database import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()
