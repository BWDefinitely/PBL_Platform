from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class AssessmentRun(Base):
    __tablename__ = "assessment_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    job_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (UniqueConstraint("run_id", "student_code", "milestone", name="uq_run_student_milestone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    milestone: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    student_tier: Mapped[str] = mapped_column(String(64), nullable=False)
    assessed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    narrative_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dissent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DomainScore(Base):
    __tablename__ = "domain_scores"
    __table_args__ = (UniqueConstraint("assessment_id", "domain", name="uq_assessment_domain"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(8), nullable=False)
    normalized: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DimensionScore(Base):
    __tablename__ = "dimension_scores"
    __table_args__ = (UniqueConstraint("assessment_id", "dimension", name="uq_assessment_dimension"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension: Mapped[str] = mapped_column(String(16), nullable=False)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)


class AssessmentFlag(Base):
    __tablename__ = "assessment_flags"
    __table_args__ = (UniqueConstraint("assessment_id", name="uq_assessment_flags_assessment_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_alert: Mapped[bool] = mapped_column(default=False, nullable=False)
    equity_flag: Mapped[bool] = mapped_column(default=False, nullable=False)
    unresolved_dimensions: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvidenceSnippet(Base):
    __tablename__ = "evidence_snippets"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    trace_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReportArtifact(Base):
    __tablename__ = "report_artifacts"
    __table_args__ = (UniqueConstraint("run_id", "name", name="uq_run_artifact_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
