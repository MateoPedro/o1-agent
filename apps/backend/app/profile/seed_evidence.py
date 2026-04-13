"""Seed Evidence entries from profile.yaml story modules."""
from datetime import date
from sqlalchemy.orm import Session
from app.profile.loader import load_profile
from app.models import Evidence

# Map profile short names → full USCIS criterion names
CRITERION_MAP = {
    "critical role at distinguished organization": "Employment in a critical or essential capacity for organizations with a distinguished reputation",
    "published material about the person's work": "Published material about the beneficiary in professional or major media",
    "original contributions of major significance": "Original contributions of major significance in the field",
    "nationally recognized prizes or awards": "Receipt of nationally or internationally recognized prizes or awards for excellence",
    "membership in selective associations": "Membership in associations that require outstanding achievements of their members",
    "judging the work of others": "Participation as a judge of the work of others in the same or allied field",
    "authorship of scholarly articles": "Authorship of scholarly articles in professional journals or other major media",
    "high salary": "High salary or other high remuneration compared with others in the field",
}


def seed_profile_evidence(db: Session) -> int:
    """Create Evidence entries from profile story modules. Skips if already seeded."""
    existing = db.query(Evidence).filter_by(source="profile").count()
    if existing > 0:
        return 0

    profile = load_profile()
    today = date.today()
    count = 0

    for module_name, module in profile["story_modules"].items():
        uscis_criteria = []
        for short_name in module.get("uscis_criteria", []):
            full_name = CRITERION_MAP.get(short_name.lower().strip(), short_name)
            uscis_criteria.append({
                "criterion": full_name,
                "strength": "strong",
                "rationale": module["summary"],
            })

        evidence = Evidence(
            opportunity_id=None,
            activity_type="employment",
            host_name="Meta Platforms",
            host_description="Global technology company — Facebook, Instagram, WhatsApp, Threads (3B+ users)",
            date=today,
            public_url="https://meta.com",
            uscis_criteria=uscis_criteria,
            supporting_details={
                "module": module_name,
                "title": module["title"],
                "summary": module["summary"],
            },
            source="profile",
        )
        db.add(evidence)
        count += 1

    db.commit()
    return count
