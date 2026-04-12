from app.worker import celery_app
from app.database import SessionLocal
from app.models import Opportunity
from app.llm.discovery import discover_speaking_opportunities
from app.llm.normalizer import normalize_opportunity
from app.llm.scorer import score_opportunity
from app.llm.criteria import map_criteria


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
            if db.query(Opportunity).filter_by(source_url=url).first():
                results["skipped_duplicates"] += 1
                continue

            # 1. Normalize raw dict → typed Opportunity
            normalized = normalize_opportunity(raw, db)
            if not normalized:
                results["failed"] += 1
                continue

            opp = Opportunity(**normalized.model_dump())
            db.add(opp)
            db.commit()
            db.refresh(opp)

            # 2. Score (LLM) — updates opp in-place and commits
            score_opportunity(opp, db)

            # 3. Map USCIS criteria (pure function) — requires prestige_score from step 2
            opp.uscis_criteria = map_criteria(opp)
            db.commit()

            results["discovered"] += 1

    finally:
        db.close()

    return results
