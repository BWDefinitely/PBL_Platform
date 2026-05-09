from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models import ActivityEvent, Assessment, ChatMessage, DocContribution, PresentationRecord


def _truncate_for_refresh(db: Session) -> None:
    db.query(ChatMessage).delete()
    db.query(DocContribution).delete()
    db.query(PresentationRecord).delete()
    db.query(ActivityEvent).delete()


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _pick(row: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        val = row.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if text != "":
            return text
    return default


def _to_int(value: str | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _to_float(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        # Support typical ISO strings like 2024-10-07T21:12:00.000Z
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_project_time_bounds(*datasets: list[dict]) -> dict[str, tuple[datetime, datetime]]:
    by_project: dict[str, list[datetime]] = {}
    for rows in datasets:
        for row in rows:
            project_id = _pick(row, ["project_id", "Project-ID", "project", "projectId"], default="unknown")
            dt = _parse_dt(_pick(row, ["timestamp", "sent_at", "happened_at", "created_at"]))
            if not dt:
                continue
            by_project.setdefault(project_id or "unknown", []).append(dt)

    bounds: dict[str, tuple[datetime, datetime]] = {}
    for project_id, points in by_project.items():
        points.sort()
        bounds[project_id] = (points[0], points[-1])
    return bounds


def _infer_milestone(row: dict, project_bounds: dict[str, tuple[datetime, datetime]]) -> str:
    explicit = _pick(row, ["milestone", "Milestone", "phase", "Phase"])
    if explicit:
        text = explicit.upper()
        if text in {"M1", "M2", "M3"}:
            return text

    project_id = _pick(row, ["project_id", "Project-ID", "project", "projectId"], default="unknown") or "unknown"
    dt = _parse_dt(_pick(row, ["timestamp", "sent_at", "happened_at", "created_at"]))
    if dt and project_id in project_bounds:
        start, end = project_bounds[project_id]
        if end > start:
            ratio = (dt - start).total_seconds() / (end - start).total_seconds()
            if ratio < 1 / 3:
                return "M1"
            if ratio < 2 / 3:
                return "M2"
            return "M3"

    # Fallback: infer by section index/id if timestamp is missing.
    section_idx = _to_int(_pick(row, ["Section-Index", "section_index", "Section-ID", "section_id"]))
    if section_idx is not None:
        if section_idx <= 2:
            return "M1"
        if section_idx <= 4:
            return "M2"
        return "M3"
    return "M2"


def _build_student_alias_map(db: Session, *datasets: list[dict]) -> dict[str, str]:
    canonical = {
        row[0]
        for row in db.query(Assessment.student_code).distinct().all()
        if row[0]
    }
    if not canonical:
        return {}

    observed: set[str] = set()
    for rows in datasets:
        for row in rows:
            sid = _pick(row, ["student_id", "student", "Actor-Name", "actor_name", "actor"])
            if sid:
                observed.add(sid)

    alias_map: dict[str, str] = {}
    for sid in observed:
        if sid in canonical:
            alias_map[sid] = sid
            continue

        # First try constrained matching: same prefix and suffix is usually safer.
        constrained = [
            name
            for name in canonical
            if name[:2].lower() == sid[:2].lower() and name[-1:].lower() == sid[-1:].lower()
        ]
        candidates = constrained if constrained else list(canonical)
        scored = sorted(
            ((SequenceMatcher(None, sid.lower(), cand.lower()).ratio(), cand) for cand in candidates),
            reverse=True,
        )
        best_ratio, best_name = scored[0] if scored else (0.0, sid)
        alias_map[sid] = best_name if best_ratio >= 0.72 else sid
    return alias_map


def import_process_dataset(dataset_dir: Path, refresh: bool = True) -> dict:
    db = SessionLocal()
    try:
        if refresh:
            _truncate_for_refresh(db)

        messages = _read_csv(dataset_dir / "messages.csv")
        content = _read_csv(dataset_dir / "content.csv")
        presentations = _read_csv(dataset_dir / "presentations.csv")
        events = _read_csv(dataset_dir / "events.csv")
        bounds = _build_project_time_bounds(messages, content, presentations, events)
        alias_map = _build_student_alias_map(db, messages, content, presentations, events)

        generated_milestones = 0
        generated_student_codes = 0
        remapped_student_codes = 0

        for row in messages:
            raw_student_code = _pick(row, ["student_id", "student", "Actor-Name", "actor_name", "actor"], default="unknown_student")
            student_code = alias_map.get(raw_student_code, raw_student_code)
            if raw_student_code != student_code:
                remapped_student_codes += 1
            if student_code == "unknown_student":
                generated_student_codes += 1
            milestone = _infer_milestone(row, bounds)
            if not _pick(row, ["milestone", "Milestone", "phase", "Phase"]):
                generated_milestones += 1
            db.add(
                ChatMessage(
                    student_code=student_code,
                    project_id=_pick(row, ["project_id", "Project-ID", "project", "projectId"]),
                    milestone=milestone,
                    sent_at=_pick(row, ["timestamp", "sent_at", "created_at"]),
                    content=_pick(row, ["message", "Message-Text", "content", "text"], default="") or "",
                )
            )

        for row in content:
            raw_student_code = _pick(row, ["student_id", "student", "Actor-Name", "actor_name", "actor"], default="unknown_student")
            student_code = alias_map.get(raw_student_code, raw_student_code)
            if raw_student_code != student_code:
                remapped_student_codes += 1
            if student_code == "unknown_student":
                generated_student_codes += 1
            milestone = _infer_milestone(row, bounds)
            if not _pick(row, ["milestone", "Milestone", "phase", "Phase"]):
                generated_milestones += 1
            db.add(
                DocContribution(
                    student_code=student_code,
                    project_id=_pick(row, ["project_id", "Project-ID", "project", "projectId"]),
                    milestone=milestone,
                    section_title=_pick(row, ["section_title", "Section-Title", "section", "Section-ID"]),
                    content_excerpt=(_pick(row, ["content", "Section-Content", "excerpt"], default="") or "")[:1000],
                    source_count=_to_int(_pick(row, ["source_count", "Source-Count"])),
                )
            )

        for row in presentations:
            raw_student_code = _pick(row, ["student_id", "student", "Actor-Name", "actor_name", "actor"], default="unknown_student")
            student_code = alias_map.get(raw_student_code, raw_student_code)
            if raw_student_code != student_code:
                remapped_student_codes += 1
            if student_code == "unknown_student":
                generated_student_codes += 1
            milestone = _infer_milestone(row, bounds)
            if not _pick(row, ["milestone", "Milestone", "phase", "Phase"]):
                generated_milestones += 1
            structure = _to_float(_pick(row, ["clarity_score", "structure_score_proxy"]))
            academic = _to_float(_pick(row, ["academic_score_proxy"]))
            clarity = structure if structure is not None else academic
            db.add(
                PresentationRecord(
                    student_code=student_code,
                    project_id=_pick(row, ["project_id", "Project-ID", "project", "projectId"]),
                    milestone=milestone,
                    title=_pick(row, ["title", "presentation_title", "presentation_text", "uuid"]),
                    words=_to_int(_pick(row, ["word_count", "words"])),
                    clarity_score=clarity,
                )
            )

        for row in events:
            raw_student_code = _pick(row, ["student_id", "student", "Actor-Name", "actor_name", "actor"], default="unknown_student")
            student_code = alias_map.get(raw_student_code, raw_student_code)
            if raw_student_code != student_code:
                remapped_student_codes += 1
            if student_code == "unknown_student":
                generated_student_codes += 1
            milestone = _infer_milestone(row, bounds)
            if not _pick(row, ["milestone", "Milestone", "phase", "Phase"]):
                generated_milestones += 1
            db.add(
                ActivityEvent(
                    student_code=student_code,
                    project_id=_pick(row, ["project_id", "Project-ID", "project", "projectId"]),
                    milestone=milestone,
                    event_type=_pick(row, ["event_type", "type", "Verb", "Object-Type"]),
                    happened_at=_pick(row, ["timestamp", "happened_at", "created_at"]),
                    metadata_json=json.dumps(row, ensure_ascii=False),
                )
            )

        db.commit()
        return {
            "messages": len(messages),
            "content": len(content),
            "presentations": len(presentations),
            "events": len(events),
            "generated_milestones": generated_milestones,
            "generated_student_codes": generated_student_codes,
            "remapped_student_codes": remapped_student_codes,
        }
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import process CSV files (messages/content/presentations/events) into DB.")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--no-refresh", action="store_true")
    args = parser.parse_args()
    result = import_process_dataset(Path(args.dataset_dir), refresh=not args.no_refresh)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
