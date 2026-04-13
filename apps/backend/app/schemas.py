from pydantic import BaseModel
from typing import Literal
from datetime import date, datetime


class OpportunityCreate(BaseModel):
    type: Literal["judge", "member", "talk", "blog", "article"]
    host: str
    host_domain: str
    topic_tags: list[str]
    deadline: date | None = None
    deadline_status: Literal["specific", "rolling", "unknown"] = "unknown"
    event_date: date | None = None
    requirements: str
    effort: Literal["low", "medium", "high"]
    effort_rationale: str | None = None
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
    deadline_status: str
    event_date: date | None
    effort: str
    effort_rationale: str | None
    location: str | None
    source_url: str
    priority_score: float | None
    score_rationale: str | None
    uscis_criteria: list | None
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
    action_plan: dict | None
    message_id: str | None
    thread_id: str | None
    reply_classification: str | None
    reply_summary: str | None
    created_at: datetime
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class PipelineOpportunityOut(BaseModel):
    id: int
    type: str
    host: str
    host_domain: str
    topic_tags: list[str]
    deadline: date | None
    deadline_status: str
    event_date: date | None
    effort: str
    effort_rationale: str | None
    location: str | None
    source_url: str
    priority_score: float | None
    score_rationale: str | None
    uscis_criteria: list | None
    status: str
    created_at: datetime
    draft: DraftOut | None = None

    model_config = {"from_attributes": True}


class EvidenceOut(BaseModel):
    id: int
    opportunity_id: int | None
    activity_type: str
    host_name: str
    host_description: str
    date: date
    public_url: str
    uscis_criteria: list
    supporting_details: dict
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
