from pydantic import BaseModel
from typing import Literal
from datetime import date, datetime


class OpportunityCreate(BaseModel):
    type: Literal["judge", "member", "talk", "blog", "article"]
    host: str
    host_domain: str
    topic_tags: list[str]
    deadline: date | None = None
    requirements: str
    effort: Literal["low", "medium", "high"]
    source_url: str
    raw_text: str
    location: str | None = None


class OpportunityOut(BaseModel):
    id: int
    type: str
    host: str
    host_domain: str
    topic_tags: list[str]
    deadline: date | None
    effort: str
    location: str | None
    priority_score: float | None
    score_rationale: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DraftOut(BaseModel):
    id: int
    opportunity_id: int
    subject: str
    body: str
    form_fields: dict | None
    bio_variant_used: str | None
    story_module_used: str | None
    created_at: datetime
    approved_at: datetime | None

    model_config = {"from_attributes": True}
