from datetime import date, datetime
from sqlalchemy import String, Text, Float, Date, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))           # judge | member | talk | blog | article
    host: Mapped[str] = mapped_column(String(255))
    host_domain: Mapped[str] = mapped_column(String(255))
    topic_tags: Mapped[list] = mapped_column(JSON)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_status: Mapped[str] = mapped_column(String(20), default="unknown")  # specific | rolling | unknown
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    requirements: Mapped[str] = mapped_column(Text)
    effort: Mapped[str] = mapped_column(String(10))         # low | medium | high
    effort_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), unique=True)
    raw_text: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # city or "virtual"
    uscis_criteria: Mapped[list | None] = mapped_column(JSON, nullable=True)

    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    prestige_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    effort_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # discovered | drafted | approved | submitted | accepted | rejected | completed
    status: Mapped[str] = mapped_column(String(20), default="discovered")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    drafts: Mapped[list["Draft"]] = relationship(back_populates="opportunity")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="opportunity")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="opportunity")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    form_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bio_variant_used: Mapped[str | None] = mapped_column(String(20), nullable=True)
    story_module_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="drafts")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="draft")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    activity_type: Mapped[str] = mapped_column(String(50))
    host_name: Mapped[str] = mapped_column(String(255))
    host_description: Mapped[str] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date)
    public_url: Mapped[str] = mapped_column(String(500))
    uscis_criteria: Mapped[list] = mapped_column(JSON)      # e.g. ["judging", "leading role"]
    supporting_details: Mapped[dict] = mapped_column(JSON)  # audience size, acceptance rate, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="evidence")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(10))      # outbound | inbound | llm
    payload: Mapped[dict] = mapped_column(JSON)
    response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunity: Mapped["Opportunity | None"] = relationship(back_populates="audit_logs")
    draft: Mapped["Draft | None"] = relationship(back_populates="audit_logs")


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))          # e.g. "speaking_discovery"
    version: Mapped[int] = mapped_column(default=1)
    body: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    performance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
