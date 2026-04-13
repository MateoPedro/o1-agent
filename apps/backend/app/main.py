from contextlib import asynccontextmanager
from datetime import date, datetime
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app import models
from app.schemas import OpportunityOut, PipelineOpportunityOut, DraftOut
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
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
    limit: int = Query(default=None),
    db: Session = Depends(get_db),
):
    cap = limit or settings.weekly_max_actions
    today = date.today()
    opportunities = (
        db.query(models.Opportunity)
        .filter(models.Opportunity.status == "discovered")
        .filter(models.Opportunity.priority_score.isnot(None))
        # Exclude if application deadline has passed
        .filter(
            or_(
                models.Opportunity.deadline_status != "specific",
                models.Opportunity.deadline >= today,
            )
        )
        # Exclude if the event itself has already happened
        .filter(
            or_(
                models.Opportunity.event_date.is_(None),
                models.Opportunity.event_date >= today,
            )
        )
        .order_by(models.Opportunity.priority_score.desc())
        .limit(cap)
        .all()
    )
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
    return opp


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

    message_id = gmail_send(
        to=target["to"],
        subject=target["subject"],
        body=target["body"],
    )

    # Mark email as sent
    target["sent"] = True
    draft.action_plan = {**plan, "email_drafts": email_drafts}
    draft.message_id = message_id

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
    db.commit()
    db.refresh(draft)
    return draft


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
