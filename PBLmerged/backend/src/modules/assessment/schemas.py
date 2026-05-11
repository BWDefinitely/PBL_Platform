from pydantic import BaseModel


class DomainScoreOut(BaseModel):
    domain: str
    normalized: float
    tier: str | None = None


class MilestoneSummaryOut(BaseModel):
    milestone: str
    composite_score: float
    student_tier: str
    assessed_at: str | None = None
    domain_scores: dict[str, float]


class StudentListItem(BaseModel):
    student_id: str
    latest_milestone: str
    latest_composite_score: float
    latest_tier: str
    intervention_alert: bool
