"""Discover podcast, newsletter, and media opportunities where the beneficiary can be featured."""
from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "media_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding media opportunities where a software engineer can be featured — podcasts, YouTube channels, newsletters, and journalists writing about them.

The USCIS O-1A criterion being targeted is: "Published material about the beneficiary in professional or major media."

The beneficiary is a Software Engineer IC4 at Meta Platforms (~2 years experience). Key background:
- Built compliance systems for Australia's world-first social media Under-16 law (~544K account actions across Instagram, Facebook, Threads) — covered by TIME, CNBC, PBS NewsHour
- Engineered anti-circumvention systems protecting 50M+ US teenagers on Instagram and Facebook — covered by Washington Post, Fox News
- Migrated 60+ agentic AI tools to MCP at Meta, improving production latency 20%
- Promoted IC3→IC4 in under a year at Meta (typical timeline: 2–3 years)
- From France, navigated F-1 visa → US tech career at a top company
Domains: AI agents, MCP, age verification, child safety, social media regulation, software engineering career, immigration into US tech.

Search broadly for active media outlets, podcast shows, and journalists where this profile would be a strong fit as a featured guest or story subject. Do not limit yourself to outlets you already know — use web search to find active shows and publications currently seeking guests or covering these topics. Look for:

**Podcasts and YouTube shows actively booking guests:**
- Tech and AI-focused shows (software engineering, AI agents, LLM tooling, MCP, agentic systems)
- Child safety, social media policy, and digital rights shows
- Career and immigration shows (breaking into US tech, international engineers, F-1 visa stories)
- Big tech insider / engineering culture shows

**Newsletters with guest contributor or interview slots:**
- Engineering and AI practitioner newsletters (e.g. The Pragmatic Engineer, TLDR, Software Engineering Daily, Import AI, The Batch)
- Policy and tech newsletters covering social media regulation and child safety
- Career/immigration newsletters for international engineers

**Journalists and publications actively covering these beats:**
- Reporters covering AI safety, age verification, social media regulation at major publications
- Tech trade press covering agentic AI and developer tooling
- Immigration and international career publications

For each opportunity, return structured data using the return_opportunities tool. Include:
- Outlet name and domain
- Platform type: podcast, youtube, newsletter, press, blog
- Audience size or reach if findable (e.g. "50K subscribers", "300K YouTube")
- Why this outlet is a strong fit for the beneficiary's story
- How to pitch: submission form URL, editor email format, guest booking page
- Deadline or response window if known
- Effort to pitch: low (<30 min), medium (30–90 min), high (>90 min), plus rationale
- Topic tags (2–4 relevant tags)

Return up to 12 results. Prioritize outlets with established audiences where coverage would constitute "major media" or recognized professional publications. Surface niche but credible outlets too — a focused newsletter with 30K engineers reading it can be stronger evidence than a generic blog with 1M casual readers."""

RETURN_TOOL = {
    "name": "return_opportunities",
    "description": "Return the list of media opportunities found via web search.",
    "input_schema": {
        "type": "object",
        "properties": {
            "opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event_name": {"type": "string", "description": "e.g. 'The Pragmatic Engineer Newsletter — Guest Interview'"},
                        "host_organization": {"type": "string", "description": "Outlet or show name"},
                        "host_domain": {"type": "string"},
                        "platform_type": {"type": "string", "enum": ["podcast", "youtube", "newsletter", "press", "blog"]},
                        "audience_size": {"type": ["string", "null"], "description": "e.g. '50K subscribers' or null if unknown"},
                        "fit_rationale": {"type": "string", "description": "1–2 sentences on why this outlet fits the beneficiary's story"},
                        "topic_tags": {"type": "array", "items": {"type": "string"}},
                        "deadline": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null"},
                        "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"]},
                        "requirements": {"type": "string", "description": "How to pitch: what to send, where, any format requirements"},
                        "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                        "effort_rationale": {"type": "string"},
                        "url": {"type": "string", "description": "Guest submission page, contact page, or pitch instructions URL"},
                    },
                    "required": [
                        "event_name", "host_organization", "host_domain", "platform_type",
                        "fit_rationale", "topic_tags", "deadline_status",
                        "requirements", "effort", "effort_rationale", "url",
                    ],
                },
            }
        },
        "required": ["opportunities"],
    },
}


def get_active_prompt(db: Session) -> tuple[str, int]:
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


def discover_media_opportunities(db: Session) -> list[dict]:
    prompt_body, prompt_id = get_active_prompt(db)

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8096,
        tools=[
            {"type": "web_search_20250305", "name": "web_search"},
            RETURN_TOOL,
        ],
        messages=[{"role": "user", "content": prompt_body}],
    )

    db.add(AuditLog(
        direction="llm",
        payload={"prompt_name": DEFAULT_PROMPT_NAME, "prompt_body": prompt_body, "model": "claude-opus-4-5"},
        response={"stop_reason": response.stop_reason, "content_blocks": len(response.content)},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "return_opportunities":
            return block.input.get("opportunities", [])

    return []
