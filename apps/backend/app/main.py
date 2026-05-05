from contextlib import asynccontextmanager
from datetime import date, datetime
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app import models
from app.models import AuditLog
from app.schemas import OpportunityOut, PipelineOpportunityOut, DraftOut, EvidenceOut
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    # Seed profile evidence on startup (no-op if already seeded)
    from app.database import SessionLocal as _Session
    from app.profile.seed_evidence import seed_profile_evidence
    _db = _Session()
    try:
        seed_profile_evidence(_db)
    finally:
        _db.close()
    yield


app = FastAPI(title="o1-agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/inbox", response_model=list[OpportunityOut])
def inbox(
    limit: int = Query(default=20),
    type: str = Query(default=None),
    db: Session = Depends(get_db),
):
    today = date.today()
    q = (
        db.query(models.Opportunity)
        .filter(models.Opportunity.status == "discovered")
        .filter(models.Opportunity.priority_score.isnot(None))
        .filter(
            or_(
                models.Opportunity.deadline_status != "specific",
                models.Opportunity.deadline >= today,
            )
        )
        .filter(
            or_(
                models.Opportunity.event_date.is_(None),
                models.Opportunity.event_date >= today,
            )
        )
    )
    if type:
        types = type.split(",")
        q = q.filter(models.Opportunity.type.in_(types))
    opportunities = q.order_by(models.Opportunity.priority_score.desc()).limit(limit).all()
    return opportunities


@app.post("/opportunities/{opportunity_id}/plan", response_model=PipelineOpportunityOut)
def create_plan(opportunity_id: int, db: Session = Depends(get_db)):
    from app.llm.planner import create_action_plan
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    action_plan = create_action_plan(opp, db)

    draft = models.Draft(
        opportunity_id=opp.id,
        subject="",
        body="",
        action_plan=action_plan,
    )
    db.add(draft)
    opp.status = "in_progress"
    db.commit()
    db.refresh(opp)
    db.refresh(draft)
    data = PipelineOpportunityOut.model_validate(opp)
    data.draft = DraftOut.model_validate(draft)
    return data


@app.post("/drafts/{draft_id}/emails/{email_id}/send", response_model=DraftOut)
def send_email(draft_id: int, email_id: str, db: Session = Depends(get_db)):
    from app.gmail import send_email as gmail_send
    draft = db.query(models.Draft).filter(models.Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    plan = draft.action_plan or {}
    email_drafts = plan.get("email_drafts", [])
    target = next((e for e in email_drafts if e["id"] == email_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Email draft not found")

    message_id, thread_id = gmail_send(
        to=target["to"],
        subject=target["subject"],
        body=target["body"],
    )

    # Mark email as sent
    target["sent"] = True
    draft.action_plan = {**plan, "email_drafts": email_drafts}
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(draft, "action_plan")
    draft.message_id = message_id
    draft.thread_id = thread_id

    # Move opportunity to submitted
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == draft.opportunity_id).first()
    if opp:
        opp.status = "submitted"

    db.add(AuditLog(
        opportunity_id=draft.opportunity_id,
        draft_id=draft.id,
        direction="outbound",
        payload={"to": target["to"], "subject": target["subject"], "gmail_message_id": message_id},
        timestamp=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(draft)
    return draft


@app.patch("/drafts/{draft_id}/todos/{todo_id}/toggle", response_model=DraftOut)
def toggle_todo(draft_id: int, todo_id: str, db: Session = Depends(get_db)):
    draft = db.query(models.Draft).filter(models.Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    plan = draft.action_plan or {}
    todos = plan.get("todos", [])
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = not todo["completed"]
            break

    draft.action_plan = {**plan, "todos": todos}
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(draft, "action_plan")
    db.commit()
    db.refresh(draft)
    return draft


@app.post("/opportunities/{opportunity_id}/accept", response_model=PipelineOpportunityOut)
def accept_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    opp = db.query(models.Opportunity).options(joinedload(models.Opportunity.drafts)).filter(models.Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = "accepted"
    db.commit()
    data = PipelineOpportunityOut.model_validate(opp)
    if opp.drafts:
        data.draft = DraftOut.model_validate(opp.drafts[-1])
    return data


@app.post("/opportunities/{opportunity_id}/log-evidence", response_model=EvidenceOut)
def log_evidence(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    evidence = models.Evidence(
        opportunity_id=opp.id,
        activity_type=opp.type,
        host_name=opp.host,
        host_description=opp.host_domain,
        date=opp.event_date or date.today(),
        public_url=opp.source_url,
        uscis_criteria=opp.uscis_criteria or [],
        supporting_details={
            "location": opp.location,
            "topic_tags": opp.topic_tags,
            "priority_score": opp.priority_score,
            "score_rationale": opp.score_rationale,
            "effort": opp.effort,
        },
    )
    db.add(evidence)
    opp.status = "completed"
    db.commit()
    db.refresh(evidence)

    # Update profile.yaml with a new story module and re-seed so it appears in evidence
    try:
        from app.profile.updater import update_profile_with_opportunity
        from app.profile.seed_evidence import seed_profile_evidence
        update_profile_with_opportunity(opp, db)
        seed_profile_evidence(db)
    except Exception:
        pass  # Profile update is best-effort — never fail the evidence log

    return evidence


@app.get("/evidence", response_model=list[EvidenceOut])
def get_evidence(db: Session = Depends(get_db)):
    return db.query(models.Evidence).order_by(models.Evidence.date.desc()).all()


@app.get("/evidence/export")
def export_evidence(db: Session = Depends(get_db)):
    from fastapi.responses import PlainTextResponse
    entries = db.query(models.Evidence).order_by(models.Evidence.date.desc()).all()
    if not entries:
        return PlainTextResponse("No evidence logged yet.")

    # Group by criterion
    by_criterion: dict[str, list] = {}
    for entry in entries:
        for c in (entry.uscis_criteria or []):
            criterion = c.get("criterion", "Unknown")
            by_criterion.setdefault(criterion, []).append((entry, c))

    lines = ["# O-1A Evidence Log\n"]
    for criterion, items in by_criterion.items():
        lines.append(f"## {criterion}\n")
        for entry, c in items:
            lines.append(f"### {entry.host_name} — {entry.activity_type} — {entry.date}")
            lines.append(f"- **Strength:** {c.get('strength', '').capitalize()}")
            lines.append(f"- **URL:** {entry.public_url}")
            lines.append(f"- **Rationale:** {c.get('rationale', '')}")
            if entry.supporting_details.get("score_rationale"):
                lines.append(f"- **Context:** {entry.supporting_details['score_rationale']}")
            lines.append("")

    from fastapi.responses import Response
    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=o1a-evidence.md"},
    )


@app.get("/pipeline", response_model=list[PipelineOpportunityOut])
def pipeline(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    from app.schemas import DraftOut
    opps = (
        db.query(models.Opportunity)
        .options(joinedload(models.Opportunity.drafts))
        .filter(models.Opportunity.status != "discovered")
        .order_by(models.Opportunity.updated_at.desc())
        .all()
    )
    results = []
    for opp in opps:
        data = PipelineOpportunityOut.model_validate(opp)
        if opp.drafts:
            data.draft = DraftOut.model_validate(opp.drafts[-1])
        results.append(data)
    return results
