"""Discover guest post, article, and publication opportunities for the authorship USCIS criterion."""
from datetime import datetime, date
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Prompt, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

DEFAULT_PROMPT_NAME = "publishing_discovery"
DEFAULT_PROMPT_VERSION = 1
DEFAULT_PROMPT_BODY = """You are helping build an O-1A immigration case by finding publishing opportunities — guest posts, bylined articles, research pieces, and column slots — where a software engineer can contribute as a named author.

The USCIS O-1A criterion being targeted: "Authorship of scholarly articles in the field, in professional journals, or other major media."

The beneficiary is a Software Engineer IC4 at Meta Platforms (~2 years experience). Key background:
- Built compliance systems for Australia's world-first social media Under-16 law (~544K account actions across Instagram, Facebook, Threads) — covered by TIME, CNBC, PBS NewsHour
- Engineered anti-circumvention systems protecting 50M+ US teenagers on Instagram and Facebook — covered by Washington Post, Fox News
- Migrated 60+ agentic AI tools to MCP at Meta, improving production latency 20%
- Promoted IC3→IC4 in under a year at Meta (typical timeline: 2–3 years)
- From France, navigated F-1 visa → US tech career; mentors international engineers
Domains: AI agents, MCP, age verification, child safety, social media regulation, developer tools, software engineering career, immigration into US tech.

Search actively for outlets actively accepting guest contributions, pitches, or submissions. Go wide — start with well-known outlets then go deeper:

**Practitioner engineering publications (high USCIS value):**
- The Pragmatic Engineer (Substack, ~600K subscribers) — guest posts and interviews
- Software Engineering Daily — articles and podcast episodes
- InfoQ — technical articles and case studies
- DZone — technical contributor program
- Dev.to and Hashnode — open contributor platforms (lower prestige but indexed)
- TLDR Newsletter — sponsored/guest slots

**AI/ML and agentic AI publications:**
- Towards Data Science (Medium publication, ~700K followers) — guest contributor
- The Batch (Andrew Ng / DeepLearning.AI) — guest essays
- Import AI (Jack Clark) — guest perspectives
- Gradient Flow — AI/ML practitioner pieces
- The AI Edge — practical AI engineering content
- Last Week in AI — submissions and guest pieces
- Association for Computing Machinery (ACM) Queue — practitioner articles
- IEEE Spectrum — technology and engineering articles

**Policy, child safety, and social media regulation:**
- Tech Policy Press — long-form policy analysis
- Center for Democracy and Technology (CDT) — guest commentaries
- Future of Privacy Forum — practitioner perspectives
- Knight First Amendment Institute — essays on tech and rights
- Lawfare — tech and national security overlap
- WIRED Opinion / Ideas — op-eds and essays

**Software engineering and career:**
- freeCodeCamp — technical tutorials and deep dives
- Better Programming (Medium) — engineering culture and career
- Hacker Noon — technical articles with broad reach
- Changelog — engineering community content

**Academic and scholarly (O-1A gold standard):**
- ACM Digital Library — conference and journal papers
- IEEE Transactions journals — peer-reviewed articles
- arXiv preprints — especially CS.CR (security/privacy), CS.CY (social), CS.AI
- USENIX Security, IEEE S&P, CCS — academic security and systems venues

For each opportunity return:
- Publication name and host domain
- Content type: article, blog, op_ed, research_paper, case_study, tutorial
- Audience size or reach if findable
- Whether submissions are open and how to pitch
- Typical article length (word count range)
- Review timeline (how long until published)
- Deadline or rolling
- Effort: low (<2hr to pitch), medium (2–8hr to write), high (>8hr for research papers)
- Topic fit: which of the beneficiary's domains would resonate most with this outlet
- URL to contributor guidelines or submission page

Return up to 12 results. Prioritize outlets where a bylined article directly constitutes "published material in professional journals or major media" per USCIS standards. Include a range from prestigious trade press to accessible practitioner platforms."""

RETURN_TOOL = {
    "name": "return_opportunities",
    "description": "Return the list of publishing opportunities found via web search.",
    "input_schema": {
        "type": "object",
        "properties": {
            "opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event_name": {
                            "type": "string",
                            "description": "e.g. 'ACM Queue — Practitioner Article Submission' or 'The Pragmatic Engineer — Guest Post'",
                        },
                        "host_organization": {"type": "string"},
                        "host_domain": {"type": "string"},
                        "content_type": {
                            "type": "string",
                            "enum": ["article", "blog", "op_ed", "research_paper", "case_study", "tutorial"],
                        },
                        "audience_size": {
                            "type": ["string", "null"],
                            "description": "e.g. '600K subscribers' or null if unknown",
                        },
                        "word_count_range": {
                            "type": ["string", "null"],
                            "description": "e.g. '1500–3000 words' or null if unspecified",
                        },
                        "review_timeline": {
                            "type": ["string", "null"],
                            "description": "Typical time from submission to publication, e.g. '2–4 weeks'",
                        },
                        "topic_fit": {
                            "type": "string",
                            "description": "Which specific topic from the beneficiary's background would resonate most here and why",
                        },
                        "topic_tags": {"type": "array", "items": {"type": "string"}},
                        "deadline": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null for rolling"},
                        "deadline_status": {"type": "string", "enum": ["specific", "rolling", "unknown"]},
                        "requirements": {
                            "type": "string",
                            "description": "How to pitch or submit: what to send, pitch vs. full draft, format requirements",
                        },
                        "effort": {"type": "string", "enum": ["low", "medium", "high"]},
                        "effort_rationale": {"type": "string"},
                        "url": {"type": "string", "description": "Contributor guidelines or submission page URL"},
                    },
                    "required": [
                        "event_name", "host_organization", "host_domain", "content_type",
                        "topic_fit", "topic_tags", "deadline_status",
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


def discover_publishing_opportunities(db: Session) -> list[dict]:
    prompt_body, prompt_id = get_active_prompt(db)

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
            RETURN_TOOL,
        ],
        messages=[{"role": "user", "content": dated_prompt}],
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
