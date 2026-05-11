from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models import Project, User
from src.modules.auth.deps import get_current_user, require_role
from src.modules.project.schemas import ProjectCreateRequest, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["project"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    query = db.query(Project)
    if user.role == "teacher":
        query = query.filter(Project.owner_teacher_id == user.id)
    return [ProjectResponse(id=p.id, name=p.name, term=p.term, status=p.status) for p in query.order_by(Project.id.desc()).all()]


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role({"teacher"}))],
):
    project = Project(owner_teacher_id=teacher.id, name=payload.name, term=payload.term, status=payload.status)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(id=project.id, name=project.name, term=project.term, status=project.status)
