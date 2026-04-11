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
            "deadline": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null"},
            "requirements": {"type": "string"},
            "effort": {"type": "string", "enum": ["low", "medium", "high"]},
            "source_url": {"type": "string"},
            "raw_text": {"type": "string"},
            "location": {"type": ["string", "null"]},
        },
        "required": ["type", "host", "host_domain", "topic_tags", "requirements", "effort", "source_url", "raw_text"],
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
            # Parse deadline string → date object
            deadline = None
            if data.get("deadline"):
                try:
                    deadline = date.fromisoformat(data["deadline"])
                except ValueError:
                    pass
            return OpportunityCreate(
                type=data.get("type", "talk"),
                host=data["host"],
                host_domain=data["host_domain"],
                topic_tags=data["topic_tags"],
                deadline=deadline,
                requirements=data["requirements"],
                effort=data["effort"],
                source_url=data["source_url"],
                raw_text=data["raw_text"],
                location=data.get("location"),
            )

    return None
