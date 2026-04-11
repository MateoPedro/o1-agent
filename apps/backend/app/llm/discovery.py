import json
from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "speaking_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding open speaking opportunities at tech events.

Search for currently open calls for speakers, panelists, or workshop presenters at conferences, summits, meetups, and online events relevant to these domains:
- AI agents and agentic systems
- Age verification and child safety online
- Model Context Protocol (MCP)
- AI safety
- Social media regulation and compliance
- Software engineering (production systems, eng culture, career growth, big tech)
- Immigration and breaking into tech as a foreigner (international student → US tech career)

Location preference: Bay Area (San Francisco, San Jose, Berkeley) or virtual/remote events. Include global events if highly relevant, but flag the location clearly — it will be factored into scoring.

For each open call you find, return structured data using the return_opportunities tool. Include:
- Event name and host organization
- Host domain (website URL of the org)
- Event format: conference, meetup, panel, workshop, or online
- Location: city name or "virtual"
- Topic tags (pick 2-5 relevant tags)
- Deadline (ISO date string YYYY-MM-DD if known, otherwise null)
- Requirements: what the event asks for (abstract length, bio, topics, etc.)
- Effort to apply: low (< 30 min), medium (30–90 min), or high (> 90 min)
- URL to the speaker application or call for speakers page

Prioritize events with clear professional recognition, named speaker credits, and international or national reach.
Return up to 10 results."""


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
                            "deadline": {"type": ["string", "null"]},
                            "requirements": {"type": "string"},
                            "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                            "url": {"type": "string"},
                        },
                        "required": ["event_name", "host_organization", "host_domain", "event_format", "location", "topic_tags", "requirements", "effort", "url"],
                    },
                }
            },
            "required": ["opportunities"],
        },
    }

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8096,
        tools=[
            {"type": "web_search_20250305", "name": "web_search"},
            return_tool,
        ],
        messages=[{"role": "user", "content": prompt_body}],
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
