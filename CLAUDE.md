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
| Frontend | Next.js 14 App Router + TypeScript + Tailwind CSS |

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

### Layer 1 — Discovery (Celery beat)
Discovery is LLM-driven — no custom scrapers. Claude (with web search enabled) runs a versioned discovery prompt stored in the `prompts` DB table and returns structured opportunity objects directly via tool use. Adding a new source type = updating the prompt, not writing a parser.

**Cron schedule (America/Los_Angeles):**
- `discover_speaking_ops` — Fridays at 4:00 PM PT
- `poll_outcomes` — Daily at 5:00 PM PT

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
- **Opportunity inbox** — `GET /inbox` returns top-N opportunities by `priority_score`, capped by `weekly_max_actions` in profile.yaml. Filters out past deadlines and past event dates.
- **Action planner** — `POST /opportunities/{id}/plan` triggers a Haiku LLM call that generates a structured action plan: todos, email drafts, and a content outline (suggested angle, title ideas, key points, story modules to reference). Status moves to `in_progress`.
- **Submission engine** — email path via Gmail API (logs `Message-Id` + `thread_id` for reply threading). Form-based submissions are handled as manual todos in the action plan.
- **Outcome tracker** — `poll_outcomes` Celery task polls Gmail for replies; Haiku classifier categorizes: `accepted / rejected / more_info_needed` with a reply summary.
- **Evidence logger** — `POST /opportunities/{id}/log-evidence` creates an `Evidence` entry mapped to USCIS criteria, then automatically generates a new story module in `profile.yaml` via Haiku and re-seeds it as a second evidence entry (source=`profile`). Exportable as criterion-filtered Markdown.

### Layer 4 — Storage
```sql
opportunities   -- discovered + scored + status lifecycle
drafts          -- generated content, bio_variant_used, story_module_used, approved_at
evidence        -- completed activities mapped to USCIS criteria
audit_log       -- every outbound payload + every LLM call, with timestamps
```

Status lifecycle for opportunities: `discovered → in_progress → submitted → accepted | rejected → completed`

## Hard rules (never relaxed)

- **No automatic submissions.** The Send Email button is always a manual user action — nothing goes outbound without a click. `approved_at` column exists in the schema but the gate is not currently enforced at the API layer (deliberate decision: single user, manual workflow makes the extra step redundant friction).
- **All LLM calls are logged** with their opportunity ID to `audit_log`.
- **Gmail integration is narrowly scoped** — only agent-initiated threads, never the full inbox.
- **No internal/employer data** — scrapers only touch public sources.

## Implementation plan

The build is structured in 5 slices, each adding a new opportunity vertical on top of the shared core loop. All discovery is LLM-driven (Claude web search + versioned prompts) — no custom scrapers.

### Slice 1 — Speaking vertical ✅ Done
Validates the full core loop end-to-end. Speaking opportunities (invited speaker) produce strong USCIS evidence (`original contributions` + `leading role`) and the draft assets (title, abstract, bio) are reusable across many events.

| Phase | Status | Deliverable |
|---|---|---|
| Foundation | ✅ Done | Repo, FastAPI `/health`, SQLite schema, Celery+Redis, YAML profile |
| Speaking Discovery | ✅ Done | `discover_speaking_ops` Celery task — Claude web search → typed `Opportunity` objects in DB, prompt versioned in `prompts` table |
| Scoring + Inbox | ✅ Done | Scoring engine, `GET /inbox` with deadline + event_date filters, Next.js Inbox UI |
| Action Planning | ✅ Done | Haiku planner generates todos + email drafts + content outline; Pipeline page (In Progress / Accepted / Completed tabs) |
| Submission + Tracking | ✅ Done | Gmail send via OAuth2, `poll_outcomes` task, Haiku reply classifier (accepted / rejected / more_info_needed + summary) |
| Evidence + Profile | ✅ Done | Evidence page grouped by USCIS criterion, Markdown export, profile.yaml auto-update on log-evidence, incremental re-seed |
| Cron schedule | ✅ Done | Discovery Fridays 4pm PT, polling daily 5pm PT (America/Los_Angeles, pytz) |

### Slice 2 — Judging vertical
`discover_judging_ops` — hackathon judge/mentor roles, program committees, accelerator demo days, grant panels. Formally invited roles prioritized. Judging opportunities may already be lined up manually; the discovery task adds automation on top.

### Slice 3 — Publishing vertical
`discover_publishing_ops` — guest blog posts, tech magazines, practitioner "research" outlets, scholarly article calls. Target outlets: Towards Data Science, The Pragmatic Engineer, IEEE Spectrum, ACM Queue, and similar. Maps to USCIS `authorship` criterion.

### Slice 4 — Memberships + evidence logger
`discover_membership_ops` — IEEE, ACM, curated AI/ML professional org membership pages. Membership statement drafter. Evidence logger with criterion-filtered Markdown export.

### Slice 5 — Feedback loop
Conversion metrics tracking (discovered → applied → accepted per source), scorer weight tuning, discovery prompt refinement from acceptance patterns.

**Deferred:** Postgres migration (when concurrent workers needed). Next.js frontend is already live — Streamlit was skipped.

## Reference docs

- [Functionalities](https://www.notion.so/3332a083c9f7805c9eafd214ef2657b6) — full feature spec (opportunity discovery, scoring, inbox, drafting, submission, outcome tracking, evidence logging, feedback loop)
- [Technical spec](https://www.notion.so/3332a083c9f7811a8a39ff138837ed1a) — architecture diagram, full data model, key design decisions
- [Execution Plan](https://www.notion.so/3342a083c9f78162a6b6cf49df6cb2c7) — phased task checklist with exit criteria per phase
