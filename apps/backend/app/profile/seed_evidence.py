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

# Set of module names already seeded (checked per-module so new ones can be added)
def _seeded_modules(db: Session) -> set[str]:
    rows = db.query(Evidence).filter_by(source="profile").all()
    return {r.supporting_details.get("module") for r in rows if r.supporting_details}


def seed_profile_evidence(db: Session) -> int:
    """Create Evidence entries for any profile story modules not yet seeded."""
    already_seeded = _seeded_modules(db)
    profile = load_profile()
    today = date.today()
    count = 0

    for module_name, module in profile["story_modules"].items():
        if module_name in already_seeded:
            continue

        uscis_criteria = []
        for short_name in module.get("uscis_criteria", []):
            full_name = CRITERION_MAP.get(short_name.lower().strip(), short_name)
            uscis_criteria.append({
                "criterion": full_name,
                "strength": "strong",
                "rationale": module["summary"],
            })

        # Use URL from module if available (e.g. youtube), otherwise Meta
        public_url = module.get("url", "https://meta.com")
        host_name = "Meta Platforms" if not module.get("url") else "Jack of All Trades / YouTube"
        host_description = (
            "Global technology company — Facebook, Instagram, WhatsApp, Threads (3B+ users)"
            if not module.get("url")
            else "YouTube podcast with 300,000+ Instagram followers"
        )
        activity_type = _activity_type(module_name)

        evidence = Evidence(
            opportunity_id=None,
            activity_type=activity_type,
            host_name=host_name,
            host_description=host_description,
            date=today,
            public_url=public_url,
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

    if count:
        db.commit()
    return count


def _activity_type(module_name: str) -> str:
    mapping = {
        "hackathon_judging": "judge",
        "youtube_appearance": "media",
        "high_salary": "employment",
        "internal_evaluations": "judge",
    }
    return mapping.get(module_name, "employment")
