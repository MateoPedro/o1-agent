from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Opportunity, AuditLog

client = Anthropic(api_key=settings.anthropic_api_key)

# Exact USCIS O-1A criterion definitions
USCIS_CRITERIA = [
    {
        "name": "Receipt of nationally or internationally recognized prizes or awards for excellence",
        "guidance": "Covers awards that show broad recognition beyond a local office or school — major professional prizes, selective fellowships, competition wins. Must reflect real distinction in the field, not participation or routine recognition.",
    },
    {
        "name": "Membership in associations that require outstanding achievements of their members",
        "guidance": "Membership is not open to anyone who pays dues. USCIS looks for organizations that admit members based on peer-reviewed accomplishments, exceptional achievement, or selective standards.",
    },
    {
        "name": "Published material about the beneficiary in professional or major media",
        "guidance": "The material must be about you and your work — feature articles, interviews, profiles, or substantial coverage in recognized trade, professional, or mainstream media. Not just written by you or casually mentioning you.",
    },
    {
        "name": "Participation as a judge of the work of others in the same or allied field",
        "guidance": "Includes reviewing papers, serving on award panels, evaluating competitors, judging grants, or acting as a peer reviewer. Shows that others in the field trust your expertise enough to assess their work.",
    },
    {
        "name": "Original contributions of major significance in the field",
        "guidance": "Requires evidence that your work had meaningful impact — widely used technology, influential research, or innovations that affected the field beyond your employer.",
    },
    {
        "name": "Authorship of scholarly articles in professional journals or other major media",
        "guidance": "Published writing showing recognized expertise — articles in respected journals, conference proceedings, or major industry publications. Quality and importance of the publications matter more than quantity.",
    },
    {
        "name": "Employment in a critical or essential capacity for organizations with a distinguished reputation",
        "guidance": "A key role essential to the organization's success, with a highly regarded employer. Evidence includes job descriptions, organizational charts, and proof that work had strategic importance.",
    },
    {
        "name": "High salary or other high remuneration compared with others in the field",
        "guidance": "Compensation significantly above typical for the occupation and location. USCIS compares salary, bonus, equity, or consulting fees against market data, contracts, and wage surveys.",
    },
]

CRITERIA_TOOL = {
    "name": "map_criteria",
    "description": "Map the opportunity to the O-1A USCIS criteria it supports.",
    "input_schema": {
        "type": "object",
        "properties": {
            "criteria": {
                "type": "array",
                "description": "Only include criteria that genuinely apply. Omit criteria with no real connection. Typically 1–3 criteria per opportunity.",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterion": {
                            "type": "string",
                            "description": "Exact criterion name from the list provided.",
                        },
                        "strength": {
                            "type": "string",
                            "enum": ["strong", "moderate", "weak"],
                            "description": "strong = directly satisfies the criterion with concrete evidence; moderate = supports it but evidence is indirect; weak = tangential, useful only as corroborating evidence.",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "One sentence explaining specifically why this opportunity supports this criterion for this person.",
                        },
                    },
                    "required": ["criterion", "strength", "rationale"],
                },
            }
        },
        "required": ["criteria"],
    },
}


def map_criteria(opp: Opportunity, db: Session) -> list[dict]:
    criteria_text = "\n".join(
        f"{i+1}. {c['name']}\n   {c['guidance']}"
        for i, c in enumerate(USCIS_CRITERIA)
    )

    prompt = f"""You are helping map an O-1A immigration petition for a software engineer.

Beneficiary profile:
- Role: Software Engineer IC4 at Meta Platforms (San Francisco Bay Area)
- Key work: Age verification systems (Australia Under-16 enforcement ~544K accounts, Florida HB3/Utah SB152 protecting 5M+ minors, Teen Accounts for 50M+ US teenagers), MCP tool migration (60+ tools, 20% latency improvement)
- Compensation: ~$294K total (2.2x US SWE median)
- Background: French/Portuguese, Georgia Tech CS grad, promoted IC3→IC4 in ~1 year

Opportunity being evaluated:
- Host: {opp.host} ({opp.host_domain})
- Type: {opp.type}
- Location: {opp.location}
- Topic tags: {opp.topic_tags}
- Requirements: {opp.requirements[:500]}
- Prestige score: {opp.prestige_score}

The 8 USCIS O-1A criteria:
{criteria_text}

Using the map_criteria tool, identify which of the 8 criteria this opportunity genuinely supports for this beneficiary. Be precise — only include criteria with a real, defensible connection. Typically 1–3 criteria apply per opportunity."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        tools=[CRITERIA_TOOL],
        tool_choice={"type": "tool", "name": "map_criteria"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "criteria_mapping", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "map_criteria":
            return block.input.get("criteria", [])

    return []
