from contextlib import asynccontextmanager
from datetime import date
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app import models
from app.schemas import OpportunityOut
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


@app.post("/opportunities/{opportunity_id}/approve", response_model=OpportunityOut)
def approve_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = "drafted"
    db.commit()
    db.refresh(opp)
    return opp
