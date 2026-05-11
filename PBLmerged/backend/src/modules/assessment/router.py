from datetime import datetime
import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.integrations.pbl_assessment.engine_adapter import AssessmentEngineAdapter
from src.jobs.import_assessment_results import import_assessments
from src.models import Assessment, AssessmentFlag, AssessmentRun, DimensionScore, DomainScore, EvidenceSnippet, StudentProfile, User
from src.modules.assessment.schemas import MilestoneSummaryOut, StudentListItem
from src.modules.auth.deps import get_current_user
from src.core.config import get_settings

router = APIRouter(prefix="/api/assessments", tags=["assessment"])
settings = get_settings()


def _run_assessment_job(db: Session, run: AssessmentRun, payload: dict) -> dict:
    pbl_root = Path(payload.get("pbl_assessment_root", "/Users/meiling/Desktop/red bird/pbl_assessment"))
    manifest = payload.get("manifest")
    output_dir = payload.get("output_dir")
    batch_db = payload.get("batch_db")
    report_dir = payload.get("report_dir")
    evidence_dir = payload.get("evidence_dir")
    assessment_json = payload.get("assessment_json")

    if not manifest or not output_dir or not batch_db:
        raise HTTPException(status_code=400, detail="manifest, output_dir, batch_db are required")

    run.status = "running"
    run.started_at = datetime.utcnow()
    db.commit()

    adapter = AssessmentEngineAdapter(pbl_assessment_root=pbl_root)
    adapter.run_assessment(manifest_path=manifest, output_dir=output_dir, db_path=batch_db)

    resolved_assessment_json = (
        Path(assessment_json) if assessment_json else (Path(output_dir) / "assessment_results.json")
    )
    result = import_assessments(
        db=db,
        run_id=run.run_id,
        assessment_json=resolved_assessment_json,
        evidence_dir=Path(evidence_dir) if evidence_dir else None,
        report_dir=Path(report_dir) if report_dir else None,
    )
    run.status = "completed"
    run.finished_at = datetime.utcnow()
    db.commit()
    return result


@router.get("/students", response_model=list[StudentListItem])
def list_students_with_latest_scores(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    rows = db.query(Assessment).order_by(Assessment.student_code.asc(), Assessment.milestone.desc()).all()
    if current_user.role == "student":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile:
            return []
        rows = [row for row in rows if row.student_code == profile.student_code]
    latest: dict[str, Assessment] = {}
    rank = {"M1": 1, "M2": 2, "M3": 3}
    for row in rows:
        current = latest.get(row.student_code)
        if not current or rank.get(row.milestone, 0) > rank.get(current.milestone, 0):
            latest[row.student_code] = row

    output: list[StudentListItem] = []
    for student_code, item in latest.items():
        flag = db.query(AssessmentFlag).filter(AssessmentFlag.assessment_id == item.id).first()
        output.append(
            StudentListItem(
                student_id=student_code,
                latest_milestone=item.milestone,
                latest_composite_score=item.composite_score,
                latest_tier=item.student_tier,
                intervention_alert=bool(flag.intervention_alert) if flag else False,
            )
        )
    return output


@router.get("/students/{student_code}/milestones", response_model=list[MilestoneSummaryOut])
def get_student_milestone_scores(
    student_code: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    assessments = (
        db.query(Assessment)
        .filter(Assessment.student_code == student_code)
        .order_by(Assessment.assessed_at.asc())
        .all()
    )
    if not assessments:
        raise HTTPException(status_code=404, detail="Student assessment not found")

    output: list[MilestoneSummaryOut] = []
    for item in assessments:
        scores = db.query(DomainScore).filter(DomainScore.assessment_id == item.id).all()
        output.append(
            MilestoneSummaryOut(
                milestone=item.milestone,
                composite_score=item.composite_score,
                student_tier=item.student_tier,
                assessed_at=item.assessed_at,
                domain_scores={s.domain: s.normalized for s in scores},
            )
        )
    return output


@router.get("/students/{student_code}/milestones/{milestone}")
def get_student_milestone_detail(
    student_code: str,
    milestone: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role == "student":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if not profile or profile.student_code != student_code:
            raise HTTPException(status_code=403, detail="You can only access your own data")

    item = (
        db.query(Assessment)
        .filter(Assessment.student_code == student_code, Assessment.milestone == milestone)
        .order_by(Assessment.id.desc())
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Assessment not found")

    domain_scores = db.query(DomainScore).filter(DomainScore.assessment_id == item.id).all()
    dimension_scores = db.query(DimensionScore).filter(DimensionScore.assessment_id == item.id).all()
    flags = db.query(AssessmentFlag).filter(AssessmentFlag.assessment_id == item.id).first()
    evidence = db.query(EvidenceSnippet).filter(EvidenceSnippet.assessment_id == item.id).limit(12).all()

    return {
        "student_id": student_code,
        "milestone": milestone,
        "composite_score": item.composite_score,
        "student_tier": item.student_tier,
        "assessed_at": item.assessed_at,
        "narrative_summary": item.narrative_summary,
        "domain_scores": {
            row.domain: {"normalized": row.normalized, "tier": row.tier}
            for row in domain_scores
        },
        "dimension_scores": {
            row.dimension: {"final_score": row.final_score, "rationale": row.rationale}
            for row in dimension_scores
        },
        "flags": {
            "intervention_alert": bool(flags.intervention_alert) if flags else False,
            "equity_flag": bool(flags.equity_flag) if flags else False,
            "unresolved_dimensions": (flags.unresolved_dimensions.split(",") if flags and flags.unresolved_dimensions else []),
        },
        "evidence_snippets": [
            {"source": e.source_type, "text": e.snippet, "trace_ref": e.trace_ref}
            for e in evidence
        ],
    }


@router.post("/runs")
def create_assessment_run(
    payload: dict,
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(get_current_user)],
):
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher can trigger assessment run")
    run_id = payload.get("run_id") or f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    run = AssessmentRun(
        run_id=run_id,
        project_id=payload.get("project_id"),
        model_name=payload.get("model_name"),
        job_payload_json=json.dumps(payload.get("job_payload", {}), ensure_ascii=False),
        status="queued",
        started_at=None,
        finished_at=None,
    )
    db.add(run)
    db.commit()
    return {"run_id": run_id, "status": "queued", "message": "Run created. Trigger worker to process."}


@router.get("/runs/{run_id}")
def get_assessment_run(
    run_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    run = db.query(AssessmentRun).filter(AssessmentRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run.run_id,
        "status": run.status,
        "project_id": run.project_id,
        "model_name": run.model_name,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


@router.post("/runs/{run_id}/execute")
def execute_assessment_run(
    run_id: str,
    payload: dict,
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(get_current_user)],
):
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher can execute runs")
    run = db.query(AssessmentRun).filter(AssessmentRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.job_payload_json = json.dumps(payload, ensure_ascii=False)
    run.status = "queued"
    db.commit()

    if settings.enable_async_queue:
        return {
            "run_id": run_id,
            "status": "queued",
            "mode": "async",
            "message": "Run enqueued. Start worker to process queued runs.",
        }

    result = _run_assessment_job(db=db, run=run, payload=payload)
    return {"run_id": run_id, "status": "completed", "mode": "sync", "import_result": result}
