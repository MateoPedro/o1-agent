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
Discovery is LLM-driven — no custom scrapers. Claude (with web search enabled) runs a versioned discovery prompt stored in the `prompts` DB table and returns structured opportunity objects directly via tool use. Adding a new source type = updating the prompt, not writing a parser.

Each opportunity vertical has its own discovery prompt:
- **Speaking** (`discover_speaking_ops`) — conferences, panels, workshops, meetups, online events. Domains: AI agents, age verification, MCP, AI safety, social media compliance, software engineering, immigration/breaking into tech. Location preference: Bay Area or virtual (location feeds into scoring, not hard-filtered).
- **Judging** (`discover_judging_ops`) — hackathon judge/mentor roles, program committees, accelerator demo days, grant panels. Formally invited roles prioritized over open applications.
- **Publishing** (`discover_publishing_ops`) — guest blog posts, tech magazines, practitioner "research" outlets, scholarly article calls. Outlets like Towards Data Science, The Pragmatic Engineer, IEEE Spectrum, ACM Queue.
- **Memberships** (`discover_membership_ops`) — IEEE, ACM, curated AI/ML professional org membership pages.

All LLM prompts + responses are written to the `audit_log` table. Discovery prompts are versioned in the `prompts` table and improve over time based on conversion metrics.

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

## Follow-up items (not yet built)

- **USCIS criteria mapping refinement** — current mapping is a simple deterministic function (talk → `original contributions` + `leading role`). Needs a pass to tighten wording against the actual USCIS O-1A criterion definitions, and to handle edge cases (e.g. a prestigious invited keynote may also support `critical role at distinguished organization`). No LLM needed — pure rules per opportunity type.

## Hard rules (never relaxed)

- **No automatic submissions.** `approved_at` must be set before any outbound action. This is enforced at the API layer, not just the UI.
- **All LLM calls are logged** with their opportunity ID to `audit_log`.
- **Gmail integration is narrowly scoped** — only agent-initiated threads, never the full inbox.
- **Playwright form filler always shows a screenshot** for approval before submitting.
- **No internal/employer data** — scrapers only touch public sources.

## Implementation plan

The build is structured in 5 slices, each adding a new opportunity vertical on top of the shared core loop. All discovery is LLM-driven (Claude web search + versioned prompts) — no custom scrapers.

### Slice 1 — Speaking vertical ← in progress
Validates the full core loop end-to-end. Speaking opportunities (invited speaker) produce strong USCIS evidence (`original contributions` + `leading role`) and the draft assets (title, abstract, bio) are reusable across many events.

| Phase | Status | Deliverable |
|---|---|---|
| Foundation | ✅ Done | Repo, FastAPI `/health`, SQLite schema, Celery+Redis, YAML profile |
| Speaking Discovery | ✅ Done | `discover_speaking_ops` Celery task — Claude web search → typed `Opportunity` objects in DB, prompt versioned in `prompts` table |
| Scoring + Inbox | Next | Scoring engine + `GET /inbox` + Streamlit inbox UI |
| Talk Drafting + Approval | Planned | Abstract + bio drafter, `approved_at` gate enforced at API layer |
| Submission + Tracking | Planned | Gmail send + Playwright form filler + outcome tracker |
| Hardening | Planned | Error handling, deadline filter, ops runbook |

### Slice 2 — Judging vertical
`discover_judging_ops` — hackathon judge/mentor roles, program committees, accelerator demo days, grant panels. Formally invited roles prioritized. Judging opportunities may already be lined up manually; the discovery task adds automation on top.

### Slice 3 — Publishing vertical
`discover_publishing_ops` — guest blog posts, tech magazines, practitioner "research" outlets, scholarly article calls. Target outlets: Towards Data Science, The Pragmatic Engineer, IEEE Spectrum, ACM Queue, and similar. Maps to USCIS `authorship` criterion.

### Slice 4 — Memberships + evidence logger
`discover_membership_ops` — IEEE, ACM, curated AI/ML professional org membership pages. Membership statement drafter. Evidence logger with criterion-filtered Markdown export.

### Slice 5 — Feedback loop
Conversion metrics tracking (discovered → applied → accepted per source), scorer weight tuning, discovery prompt refinement from acceptance patterns.

**Deferred:** Postgres migration (when concurrent workers needed), Next.js frontend (Streamlit is the MVP UI).

## Reference docs

- [Functionalities](https://www.notion.so/3332a083c9f7805c9eafd214ef2657b6) — full feature spec (opportunity discovery, scoring, inbox, drafting, submission, outcome tracking, evidence logging, feedback loop)
- [Technical spec](https://www.notion.so/3332a083c9f7811a8a39ff138837ed1a) — architecture diagram, full data model, key design decisions
- [Execution Plan](https://www.notion.so/3342a083c9f78162a6b6cf49df6cb2c7) — phased task checklist with exit criteria per phase
