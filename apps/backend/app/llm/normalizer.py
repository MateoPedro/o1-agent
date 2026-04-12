from datetime import datetime, date
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import AuditLog
from app.schemas import OpportunityCreate

client = Anthropic(api_key=settings.anthropic_api_key)

NORMALIZE_TOOL = {
    "name": "save_opportunity",
    "description": "Save a normalized speaking opportunity to the database.",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["judge", "member", "talk", "blog", "article"]},
            "host": {"type": "string"},
            "host_domain": {"type": "string"},
            "topic_tags": {"type": "array", "items": {"type": "string"}},
            "deadline": {"type": ["string", "null"], "description": "Application deadline as ISO date YYYY-MM-DD or null"},
            "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"], "description": "specific = hard cutoff date known; rolling = no fixed deadline; unknown = couldn't determine"},
            "event_date": {"type": ["string", "null"], "description": "Date the event takes place as ISO date YYYY-MM-DD or null"},
            "requirements": {"type": "string"},
            "effort": {"type": "string", "enum": ["low", "medium", "high"]},
            "effort_rationale": {"type": ["string", "null"], "description": "One sentence explaining why this effort level was assigned."},
            "source_url": {"type": "string"},
            "raw_text": {"type": "string"},
            "location": {"type": ["string", "null"]},
        },
        "required": ["type", "host", "host_domain", "topic_tags", "deadline_status", "requirements", "effort", "source_url", "raw_text"],
    },
}


def normalize_opportunity(raw: dict, db: Session) -> OpportunityCreate | None:
    prompt = f"""Normalize this speaking opportunity into a structured record.
Classify it as type "talk" unless it's clearly something else.
Extract all available fields. If deadline is missing set it to null.

Raw opportunity:
{raw}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        tools=[NORMALIZE_TOOL],
        tool_choice={"type": "tool", "name": "save_opportunity"},
        messages=[{"role": "user", "content": prompt}],
    )

    # Log LLM call
    db.add(AuditLog(
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "raw_input": raw},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "save_opportunity":
            data = block.input

            def parse_date(val: str | None) -> date | None:
                if not val:
                    return None
                try:
                    return date.fromisoformat(val)
                except ValueError:
                    return None

            deadline = parse_date(data.get("deadline"))
            event_date = parse_date(data.get("event_date"))

            return OpportunityCreate(
                type=data.get("type", "talk"),
                host=data["host"],
                host_domain=data["host_domain"],
                topic_tags=data["topic_tags"],
                deadline=deadline,
                deadline_status=data.get("deadline_status", "unknown"),
                event_date=event_date,
                requirements=data["requirements"],
                effort=data["effort"],
                effort_rationale=data.get("effort_rationale"),
                source_url=data["source_url"],
                raw_text=data["raw_text"],
                location=data.get("location"),
            )

    return None
