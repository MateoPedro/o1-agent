from app.models import Opportunity

# USCIS O-1A criterion wording per opportunity type.
# No LLM needed — deterministic mapping.
# TODO: refine wording to match exact USCIS O-1A criterion language and
#       handle edge cases (e.g. high-prestige keynote may also support
#       "critical role at distinguished organization").

CRITERIA_BY_TYPE = {
    "talk": [
        "Original contributions of major significance in the field",
        "Performance in a leading or critical role for distinguished organizations",
    ],
    "judge": [
        "Participation as a judge of the work of others in the field",
    ],
    "member": [
        "Membership in associations in the field that require outstanding achievement",
    ],
    "blog": [
        "Authorship of scholarly articles in the field",
        "Original contributions of major significance in the field",
    ],
    "article": [
        "Authorship of scholarly articles in the field",
        "Original contributions of major significance in the field",
    ],
}


def map_criteria(opp: Opportunity) -> list[str]:
    criteria = CRITERIA_BY_TYPE.get(opp.type, [])

    # Boost: prestigious invited speaking role also supports critical role criterion
    if opp.type == "talk" and opp.prestige_score and opp.prestige_score >= 0.75:
        criteria = criteria + ["Critical role at a distinguished organization or establishment"]

    return criteria
