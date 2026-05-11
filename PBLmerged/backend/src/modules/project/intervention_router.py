from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models import Intervention, User
from src.modules.auth.deps import require_role
from src.modules.project.intervention_schemas import (
    InterventionCreateRequest,
    InterventionResponse,
    InterventionStatusUpdate,
)

router = APIRouter(prefix="/api/interventions", tags=["interventions"])


@router.get("", response_model=list[InterventionResponse])
def list_interventions(
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role({"teacher"}))],
    student_id: str | None = Query(default=None, description="按学生学号筛选"),
    action_type: str | None = Query(default=None, description="按动作类型筛选"),
    status: str | None = Query(default=None, description="按状态筛选，如 open / done"),
    limit: int = Query(default=100, ge=1, le=500),
):
    q = db.query(Intervention)
    if teacher.id and teacher.id > 0:
        q = q.filter(Intervention.teacher_id == teacher.id)
    if student_id:
        q = q.filter(Intervention.student_code == student_id)
    if action_type:
        q = q.filter(Intervention.action_type == action_type)
    if status:
        q = q.filter(Intervention.status == status)
    rows = q.order_by(Intervention.id.desc()).limit(limit).all()
    return [
        InterventionResponse(
            id=r.id,
            student_id=r.student_code,
            action_type=r.action_type,
            milestone=r.milestone,
            note=r.note,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.patch("/{intervention_id}", response_model=InterventionResponse)
def update_intervention_status(
    intervention_id: int,
    payload: InterventionStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role({"teacher"}))],
):
    row = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Intervention not found")
    if teacher.id and teacher.id > 0 and row.teacher_id is not None and row.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not allowed to modify this record")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return InterventionResponse(
        id=row.id,
        student_id=row.student_code,
        action_type=row.action_type,
        milestone=row.milestone,
        note=row.note,
        status=row.status,
        created_at=row.created_at,
    )


@router.post("", response_model=InterventionResponse)
def create_intervention(
    payload: InterventionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role({"teacher"}))],
):
    record = Intervention(
        teacher_id=teacher.id if teacher.id and teacher.id > 0 else None,
        student_code=payload.student_id,
        action_type=payload.action_type,
        milestone=payload.milestone,
        note=payload.note,
        status="open",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return InterventionResponse(
        id=record.id,
        student_id=record.student_code,
        action_type=record.action_type,
        milestone=record.milestone,
        note=record.note,
        status=record.status,
        created_at=record.created_at,
    )
