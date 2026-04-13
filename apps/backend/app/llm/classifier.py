from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

CLASSIFY_TOOL = {
    "name": "classify_reply",
    "description": "Classify an email reply to a speaker application.",
    "input_schema": {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": ["accepted", "rejected", "more_info_needed"],
                "description": (
                    "accepted = they want you to speak / confirmed your spot; "
                    "rejected = declined, no slot available, not a fit; "
                    "more_info_needed = they're asking follow-up questions or requesting additional materials."
                ),
            },
            "summary": {
                "type": "string",
                "description": (
                    "One sentence. For more_info_needed: describe exactly what they're asking for. "
                    "For accepted/rejected: brief summary of their response."
                ),
            },
        },
        "required": ["classification", "summary"],
    },
}


def classify_reply(reply_text: str, opportunity_host: str, db: Session, opportunity_id: int) -> tuple[str, str]:
    """Returns (classification, summary)."""
    prompt = f"""Classify this email reply to a speaker application sent to {opportunity_host}.

Reply:
{reply_text[:2000]}

Use the classify_reply tool."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_reply"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opportunity_id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "reply_classification", "opportunity_id": opportunity_id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_reply":
            return block.input["classification"], block.input["summary"]

    return "more_info_needed", "Could not classify reply."
