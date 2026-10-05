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
.venv\Scripts\activate
pytest
```

Tests use an in-memory SQLite database and do not require PostgreSQL.

```bash
cd ui
npm test
```

Frontend tests run with Vitest and React Testing Library.

## Semantic retrieval threshold calibration

Gap analysis rescues lexical gaps using CV-chunk embeddings (`app/services/embeddings.py`)
when `settings.semantic_match_threshold` (default `0.45`) is cleared by cosine similarity
against a canonical skill phrase. That default is a starting guess, not a calibrated value.
To recompute it from real CV/job data:

```bash
cd backend
.venv\Scripts\activate
python scripts/calibrate_semantic_threshold.py path/to/cv.txt path/to/job_spec.txt
```

This prints every lexical gap skill against its best-matching CV passage with the
similarity score, and a suggested threshold at the midpoint of the largest gap between
consecutive scores. Requires a real `openai_api_key` in `app/config.py` - it calls the
OpenAI embeddings endpoint directly and makes no database calls.