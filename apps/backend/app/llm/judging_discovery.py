"""Discover hackathon judging, program committee, and evaluation panel opportunities."""
from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "judging_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding opportunities where a software engineer can serve as a judge, evaluator, or reviewer — hackathons, program committees, accelerator demo days, grant panels, and award committees.

The USCIS O-1A criterion being targeted: "Participation, either individually or on a panel, as a judge of the work of others in the same or an allied field."

The beneficiary is a Software Engineer IC4 at Meta Platforms (~2 years experience). Key background:
- Built compliance systems for Australia's world-first social media Under-16 law (~544K account actions across Instagram, Facebook, Threads) — covered by TIME, CNBC, PBS NewsHour
- Engineered anti-circumvention systems protecting 50M+ US teenagers on Instagram and Facebook — covered by Washington Post, Fox News
- Migrated 60+ agentic AI tools to MCP at Meta, improving production latency 20%
- Promoted IC3→IC4 in under a year at Meta (typical timeline: 2–3 years)
- From France, navigated F-1 visa → US tech career; mentors international engineers
- GitHub contributor; active in AI agents, MCP, and developer tooling ecosystems
Domains: AI agents, MCP, age verification, child safety, social media regulation, developer tools, software engineering career, immigration into US tech.

Search actively for judging and evaluation opportunities where this profile would qualify. Start with well-known networks and then go broader:

**Major hackathon networks (search these explicitly):**
- Major League Hacking (MLH) — official hackathon season schedule, judge applications, mentor roles
- Devpost — platform listing active hackathons seeking judges
- HackMIT, TreeHacks (Stanford), CalHacks (UC Berkeley), LA Hacks, SB Hacks — university flagship hackathons
- AI-specific hackathons: AI Agents Hackathon, Anthropic hackathons, OpenAI hackathons, LangChain builds

**Accelerator and demo day judging:**
- Y Combinator Demo Day panelist/mentor roles (batch applications)
- a16z, Sequoia, Founders Fund accelerator demo days
- Techstars, 500 Startups demo days
- AI-focused accelerators: AI2 Incubator, Radical Ventures, Conviction
- Social impact accelerators: FastForward, Echoing Green (tech for good angle)

**Conference program committees and paper reviews:**
- NeurIPS, ICML, ICLR, AAAI — reviewer/program committee applications (typically open 3–6 months before conference)
- ACL, EMNLP — NLP conferences (given AI agents work)
- WWW, TheWebConf — social media / web systems angle
- FAccT (Fairness, Accountability, Transparency) — given child safety and compliance work
- IEEE and ACM conferences in software engineering, security, systems

**Award and competition judging:**
- Forbes 30 Under 30 Technology — judge applications
- Webby Awards — technology category judges
- Product Hunt Golden Kitty Awards — category judges
- AngelList / Wellfound startup competitions
- SXSW Pitch competition judges
- Fast Company Innovation by Design — technology track

**Grant and fellowship review panels:**
- NSF SBIR/STTR program review panels
- Mozilla Foundation technology grants
- Ford Foundation, Knight Foundation tech for social good
- Schmidt Futures, Open Philanthropy — tech reviewers

Return all opportunities you find using the return_opportunities tool. Include:
- Event or program name and host organization
- What kind of judging/evaluation role (judge, reviewer, program committee, mentor/judge)
- Whether it is formally invited (higher USCIS value) vs. open application
- Domains being evaluated (should match beneficiary's expertise)
- Event date or review window
- Application deadline or rolling
- How to apply or express interest (URL)
- Effort: low (<2hr total), medium (2–8hr), high (>8hr), plus rationale
- Topic tags (2–4)

Prioritize formally invited roles and nationally/internationally recognized programs — these carry more weight for USCIS. Include smaller but credible opportunities too if they are a strong domain fit. Return up to 12 results."""

RETURN_TOOL = {
    "name": "return_opportunities",
    "description": "Return the list of judging and evaluation opportunities found via web search.",
    "input_schema": {
        "type": "object",
        "properties": {
            "opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event_name": {"type": "string", "description": "e.g. 'MLH Fall 2025 Season — Hackathon Judge'"},
                        "host_organization": {"type": "string", "description": "Organization running the program"},
                        "host_domain": {"type": "string"},
                        "role_type": {
                            "type": "string",
                            "enum": ["hackathon_judge", "program_committee", "demo_day_judge", "grant_reviewer", "award_judge", "mentor_judge"],
                            "description": "Type of judging/evaluation role",
                        },
                        "is_invited": {
                            "type": "boolean",
                            "description": "True if this is a formally invited/nominated role (higher USCIS value), False if open application",
                        },
                        "evaluation_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Domains or tracks being evaluated (e.g. AI/ML, social impact, developer tools)",
                        },
                        "topic_tags": {"type": "array", "items": {"type": "string"}},
                        "event_date": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null"},
                        "deadline": {"type": ["string", "null"], "description": "Application deadline ISO date or null"},
                        "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"]},
                        "requirements": {
                            "type": "string",
                            "description": "How to apply or express interest; what qualifications are expected",
                        },
                        "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                        "effort_rationale": {"type": "string"},
                        "url": {"type": "string", "description": "Application page or contact URL"},
                    },
                    "required": [
                        "event_name", "host_organization", "host_domain", "role_type",
                        "is_invited", "evaluation_domains", "topic_tags", "deadline_status",
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


def discover_judging_opportunities(db: Session) -> list[dict]:
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
