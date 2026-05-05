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

MEMBERSHIP_PLAN_TOOL = {
    "name": "create_action_plan",
    "description": "Create a detailed action plan for pursuing this membership application.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "Ordered list of concrete next steps to complete and submit this membership application.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "task": {"type": "string", "description": "Short action title (under 10 words)"},
                        "detail": {"type": "string", "description": "Specific instructions: what to prepare, who to contact, what to write, by when."},
                        "completed": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "task", "detail", "completed"],
                },
            },
            "email_drafts": {
                "type": "array",
                "description": "Ready-to-send emails for nominator outreach. One email per nominator you are asking to endorse.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "to": {"type": "string", "description": "Recipient role description, e.g. 'Former manager at Meta'"},
                        "subject": {"type": "string"},
                        "body": {"type": "string", "description": "Full email body, personalized and ready to send"},
                        "sent": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "to", "subject", "body", "sent"],
                },
            },
            "membership_statement": {
                "type": "object",
                "properties": {
                    "personal_statement_draft": {
                        "type": "string",
                        "description": "A 2–3 paragraph draft personal statement written in first person, grounded in the beneficiary's specific achievements. Should directly address the membership's eligibility criteria.",
                    },
                    "nominator_suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "description": "e.g. 'Engineering Manager at Meta', 'Former intern who became full-time'"},
                                "why": {"type": "string", "description": "Why this person is a strong nominator for this specific membership"},
                                "outreach_note": {"type": "string", "description": "One sentence on what to say when asking them to nominate"},
                            },
                            "required": ["role", "why", "outreach_note"],
                        },
                        "description": "3–5 suggestions for who to ask as nominators, with specific rationale.",
                    },
                    "talking_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "4–6 specific bullet points from the beneficiary's background that most directly satisfy this membership's eligibility criteria.",
                    },
                    "application_window_note": {
                        "type": "string",
                        "description": "Summary of when to apply and key dates to track.",
                    },
                },
                "required": ["personal_statement_draft", "nominator_suggestions", "talking_points", "application_window_note"],
            },
        },
        "required": ["todos", "email_drafts", "membership_statement"],
    },
}


MEDIA_PLAN_TOOL = {
    "name": "create_action_plan",
    "description": "Create an action plan for pitching this media outlet for a feature or guest appearance.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "Ordered steps to research, pitch, and follow up with this outlet.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "task": {"type": "string", "description": "Short action title (under 10 words)"},
                        "detail": {"type": "string", "description": "Specific instructions: what to do, where, by when."},
                        "completed": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "task", "detail", "completed"],
                },
            },
            "email_drafts": {
                "type": "array",
                "description": "Ready-to-send pitch email(s) to the host or editor. Should be personalized, concise, and lead with the most compelling story angle.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "to": {"type": "string", "description": "Recipient role e.g. 'Podcast host' or editor email if known"},
                        "subject": {"type": "string"},
                        "body": {"type": "string", "description": "Full pitch email body, ready to send"},
                        "sent": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "to", "subject", "body", "sent"],
                },
            },
            "pitch": {
                "type": "object",
                "properties": {
                    "suggested_angle": {
                        "type": "string",
                        "description": "The specific story angle that best fits this outlet's audience — 2–3 sentences on what the episode/feature would be about.",
                    },
                    "talking_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "4–5 concrete things from the beneficiary's work to highlight — specific metrics, stories, or insights that would resonate with this audience.",
                    },
                    "follow_up_note": {
                        "type": "string",
                        "description": "What to say in a follow-up if no reply in 2 weeks.",
                    },
                },
                "required": ["suggested_angle", "talking_points", "follow_up_note"],
            },
        },
        "required": ["todos", "email_drafts", "pitch"],
    },
}


JUDGING_PLAN_TOOL = {
    "name": "create_action_plan",
    "description": "Create an action plan for applying or expressing interest in a judging/evaluation role.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "Ordered steps to apply, confirm availability, and complete the judging role.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "task": {"type": "string", "description": "Short action title (under 10 words)"},
                        "detail": {"type": "string", "description": "Specific instructions: what to do, where, by when."},
                        "completed": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "task", "detail", "completed"],
                },
            },
            "email_drafts": {
                "type": "array",
                "description": "Ready-to-send outreach emails. Include if there is a direct contact (organizer, program chair) to reach out to. Leave empty if the process is purely form-based.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "to": {"type": "string", "description": "Recipient role e.g. 'Hackathon Organizer' or email if known"},
                        "subject": {"type": "string"},
                        "body": {"type": "string", "description": "Full email body, personalized and ready to send"},
                        "sent": {"type": "boolean", "default": False},
                    },
                    "required": ["id", "to", "subject", "body", "sent"],
                },
            },
            "judging_application": {
                "type": "object",
                "properties": {
                    "why_qualified": {
                        "type": "string",
                        "description": "2–3 sentences explaining why the beneficiary is qualified to judge this specific event/program. Ground it in actual work — specific projects, metrics, or domain expertise.",
                    },
                    "domain_expertise": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific technical and domain areas the beneficiary can evaluate (e.g. 'AI agents and LLM tool use', 'social media compliance systems', 'developer tooling').",
                    },
                    "evaluation_approach": {
                        "type": "string",
                        "description": "2–3 sentences on how the beneficiary would approach evaluating submissions — what criteria matter, what distinguishes strong from weak entries in this domain.",
                    },
                    "availability_note": {
                        "type": "string",
                        "description": "Brief note on time commitment expectations and any scheduling considerations.",
                    },
                },
                "required": ["why_qualified", "domain_expertise", "evaluation_approach", "availability_note"],
            },
        },
        "required": ["todos", "email_drafts", "judging_application"],
    },
}


def create_action_plan(opp: Opportunity, db: Session) -> dict:
    if opp.type == "member":
        return _create_membership_plan(opp, db)
    if opp.type == "media":
        return _create_media_plan(opp, db)
    if opp.type == "judge":
        return _create_judging_plan(opp, db)
    return _create_speaking_plan(opp, db)


def _create_speaking_plan(opp: Opportunity, db: Session) -> dict:
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


def _create_membership_plan(opp: Opportunity, db: Session) -> dict:
    profile = load_profile()

    achievements_text = "\n".join(f"  - {a}" for a in profile["achievements"])

    prompt = f"""You are creating an action plan to help a software engineer apply for a selective professional membership as part of an O-1A immigration petition.

The USCIS criterion being targeted: "Membership in associations that require outstanding achievements of their members as judged by recognized national or international experts."

Beneficiary profile:
- Role: {profile['bio']['short']}
- Full bio: {profile['bio']['full']}
- Key achievements:
{achievements_text}

Membership opportunity:
- Organization: {opp.host} ({opp.host_domain})
- Eligibility requirements: {opp.requirements}
- Deadline: {opp.deadline} ({opp.deadline_status})
- Effort: {opp.effort} — {opp.effort_rationale}
- Application URL: {opp.source_url}

Create a practical membership application plan using the create_action_plan tool:
- todos: ordered steps to complete the application (gathering docs, contacting nominators, writing statement, submitting)
- email_drafts: one per nominator you recommend reaching out to — personalized, ready to send
- membership_statement: draft personal statement + nominator suggestions + talking points grounded in the beneficiary's actual work

Be specific. Reference the eligibility criteria directly when drafting the personal statement and talking points."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        tools=[MEMBERSHIP_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_action_plan"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "membership_planning", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_action_plan":
            return block.input

    return {"todos": [], "email_drafts": [], "membership_statement": {}}


def _create_media_plan(opp: Opportunity, db: Session) -> dict:
    profile = load_profile()

    achievements_text = "\n".join(f"  - {a}" for a in profile["achievements"])

    prompt = f"""You are creating an action plan to help a software engineer pitch a media outlet for a guest appearance or feature story, as part of an O-1A immigration petition.

The USCIS criterion being targeted: "Published material about the beneficiary in professional or major media."

Beneficiary profile:
- Role: {profile['bio']['short']}
- Full bio: {profile['bio']['full']}
- Key achievements:
{achievements_text}
- Existing media coverage: TIME, CNBC, PBS NewsHour (Australia Under-16 law), Washington Post, Fox News (Teen Accounts)

Media outlet:
- Outlet: {opp.host} ({opp.host_domain})
- How to pitch: {opp.requirements}
- Deadline: {opp.deadline} ({opp.deadline_status})
- Effort: {opp.effort} — {opp.effort_rationale}
- Pitch URL: {opp.source_url}
- Topic tags: {', '.join(opp.topic_tags)}
- Score rationale: {opp.score_rationale}

Create a media pitch plan using the create_action_plan tool:
- todos: ordered steps (research the outlet, personalize pitch, send, follow up)
- email_drafts: a ready-to-send pitch email — concise, personalized to this specific outlet's audience, leading with the most compelling story angle. Do NOT write a generic pitch.
- pitch: the suggested angle for this specific outlet, 4–5 concrete talking points, and a follow-up message

The pitch email must feel like it was written for this outlet specifically — reference their audience, their format, and why this story is timely and relevant to their readers/listeners right now."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        tools=[MEDIA_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_action_plan"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "media_planning", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_action_plan":
            return block.input

    return {"todos": [], "email_drafts": [], "pitch": {}}


def _create_judging_plan(opp: Opportunity, db: Session) -> dict:
    profile = load_profile()

    achievements_text = "\n".join(f"  - {a}" for a in profile["achievements"])

    prompt = f"""You are creating an action plan to help a software engineer apply for or express interest in a judging/evaluation role as part of an O-1A immigration petition.

The USCIS criterion being targeted: "Participation, either individually or on a panel, as a judge of the work of others in the same or an allied field."

Beneficiary profile:
- Role: {profile['bio']['short']}
- Full bio: {profile['bio']['full']}
- Key achievements:
{achievements_text}

Judging opportunity:
- Organization: {opp.host} ({opp.host_domain})
- Role type: {opp.type}
- Topic tags: {', '.join(opp.topic_tags)}
- Event date: {opp.event_date}
- Deadline: {opp.deadline} ({opp.deadline_status})
- Requirements: {opp.requirements}
- Effort: {opp.effort} — {opp.effort_rationale}
- Application URL: {opp.source_url}

Create a practical action plan using the create_action_plan tool:
- todos: ordered steps to apply, confirm participation, and fulfill the role
- email_drafts: outreach email(s) if direct contact is appropriate (organizers, program chairs) — personalized to this specific event; skip if purely form-based
- judging_application: why the beneficiary is qualified, their domain expertise relevant to what's being judged, how they'd approach evaluation, and availability notes

Be specific to this event. The "why_qualified" and "evaluation_approach" should directly reference the beneficiary's actual work — compliance systems, AI agents/MCP, age verification — not generic software engineering. These will be used verbatim in applications."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        tools=[JUDGING_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_action_plan"},
        messages=[{"role": "user", "content": prompt}],
    )

    db.add(AuditLog(
        opportunity_id=opp.id,
        direction="llm",
        payload={"model": "claude-haiku-4-5-20251001", "task": "judging_planning", "opportunity_id": opp.id},
        response={"stop_reason": response.stop_reason},
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_action_plan":
            return block.input

    return {"todos": [], "email_drafts": [], "judging_application": {}}
