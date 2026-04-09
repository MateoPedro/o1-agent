# o1-agent

An always-on agent that discovers, scores, drafts, and tracks immigration-relevant opportunities (judging, talks, memberships, publications) to build an O1/EB1 USCIS case.

Full loop: **discover → score → draft → approve → submit → track → log evidence**

## Structure

```
o1-agent/
├── apps/
│   ├── backend/    # Python/FastAPI + Celery workers
│   └── frontend/   # Streamlit inbox UI (→ Next.js later)
├── packages/       # Shared utilities
└── docs/           # Documentation
```

## Stack

- **Backend** — Python 3.11+, FastAPI, Celery + Redis, SQLAlchemy, Alembic
- **LLM** — Anthropic Claude API (structured outputs via tool use)
- **Scraping** — Playwright (JS-heavy), httpx + BeautifulSoup4 (static)
- **Email** — Gmail API (OAuth2)
- **Database** — SQLite (dev) → PostgreSQL (prod)
- **Frontend** — Streamlit (MVP)

## Getting Started

```bash
# Backend
cd apps/backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Celery worker + scheduler
celery -A app.worker worker --loglevel=info
celery -A app.worker beat --loglevel=info

# Frontend
cd apps/frontend
pip install -r requirements.txt
streamlit run app.py
```

## Build Plan

| Slice | Scope | Status |
|---|---|---|
| 1 | CFP / Talk vertical (full core loop) | In progress |
| 2 | Judging vertical (Devpost, Lablab) | Planned |
| 3 | Memberships + evidence logger | Planned |
| 4 | Feedback loop + scorer tuning | Planned |
