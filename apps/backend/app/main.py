from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/inbox", response_model=list[OpportunityOut])
def inbox(
    limit: int = Query(default=None),
    db: Session = Depends(get_db),
):
    cap = limit or settings.weekly_max_actions
    opportunities = (
        db.query(models.Opportunity)
        .filter(models.Opportunity.status == "discovered")
        .filter(models.Opportunity.priority_score.isnot(None))
        .order_by(models.Opportunity.priority_score.desc())
        .limit(cap)
        .all()
    )
    return opportunities
