# Backend

Python/FastAPI backend for o1-agent. Runs the scraper workers, LLM reasoning pipeline, submission engine, and outcome tracker.

## Stack

- **FastAPI** — REST API (`/health`, `/inbox`, `/drafts`)
- **Celery + Redis** — background jobs (daily scrape cron, outcome polling)
- **SQLAlchemy + Alembic** — ORM + migrations (SQLite dev, Postgres prod)
- **Anthropic Claude API** — normalizer, scoring engine, drafting engine, criteria mapper
- **Playwright** — headless form submission
- **Gmail API (OAuth2)** — email send + reply monitoring

## Getting Started

```bash
pip install -r requirements.txt

# Run DB migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start Celery worker
celery -A app.worker worker --loglevel=info

# Start Celery beat (cron scheduler)
celery -A app.worker beat --loglevel=info
```

## Environment

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./o1agent.db
```

## Key modules (planned)

```
app/
├── main.py              # FastAPI app + routes
├── worker.py            # Celery app + beat schedule
├── models.py            # SQLAlchemy models (opportunities, drafts, evidence, audit_log)
├── scrapers/
│   ├── cfp.py           # CFPScraper — Sessionize, Papercall
│   ├── hackathon.py     # HackathonScraper — Devpost, Lablab
│   ├── association.py   # AssociationScraper — IEEE, ACM
│   └── writing.py       # WritingOpsScraper
├── llm/
│   ├── normalizer.py    # Raw scrape → Opportunity object
│   ├── scorer.py        # {fit, prestige, evidence, effort} vector
│   ├── drafter.py       # Type-specific draft generation
│   └── criteria.py      # Maps opportunity → USCIS criteria
├── actions/
│   ├── inbox.py         # Priority queue logic
│   ├── email.py         # Gmail send via OAuth2
│   ├── forms.py         # Playwright form filler
│   └── tracker.py       # Outcome polling + classifier
└── profile/             # YAML profile loader (bio variants, story modules)
```
