from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.config import settings
from app.models import Opportunity, AuditLog
from app.profile.loader import load_profile

client = Anthropic(api_key=settings.anthropic_api_key)

# Tunable weights — sum to 1.0
WEIGHTS = {
    "fit": 0.30,
    "prestige": 0.25,
    "evidence": 0.25,
    "effort": 0.10,
    "location": 0.10,
}

# Membership weights — prestige and evidence dominate; location is irrelevant
MEMBERSHIP_WEIGHTS = {
    "fit":      0.25,
    "prestige": 0.40,
    "evidence": 0.30,
    "effort":   0.05,
    "location": 0.00,
}

# Media weights — prestige (audience/outlet reputation) and fit dominate; location irrelevant
MEDIA_WEIGHTS = {
    "fit":      0.35,
    "prestige": 0.35,
    "evidence": 0.20,
    "effort":   0.10,
    "location": 0.00,
}

# Judging weights — evidence dominates (direct USCIS criterion); prestige of the program matters
JUDGING_WEIGHTS = {
    "fit":      0.15,
    "prestige": 0.30,
    "evidence": 0.45,
    "effort":   0.05,
    "location": 0.05,
}

LOCATION_SCORES = {
    "virtual": 1.0,
    "remote": 1.0,
    "online": 1.0,
    "san francisco": 1.0,
    "bay area": 1.0,
    "san jose": 1.0,
    "berkeley": 1.0,
    "oakland": 1.0,
}

SCORE_TOOL = {
    "name": "score_opportunity",
    "description": "Return a score vector for the opportunity.",
    "input_schema": {
        "type": "object",
        "properties": {
            "fit": {
                "type": "number",
                "description": "0.0–1.0. Topic overlap between the event and the speaker's domains.",
            },
            "prestige": {
                "type": "number",
                "description": "0.0–1.0. Host reputation: international/national brand, known org, audience scale.",
            },
            "evidence": {
                "type": "number",
                "description": "0.0–1.0. How directly and strongly this opportunity supports O-1A USCIS criteria.",
            },
            "effort": {
                "type": "number",
                "description": "0.0–1.0. Inverse of application effort. low effort → 1.0, medium → 0.6, high → 0.2.",
            },
            "rationale": {
                "type": "string",
                "description": "1–2 sentence explanation of the scores, mentioning the strongest and weakest signals.",
            },
        },
        "required": ["fit", "prestige", "evidence", "effort", "rationale"],
    },
}


def _location_score(location: str | None) -> float:
    if not location:
        return 0.5
    loc = location.lower()
    for keyword, score in LOCATION_SCORES.items():
        if keyword in loc:
            return score
    # US but not Bay Area
    us_keywords = ["new york", "seattle", "austin", "boston", "chicago", "los angeles", "united states", ", ca", ", ny", ", wa"]
    if any(k in loc for k in us_keywords):
        return 0.6
    # International
    return 0.3


def score_opportunity(opp: Opportunity, db: Session) -> None:
    """Scores the opportunity in-place and commits to DB."""
    profile = load_profile()
    is_membership = opp.type == "member"
    is_media = opp.type == "media"
    is_judging = opp.type == "judge"

    if is_judging:
        context_lines = (
            f"- Host: {opp.host} ({opp.host_domain})\n"
            f"- Role type: {opp.type}\n"
            f"- Topic tags: {opp.topic_tags}\n"
            f"- Event date: {opp.event_date}\n"
            f"- Deadline: {opp.deadline}\n"
            f"- Effort: {opp.effort}\n"
            f"- Requirements: {opp.requirements[:400]}"
        )
        scoring_note = (
            "Score as a judging/evaluation opportunity for an O-1A petition. "
            "Evidence (0.45) is the dominant factor — does participating as a judge here "
            "directly satisfy the USCIS 'judging the work of others' criterion? "
            "Formally invited roles score higher than open applications. "
            "Prestige (0.30) reflects how recognized the program is nationally or internationally "
            "(MLH, major university hackathons, YC demo days score high). "
            "Fit (0.15) reflects how well the beneficiary's technical domains match what's being judged. "
            "Effort (0.05) is de-emphasized — a high-effort judging role is still worth pursuing. "
            "Location (0.05) is low weight — virtual is fine, Bay Area in-person is a small bonus."
        )
    elif is_media:
        context_lines = (
            f"- Outlet: {opp.host} ({opp.host_domain})\n"
            f"- Platform type: {opp.type}\n"
            f"- Topic tags: {opp.topic_tags}\n"
            f"- Deadline: {opp.deadline}\n"
            f"- Effort: {opp.effort}\n"
            f"- Requirements: {opp.requirements[:400]}"
        )
        scoring_note = (
            "Score as a media appearance opportunity. "
            "Fit (0.35) reflects how well the beneficiary's story matches this outlet's audience. "
            "Prestige (0.35) reflects the outlet's reach and recognition — major publications, "
            "established podcasts, and widely-read newsletters score higher. "
            "Evidence (0.20) reflects how strongly a feature here would support the USCIS "
            "'published material about the beneficiary' criterion. "
            "Location is irrelevant."
        )
    elif is_membership:
        context_lines = (
            f"- Host: {opp.host} ({opp.host_domain})\n"
            f"- Membership type: {opp.type}\n"
            f"- Topic tags: {opp.topic_tags}\n"
            f"- Deadline: {opp.deadline}\n"
            f"- Effort: {opp.effort}\n"
            f"- Requirements: {opp.requirements[:400]}"
        )
        scoring_note = (
            "Score as a selective membership application. "
            "Prestige (0.40) and evidence (0.30) are most important — "
            "is this a nationally/internationally recognized association with selective criteria? "
            "Fit (0.25) reflects how well the beneficiary's background matches eligibility. "
            "Effort (0.05) is de-emphasized. Location is irrelevant — leave it out of your reasoning."
        )
    else:
        context_lines = (
            f"- Host: {opp.host} ({opp.host_domain})\n"
            f"- Format: {opp.type}\n"
            f"- Location: {opp.location}\n"
            f"- Topic tags: {opp.topic_tags}\n"
            f"- Deadline: {opp.deadline}\n"
            f"- Effort: {opp.effort}\n"
            f"- Requirements: {opp.requirements[:400]}"
        )
        scoring_note = "Score this opportunity. Be precise — this drives which opportunities surface in the inbox."

    prompt = f"""You are scoring an opportunity for an O-1A immigration petition.

Speaker profile:
- Role: Software Engineer IC4 at Meta Platforms
- Domains: {", ".join(profile["domains"])}
- Key achievements: {"; ".join(profile["achievements"][:4])}

Opportunity to score:
{context_lines}

{scoring_note}

Use the score_opportunity tool."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=[SCORE_TOOL],
        tool_choice={"type": "tool", "name": "score_opportunity"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "scoring", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))

    for block in response.content:
        if block.type == "tool_use" and block.name == "score_opportunity":
            s = block.input
            if is_membership:
                weights = MEMBERSHIP_WEIGHTS
            elif is_media:
                weights = MEDIA_WEIGHTS
            elif is_judging:
                weights = JUDGING_WEIGHTS
            else:
                weights = WEIGHTS
            loc_score = 0.0 if (is_membership or is_media) else _location_score(opp.location)

            opp.fit_score = s["fit"]
            opp.prestige_score = s["prestige"]
            opp.evidence_score = s["evidence"]
            opp.effort_score = s["effort"]
            opp.score_rationale = s["rationale"]
            opp.priority_score = round(
                s["fit"]      * weights["fit"]
                + s["prestige"] * weights["prestige"]
                + s["evidence"] * weights["evidence"]
                + s["effort"]   * weights["effort"]
                + loc_score     * weights["location"],
                4,
            )
            db.commit()
            return
