# IntelliInterview

## Technology stack


| Layer            | Technology                                         |
| ---------------- | -------------------------------------------------- |
| Frontend         | React.js (Vite), TypeScript, Tailwind CSS          |
| Backend          | Python, FastAPI                                    |
| Database         | PostgreSQL with pgvector                           |
| Document parsing | Apache Tika                                        |
| AI / agent       | OpenAI GPT-4o                                      |
| Auth             | JWT with role-based access (Recruiter / Candidate) |


## Project layout

```
IntelliInterview/
├── backend/          # FastAPI REST API
└── ui/               # React recruiter dashboard & candidate portal
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ with [pgvector](https://github.com/pgvector/pgvector) extension
- Java 8+ runtime (required by Apache Tika for CV/job-spec parsing)

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.init_db
uvicorn app.main:app --reload --port 8080
```

API docs: [http://localhost:8080/docs](http://localhost:8080/docs)

### 2. Frontend

```bash
cd ui
npm install
npm run dev
```

UI: [http://localhost:5173](http://localhost:5173)

## Testing

```bash
cd backend
pytest
```

Tests use an in-memory SQLite database and do not require PostgreSQL.