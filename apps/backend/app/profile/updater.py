"""Update profile.yaml with a new story module when an opportunity is completed."""
import re
from datetime import datetime
from pathlib import Path
import yaml
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Opportunity, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)
PROFILE_PATH = Path(__file__).parent.parent.parent / "profile.yaml"

MODULE_TOOL = {
    "name": "create_story_module",
    "description": "Create a story module for the completed opportunity to add to the profile.",
    "input_schema": {
        "type": "object",
        "properties": {
            "module_key": {
                "type": "string",
                "description": "Unique snake_case key for this module, e.g. talk_ai_agents_conf_2026. Should not clash with existing keys.",
            },
            "title": {
                "type": "string",
                "description": "Short descriptive title, e.g. 'Speaker — AI Agents Conference 2026'",
            },
            "summary": {
                "type": "string",
                "description": "2-3 sentences describing what was done, why it matters for the O-1A case, and any concrete metrics or outcomes.",
            },
            "uscis_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Short criterion names that apply. Use exactly these values: "
                    "'critical role at distinguished organization', "
                    "'published material about the person's work', "
                    "'original contributions of major significance', "
                    "'judging the work of others', "
                    "'nationally recognized prizes or awards', "
                    "'membership in selective associations', "
                    "'authorship of scholarly articles', "
                    "'high salary'"
                ),
            },
        },
        "required": ["module_key", "title", "summary", "uscis_criteria"],
    },
}


def update_profile_with_opportunity(opp: Opportunity, db: Session) -> str | None:
    """
    Generate a story module for a completed opportunity and append it to profile.yaml.
    Returns the module_key if added, None if skipped (e.g. already exists).
    """
    with open(PROFILE_PATH) as f:
        profile = yaml.safe_load(f)

    existing_keys = set(profile.get("story_modules", {}).keys())

    # Build context from opportunity
    criteria_text = ""
    if opp.uscis_criteria:
        criteria_text = "\n".join(
            f"  - {c['criterion']} ({c['strength']}): {c['rationale']}"
            for c in opp.uscis_criteria
        )

    prompt = f"""A software engineer just completed a speaking/judging/activity opportunity.
Add it as a story module to their O-1A immigration profile.

Completed opportunity:
- Host: {opp.host} ({opp.host_domain})
- Type: {opp.type}
- Location: {opp.location}
- Topic tags: {', '.join(opp.topic_tags)}
- Event date: {opp.event_date}
- Score rationale: {opp.score_rationale}
- USCIS criteria mapped:
{criteria_text}

Existing module keys (do not reuse): {', '.join(existing_keys)}

Generate a story module using the create_story_module tool."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=[MODULE_TOOL],
        tool_choice={"type": "tool", "name": "create_story_module"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "profile_update", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_story_module":
            data = block.input
            module_key = _safe_key(data["module_key"], existing_keys)

            new_module = {
                "title": data["title"],
                "summary": data["summary"],
                "uscis_criteria": data["uscis_criteria"],
            }
            if opp.event_date:
                new_module["date"] = str(opp.event_date)
            if opp.source_url:
                new_module["url"] = opp.source_url

            profile.setdefault("story_modules", {})[module_key] = new_module

            with open(PROFILE_PATH, "w") as f:
                yaml.dump(profile, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            return module_key

    return None


def _safe_key(key: str, existing: set[str]) -> str:
    """Ensure the key is snake_case and doesn't clash with existing keys."""
    key = re.sub(r"[^a-z0-9_]", "_", key.lower()).strip("_")
    if key not in existing:
        return key
    i = 2
    while f"{key}_{i}" in existing:
        i += 1
    return f"{key}_{i}"
