import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "speaking_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding open speaking opportunities at tech events.

The beneficiary is a Software Engineer IC4 at Meta Platforms (~2 years experience). Key background:
- Built compliance systems for Australia's world-first social media Under-16 law (~544K account actions across Instagram, Facebook, Threads) — already covered by TIME, CNBC, PBS NewsHour, making this a proven newsworthy story
- Engineered anti-circumvention systems protecting 50M+ US teenagers on Instagram and Facebook — covered by Washington Post, Fox News
- Migrated 60+ agentic AI tools to MCP at Meta, improving production AI response latency 20%
- Promoted IC3→IC4 in under a year (typical timeline: 2–3 years)
- From France, navigated F-1 visa → US tech career at Meta
Domains: AI agents, MCP, agentic systems, age verification, child safety, social media regulation, software engineering culture, immigration/breaking into US tech as a foreigner.

Search broadly for currently open calls for speakers, panelists, or workshop presenters at conferences, summits, meetups, and online events where this profile would be a strong fit. Do not limit yourself to events you already know — use web search to find CFPs currently open or closing soon. Look across:

- **AI/ML and developer conferences** with open CFPs (AI agents, LLM tooling, MCP, agentic systems, production AI)
- **Child safety, social media policy, and digital rights events** — the Australia enforcement work is directly relevant and nationally covered
- **Software engineering and big tech culture events** (eng career growth, IC promotions, production systems)
- **Immigration and international career events** (F-1 to full-time, breaking into US tech as a foreigner)
- **Meetups and online events** — lower prestige but faster to get accepted; useful for building a speaking record

Location preference: Bay Area (San Francisco, San Jose, Berkeley) or virtual/remote. Include international events if highly relevant — flag the location clearly, it will be factored into scoring.

For each open call you find, return structured data using the return_opportunities tool. Include:
- Event name and host organization
- Host domain
- Event format: conference, meetup, panel, workshop, or online
- Location: city name or "virtual"
- Topic tags (2–5 relevant tags)
- Application deadline (ISO date YYYY-MM-DD if known, otherwise null)
- Deadline status: "specific" if hard cutoff known, "rolling" if no fixed cutoff, "unknown" if unclear
- Event date (ISO date YYYY-MM-DD when the event takes place, null if unknown)
- Requirements: what the event asks for (abstract length, bio, topics, format, etc.)
- Effort: low (<30 min), medium (30–90 min), high (>90 min), plus a one-sentence rationale
- URL to the speaker application or CFP page

Prioritize events with named speaker credits, professional recognition, and national or international reach. Surface smaller or niche events too — scoring will filter them.
Return up to 12 results."""


def get_active_prompt(db: Session) -> tuple[str, int]:
    """Returns (prompt_body, prompt_id). Seeds default if none exists."""
    prompt = (
        db.query(Prompt)
        .filter_by(name=DEFAULT_PROMPT_NAME, is_active=True)
        .order_by(Prompt.version.desc())
        .first()
    )
    if not prompt:
        prompt = Prompt(
            name=DEFAULT_PROMPT_NAME,
            version=DEFAULT_PROMPT_VERSION,
            body=DEFAULT_PROMPT_BODY,
            is_active=True,
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
    return prompt.body, prompt.id


def discover_speaking_opportunities(db: Session) -> list[dict]:
    prompt_body, prompt_id = get_active_prompt(db)

    return_tool = {
        "name": "return_opportunities",
        "description": "Return the list of speaking opportunities found via web search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "opportunities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event_name": {"type": "string"},
                            "host_organization": {"type": "string"},
                            "host_domain": {"type": "string"},
                            "event_format": {"type": "string", "enum": ["conference", "meetup", "panel", "workshop", "online"]},
                            "location": {"type": "string"},
                            "topic_tags": {"type": "array", "items": {"type": "string"}},
                            "deadline": {"type": ["string", "null"], "description": "Application deadline as ISO date YYYY-MM-DD, or null"},
                            "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"], "description": "specific = hard cutoff date known; rolling = no fixed deadline; unknown = couldn't determine"},
                            "event_date": {"type": ["string", "null"], "description": "Date the event takes place as ISO date YYYY-MM-DD, or null if unknown/recurring"},
                            "requirements": {"type": "string"},
                            "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                            "effort_rationale": {"type": "string", "description": "One sentence explaining why this effort level was assigned."},
                            "url": {"type": "string"},
                        },
                        "required": ["event_name", "host_organization", "host_domain", "event_format", "location", "topic_tags", "deadline_status", "requirements", "effort", "url"],
                    },
                }
            },
            "required": ["opportunities"],
        },
    }

    dated_prompt = (
        f"Today's date is {date.today().isoformat()}. "
        f"Only return opportunities whose event date and application deadline are both in the future (after today). "
        f"Do not return events that have already happened or deadlines that have passed.\n\n"
        f"{prompt_body}"
    )

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8096,
        tools=[
            {"type": "web_search_20250305", "name": "web_search"},
            return_tool,
        ],
        messages=[{"role": "user", "content": dated_prompt}],
    )

    # Log LLM call
    db.add(AuditLog(
        direction="llm",
        payload={"prompt_name": DEFAULT_PROMPT_NAME, "prompt_body": prompt_body, "model": "claude-opus-4-5"},
        response={"stop_reason": response.stop_reason, "content_blocks": len(response.content)},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    # Extract return_opportunities tool call
    for block in response.content:
        if block.type == "tool_use" and block.name == "return_opportunities":
            return block.input.get("opportunities", [])

    return []
