from app.worker import celery_app
from app.database import SessionLocal
from app.models import Opportunity, Draft
from app.llm.discovery import discover_speaking_opportunities
from app.llm.normalizer import normalize_opportunity
from app.llm.scorer import score_opportunity
from app.llm.criteria import map_criteria
from app.llm.classifier import classify_reply
from app.gmail import get_thread_replies


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

            # 3. Map USCIS criteria (LLM) — requires prestige_score from step 2
            opp.uscis_criteria = map_criteria(opp, db)
            db.commit()

            results["discovered"] += 1

    finally:
        db.close()

    return results


@celery_app.task(name="app.tasks.poll_outcomes")
def poll_outcomes():
    db = SessionLocal()
    results = {"checked": 0, "replied": 0, "no_reply": 0, "failed": 0}

    try:
        # Find all submitted opportunities that have a thread_id to poll
        submitted = (
            db.query(Opportunity)
            .join(Draft, Draft.opportunity_id == Opportunity.id)
            .filter(Opportunity.status == "submitted")
            .filter(Draft.thread_id.isnot(None))
            .filter(Draft.reply_classification.is_(None))
            .all()
        )

        for opp in submitted:
            draft = db.query(Draft).filter_by(opportunity_id=opp.id).order_by(Draft.id.desc()).first()
            if not draft or not draft.thread_id:
                continue

            try:
                reply_text = get_thread_replies(draft.thread_id, draft.message_id)
                results["checked"] += 1

                if not reply_text:
                    results["no_reply"] += 1
                    continue

                classification, summary = classify_reply(reply_text, opp.host, db, opp.id)
                draft.reply_classification = classification
                draft.reply_summary = summary

                if classification == "accepted":
                    opp.status = "accepted"
                elif classification == "rejected":
                    opp.status = "rejected"
                elif classification == "more_info_needed":
                    opp.status = "in_progress"

                db.commit()
                results["replied"] += 1

            except Exception:
                results["failed"] += 1
                continue

    finally:
        db.close()

    return results
