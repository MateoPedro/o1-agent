"""Discover open membership application windows for selective professional associations."""
from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "membership_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding open application windows for selective professional memberships and recognition programs.

The USCIS O-1A criterion being targeted is: "Membership in associations that require outstanding achievements of their members as judged by recognized national or international experts."

The beneficiary is a Software Engineer IC4 at Meta Platforms (~2 years experience), specializing in age assurance infrastructure and agentic AI tooling. Key background: built compliance systems for Australia's world-first social media law (544K accounts), engineered anti-circumvention systems protecting 50M+ US teenagers, migrated 60+ agentic tools to MCP improving latency 20%, promoted IC3→IC4 in under a year. Domains: AI agents, MCP, age verification, child safety, social media regulation, software engineering.

Search broadly for selective memberships, fellowships, and recognition programs where this profile could be competitive. Do not limit yourself to well-known programs — look for:

- **Elevated grades in professional engineering/CS associations** (IEEE, ACM, AAAI, SIAM, and others) that require demonstrated excellence, peer nominations, or a selection committee
- **Annual recognition lists and fellowships** in tech, AI, or software engineering that are nationally or internationally recognized and selective (well-known programs but also niche ones you find through search)
- **AI/ML-specific fellowships or distinguished member programs** from organizations like Partnership on AI, AI Now Institute, MLCommons, or similar
- **Child safety, policy, or civic tech recognition programs** given the beneficiary's age assurance work
- **Industry cohort programs with selective admission** that confer recognized distinction, if they qualify as selective associations under O-1A standards

For each opportunity, assess whether the association genuinely requires outstanding achievements as judged by experts — that is the USCIS bar. Include opportunities even if eligibility is uncertain; scoring will filter them.

Return structured data using the return_opportunities tool. For each entry include:
- Organization name and host domain
- Membership grade or program name
- Whether nominators are required and how many
- Annual fee (if any)
- Eligibility criteria (what qualifications are required)
- Application window (when applications are open each year)
- Deadline (ISO date YYYY-MM-DD for the next upcoming deadline, or null)
- Deadline status: "specific" if hard cutoff known, "rolling" if ongoing, "unknown" if unclear
- Requirements: what the application asks for (personal statement, CV, publications list, etc.)
- Effort: low (<30 min), medium (30–90 min), high (>90 min), plus a one-sentence rationale
- URL to the application or nomination page

Return up to 12 results. Prioritize breadth — surface programs a typical candidate might not think to apply for."""

RETURN_TOOL = {
    "name": "return_opportunities",
    "description": "Return the list of membership opportunities found via web search.",
    "input_schema": {
        "type": "object",
        "properties": {
            "opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event_name": {"type": "string", "description": "e.g. 'IEEE Senior Member Application'"},
                        "host_organization": {"type": "string", "description": "e.g. 'IEEE'"},
                        "host_domain": {"type": "string", "description": "e.g. 'ieee.org'"},
                        "membership_grade": {"type": "string", "description": "e.g. 'Senior Member', 'Fellow', '30 Under 30'"},
                        "requires_nominators": {"type": "boolean"},
                        "nominator_count": {"type": ["integer", "null"], "description": "Number of nominators required, or null if not applicable"},
                        "annual_fee": {"type": ["string", "null"], "description": "e.g. '$150/year' or null"},
                        "eligibility_criteria": {"type": "string", "description": "Plain-language eligibility requirements"},
                        "application_window": {"type": ["string", "null"], "description": "e.g. 'January 1 – March 31 annually' or null if always open"},
                        "topic_tags": {"type": "array", "items": {"type": "string"}, "description": "2–4 relevant tags, e.g. ['AI', 'software engineering', 'IEEE']"},
                        "deadline": {"type": ["string", "null"], "description": "Next upcoming deadline as ISO date YYYY-MM-DD, or null"},
                        "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"]},
                        "requirements": {"type": "string", "description": "What the application asks for (personal statement, CV, endorsements, etc.)"},
                        "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                        "effort_rationale": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": [
                        "event_name", "host_organization", "host_domain", "membership_grade",
                        "requires_nominators", "eligibility_criteria", "topic_tags",
                        "deadline_status", "requirements", "effort", "effort_rationale", "url",
                    ],
                },
            }
        },
        "required": ["opportunities"],
    },
}


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


def discover_membership_opportunities(db: Session) -> list[dict]:
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
