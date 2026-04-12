from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Opportunity, AuditLog
from app.profile.loader import load_profile

client = Anthropic(api_key=settings.anthropic_api_key)

PLAN_TOOL = {
    "name": "create_action_plan",
    "description": "Create a detailed action plan for pursuing this speaking opportunity.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "Ordered list of concrete next steps to pursue this opportunity.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "task": {"type": "string", "description": "Short action title (under 10 words)"},
                        "detail": {"type": "string", "description": "Specific instructions: where to go, what to fill in, what to say, by when."},
                        "completed": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "task", "detail", "completed"],
                },
            },
            "email_drafts": {
                "type": "array",
                "description": "Ready-to-send emails. Only include if direct outreach is needed (no public form). Leave empty for standard CFP form submissions.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "to": {"type": "string", "description": "Recipient email if known, otherwise empty string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string", "description": "Full email body, personalized and ready to send"},
                        "sent": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "to", "subject", "body", "sent"],
                },
            },
            "content_outline": {
                "type": "object",
                "properties": {
                    "suggested_angle": {
                        "type": "string",
                        "description": "1–2 sentences on the specific angle that would resonate most with this event's audience given the speaker's background.",
                    },
                    "story_modules": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Names of the story modules from the profile that are most relevant (australia_enforcement, teen_accounts, state_compliance, mcp_migration).",
                    },
                    "title_ideas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "3 concrete talk title options, each taking a different angle.",
                    },
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "4–6 specific bullet points the talk should cover, grounded in the speaker's actual work.",
                    },
                },
                "required": ["suggested_angle", "story_modules", "title_ideas", "key_points"],
            },
        },
        "required": ["todos", "email_drafts", "content_outline"],
    },
}


def create_action_plan(opp: Opportunity, db: Session) -> dict:
    profile = load_profile()

    story_modules_text = "\n".join(
        f"- {name}: {mod['summary']}"
        for name, mod in profile["story_modules"].items()
    )

    prompt = f"""You are creating an action plan to help a software engineer pursue a speaking opportunity as part of an O-1A immigration petition.

Speaker profile:
- Role: {profile['bio']['short']}
- Full bio: {profile['bio']['full']}
- Key achievements: {chr(10).join('  - ' + a for a in profile['achievements'])}
- Story modules available:
{story_modules_text}
- Talk topic seeds: {', '.join(profile['talk_topic_seeds'])}

Opportunity:
- Host: {opp.host} ({opp.host_domain})
- Type: {opp.type}
- Location: {opp.location}
- Topic tags: {', '.join(opp.topic_tags)}
- Deadline: {opp.deadline} ({opp.deadline_status})
- Event date: {opp.event_date}
- Requirements: {opp.requirements}
- Effort: {opp.effort} — {opp.effort_rationale}
- Source URL: {opp.source_url}

Create a practical action plan using the create_action_plan tool. Be specific and actionable — reference the actual URLs, deadlines, and requirements above. The todos should be in the right order to execute. Only include email drafts if direct outreach is needed (i.e. no public submission form exists). The content outline should be tailored to this specific event's audience."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        tools=[PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_action_plan"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "action_planning", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_action_plan":
            return block.input

    return {"todos": [], "email_drafts": [], "content_outline": {}}
