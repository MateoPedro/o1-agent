from app.worker import celery_app
from app.database import SessionLocal
from app.models import Opportunity
from app.llm.discovery import discover_speaking_opportunities
from app.llm.normalizer import normalize_opportunity


@celery_app.task(name="app.tasks.discover_speaking_ops")
def discover_speaking_ops():
    db = SessionLocal()
    results = {"discovered": 0, "skipped_duplicates": 0, "failed": 0}

    try:
        raw_opportunities = discover_speaking_opportunities(db)

        for raw in raw_opportunities:
            url = raw.get("url", "")
            if not url:
                results["failed"] += 1
                continue

            # Deduplicate on source_url
            exists = db.query(Opportunity).filter_by(source_url=url).first()
            if exists:
                results["skipped_duplicates"] += 1
                continue

            normalized = normalize_opportunity(raw, db)
            if not normalized:
                results["failed"] += 1
                continue

            opp = Opportunity(**normalized.model_dump())
            db.add(opp)
            db.commit()
            results["discovered"] += 1

    finally:
        db.close()

    return results
