# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

An always-on agent that continuously discovers, scores, drafts, and tracks immigration-relevant opportunities (judging, talks, memberships, publications) to build an O1/EB1 USCIS case. The full loop: discover → score → draft → approve → submit → track → log evidence.

## Tech stack

| Layer | Technology |
|---|---|
| Backend runtime | Python 3.11+ |
| API | FastAPI |
| Background jobs | Celery + Redis |
| Scraping | Playwright (JS-heavy), httpx + BeautifulSoup4 (static) |
| LLM | Anthropic Claude API (structured outputs via tool use) |
| Database | SQLite (dev) → PostgreSQL (prod) via SQLAlchemy ORM + Alembic |
| Email | Gmail API (OAuth2) |
| Profile config | YAML flat files (version-controlled) |
| Frontend | Streamlit (MVP) → Next.js |

The backend lives in `apps/backend/` (Python/FastAPI) and the frontend in `apps/frontend/`.

## Commands

```bash
# Root — run all workspaces
npm run dev
npm run build

# Backend (from apps/backend/)
python -m uvicorn app.main:app --reload
celery -A app.worker worker --loglevel=info
celery -A app.worker beat --loglevel=info      # cron scheduler

# Database migrations (Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Frontend (from apps/frontend/)
npm run dev
```

## Architecture

The system has four layers:

### Layer 1 — Discovery (Celery beat, runs daily)
Scraper workers fetch raw opportunity data from public sources. Each has its own class:
- `HackathonScraper` — Devpost, Lablab, Devfolio (open judging applications)
- `CFPScraper` — Sessionize, Papercall, individual conference sites
- `AssociationScraper` — IEEE, ACM, AI/ML professional org membership pages
- `WritingOpsScraper` — "Write for us" pages at tech publications

After scraping, an LLM call (Claude, structured output via tool use) normalizes each raw blob into a typed `Opportunity` Pydantic model. All LLM prompts + responses are written to the `audit_log` table with the opportunity ID.

### Layer 2 — Reasoning (LLM micro-agents)
Four specialized LLM components, each with its own system prompt — not one monolithic agent:
- **Normalizer** — raw scrape → typed `Opportunity`
- **Scoring engine** — returns `{fit, prestige, evidence, effort}` float vector + rationale; `priority_score` is a tunable weighted sum
- **Drafting engine** — type-specific prompts per opportunity type (judge application, CFP abstract, membership statement, blog pitch)
- **Criteria mapper** — maps each opportunity to USCIS criteria (judging / authorship / membership / leading role / original contributions)

The static user profile (bio variants, project story modules, talk topic seeds, domain constraints) is a flat YAML file, version-controlled, not a DB table.

### Layer 3 — Action
- **Opportunity inbox** — `GET /inbox` returns top-N opportunities by `priority_score`, capped by a configurable weekly max
- **Submission engine** — two paths, both gated behind `approved_at`:
  - Email path via Gmail API (logs `Message-Id` for reply threading)
  - Form path via Playwright headless filler (shows screenshot before submitting)
- **Outcome tracker** — Celery periodic task polls Gmail for replies to agent-initiated threads; LLM classifier categorizes: `accepted / rejected / more-info-needed / no-reply`
- **Evidence logger** — when an opportunity is marked `completed`, creates a structured `EvidenceEntry` mapped to USCIS criteria, exportable as criterion-filtered Markdown

### Layer 4 — Storage
```sql
opportunities   -- discovered + scored + status lifecycle
drafts          -- generated content, bio_variant_used, story_module_used, approved_at
evidence        -- completed activities mapped to USCIS criteria
audit_log       -- every outbound payload + every LLM call, with timestamps
```

Status lifecycle for opportunities: `discovered → drafted → approved → submitted → accepted | rejected → completed`

## Hard rules (never relaxed)

- **No automatic submissions.** `approved_at` must be set before any outbound action. This is enforced at the API layer, not just the UI.
- **All LLM calls are logged** with their opportunity ID to `audit_log`.
- **Gmail integration is narrowly scoped** — only agent-initiated threads, never the full inbox.
- **Playwright form filler always shows a screenshot** for approval before submitting.
- **No internal/employer data** — scrapers only touch public sources.

## Implementation plan

The build is structured in 4 slices, each adding a new opportunity vertical on top of the shared core loop.

### Slice 1 — CFP / Talk vertical (days 1–21) ← start here
Validates the full core loop end-to-end. Chosen first because CFP submissions (invited speaker) produce strong USCIS evidence (`original contributions` + `leading role`) and the draft assets (title, abstract, bio) are reusable across many events.

| Phase | Days | Deliverable |
|---|---|---|
| Foundation | 1–3 | Repo, FastAPI `/health`, SQLite schema, Celery+Redis, Gmail OAuth2 |
| CFP Discovery | 4–7 | `CFPScraper` for Sessionize + Papercall feeding real opportunities into DB |
| Scoring + Inbox | 8–11 | Scoring engine + `GET /inbox` + Streamlit inbox UI |
| Talk Drafting + Approval | 12–15 | Abstract + bio drafter, `approved_at` gate enforced at API layer |
| Submission + Tracking | 16–18 | Gmail send + Playwright form filler + outcome tracker |
| Hardening | 19–21 | Error handling, deadline filter, ops runbook |

**Phase 1 exit criteria:** repo boots, SQLite schema created on startup, YAML profile loads, Celery processes a dummy task, Gmail token refreshes programmatically.

### Slice 2 — Judging vertical
`HackathonScraper` for Devpost + Lablab. Judging opportunities may already be lined up manually, so the scraper adds automation on top of an existing flow.

### Slice 3 — Memberships + evidence logger (weeks 6–7)
`AssociationScraper` (IEEE, ACM, curated AI/ML orgs), membership statement drafter, and the evidence logger with criterion-filtered Markdown export.

### Slice 4 — Feedback loop (week 8+)
Conversion metrics tracking (discovered → applied → accepted per source), scorer weight tuning, draft style improvement from acceptance patterns.

**Deferred:** `WritingOpsScraper`, Postgres migration (when concurrent workers needed), Next.js frontend (Streamlit is the MVP UI).

## Reference docs

- [Functionalities](https://www.notion.so/3332a083c9f7805c9eafd214ef2657b6) — full feature spec (opportunity discovery, scoring, inbox, drafting, submission, outcome tracking, evidence logging, feedback loop)
- [Technical spec](https://www.notion.so/3332a083c9f7811a8a39ff138837ed1a) — architecture diagram, full data model, key design decisions
- [Execution Plan](https://www.notion.so/3342a083c9f78162a6b6cf49df6cb2c7) — phased task checklist with exit criteria per phase
