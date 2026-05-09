import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.session import get_db
from src.models import ReportArtifact, User
from src.modules.auth.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/reports", tags=["report"])
settings = get_settings()


@router.get("")
def list_reports(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    artifacts = db.query(ReportArtifact).order_by(ReportArtifact.id.desc()).all()
    grouped: dict[str, list[dict]] = {}
    for a in artifacts:
        grouped.setdefault(a.run_id, []).append(
            {
                "id": a.id,
                "name": a.name,
                "type": a.artifact_type,
                "url": f"/api/reports/artifacts/{a.id}",
                "meta": json.loads(a.meta_json) if a.meta_json else {},
            }
        )
    return [{"run_id": run_id, "artifacts": items} for run_id, items in grouped.items()]


@router.get("/artifacts/{artifact_id}")
def get_report_artifact(
    artifact_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
):
    if settings.app_env.lower() != "dev" and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    artifact = db.query(ReportArtifact).filter(ReportArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if artifact.url.startswith("http://") or artifact.url.startswith("https://"):
        return RedirectResponse(url=artifact.url)
    path = Path(artifact.url)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing on server")
    return FileResponse(path)
