# IntelliInterview

AI-assisted interview platform for **software engineering roles** — CO7201 Individual Project (Saikiran Buchiraju, skb72@student.le.ac.uk).

## Technology stack

| Layer | Technology |
|-------|------------|
| Frontend | React.js (Vite), TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL with pgvector |
| Document parsing | Apache Tika |
| AI / agent | OpenAI GPT-4o |
| Auth | JWT with role-based access (Recruiter / Candidate) |

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

## Configuration

All settings live in `backend/app/config.py`. Edit that file to set your database URL, JWT secret, and OpenAI API key.

## Quick start

### 1. Database

Install PostgreSQL locally, create a database and user, then enable pgvector:

```sql
CREATE DATABASE intelliinterview;
CREATE USER intelliinterview WITH PASSWORD 'intelliinterview';
GRANT ALL PRIVILEGES ON DATABASE intelliinterview TO intelliinterview;
\c intelliinterview
CREATE EXTENSION vector;
```

Update `database_url` in `backend/app/config.py` if your credentials differ, then create tables:

```bash
python -m app.init_db
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

API docs: http://localhost:8080/docs

### 3. Frontend

```bash
cd ui
npm install
npm run dev
```

UI: http://localhost:5173

## Initial modules (Week 2 scaffold)

- **Health API** — `GET /api/health`
- **Auth API** — register/login with JWT and Recruiter/Candidate roles
- **Database models** — users, job specifications, candidate CVs
- **Document parser service** — Apache Tika wrapper for PDF/DOCX extraction
- **UI shell** — landing page with recruiter and candidate entry points

## Planned modules

1. CV & job-spec upload with gap analysis (pgvector RAG)
2. AI + recruiter question planning (GPT-4o)
3. Live AI interview session (text + voice)
4. Structured evaluation reports

## Testing

```bash
cd backend
pytest
```

Tests use an in-memory SQLite database and do not require PostgreSQL.
