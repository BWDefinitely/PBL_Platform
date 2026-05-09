from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models import (
    Assessment,
    AssessmentFlag,
    AssessmentRun,
    DimensionScore,
    DomainScore,
    EvidenceSnippet,
    ReportArtifact,
    StudentProfile,
)


def _upsert_student_profile(db: Session, student_code: str) -> None:
    for pending in db.new:
        if isinstance(pending, StudentProfile) and pending.student_code == student_code:
            return
    exists = db.query(StudentProfile).filter(StudentProfile.student_code == student_code).first()
    if exists:
        return
    # keep student records lightweight if user registration is not finished yet
    # profile rows can be reconciled with user accounts later.
    db.add(
        StudentProfile(
            user_id=None,  # backfill placeholder; can be reconciled once user account is linked
            student_code=student_code,
            display_name=student_code,
            class_name=None,
            grade=None,
        )
    )


def import_assessments(
    db: Session,
    run_id: str,
    assessment_json: Path,
    evidence_dir: Path | None = None,
    report_dir: Path | None = None,
) -> dict:
    data = json.loads(assessment_json.read_text(encoding="utf-8"))
    imported = 0

    run = db.query(AssessmentRun).filter(AssessmentRun.run_id == run_id).first()
    if not run:
        run = AssessmentRun(run_id=run_id, status="importing")
        db.add(run)
        db.flush()
    else:
        run.status = "importing"

    for item in data:
        student_code = item["student_id"]
        milestone = item["milestone"]
        _upsert_student_profile(db, student_code)

        existing = (
            db.query(Assessment)
            .filter(Assessment.run_id == run_id, Assessment.student_code == student_code, Assessment.milestone == milestone)
            .first()
        )
        if existing:
            assessment = existing
            # clear old child rows for idempotent re-import
            db.query(DomainScore).filter(DomainScore.assessment_id == assessment.id).delete()
            db.query(DimensionScore).filter(DimensionScore.assessment_id == assessment.id).delete()
            db.query(AssessmentFlag).filter(AssessmentFlag.assessment_id == assessment.id).delete()
            db.query(EvidenceSnippet).filter(EvidenceSnippet.assessment_id == assessment.id).delete()
        else:
            assessment = Assessment(
                run_id=run_id,
                student_code=student_code,
                milestone=milestone,
                composite_score=float(item["composite_score"]),
                student_tier=item["student_tier"],
                assessed_at=item.get("assessed_at"),
                narrative_summary=item.get("narrative_summary"),
                dissent_count=len(item.get("dissent_log", [])),
            )
            db.add(assessment)
            db.flush()

        assessment.composite_score = float(item["composite_score"])
        assessment.student_tier = item["student_tier"]
        assessment.assessed_at = item.get("assessed_at")
        assessment.narrative_summary = item.get("narrative_summary")
        assessment.dissent_count = len(item.get("dissent_log", []))

        for domain, payload in item.get("domain_scores", {}).items():
            db.add(
                DomainScore(
                    assessment_id=assessment.id,
                    domain=domain,
                    normalized=float(payload.get("normalized", 0)),
                    tier=payload.get("tier"),
                )
            )

        for dim, payload in item.get("dimension_scores", {}).items():
            db.add(
                DimensionScore(
                    assessment_id=assessment.id,
                    dimension=dim,
                    final_score=payload.get("final_score"),
                    rationale=payload.get("rationale"),
                )
            )

        flags = item.get("flags", {})
        db.add(
            AssessmentFlag(
                assessment_id=assessment.id,
                intervention_alert=bool(flags.get("intervention_alert", False)),
                equity_flag=bool(flags.get("equity_flag", False)),
                unresolved_dimensions=",".join(flags.get("unresolved_dimensions", [])),
            )
        )

        if evidence_dir:
            raw_path = evidence_dir / f"{student_code}_{milestone}.json"
            if raw_path.exists():
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
                snippets: list[tuple[str, str, str | None]] = []
                if raw.get("transcripts"):
                    snippets.append(("transcripts", raw["transcripts"][:600], None))
                if raw.get("doc_diffs"):
                    snippets.append(("doc_diffs", raw["doc_diffs"][:600], None))
                collab = raw.get("collab_trace", {})
                sections = collab.get("document_work", {}).get("latest_sections", [])
                for sec in sections[:6]:
                    snippets.append(("collab_trace", sec.get("excerpt", "")[:300], sec.get("section_title")))
                for src, text, ref in snippets:
                    if text.strip():
                        db.add(EvidenceSnippet(assessment_id=assessment.id, source_type=src, snippet=text, trace_ref=ref))

        imported += 1

    if report_dir and report_dir.exists():
        for p in sorted(report_dir.glob("*")):
            if p.suffix.lower() not in {".png", ".json", ".csv", ".md"}:
                continue
            typ = "chart_png" if p.suffix.lower() == ".png" else "report_file"
            existing_artifact = (
                db.query(ReportArtifact)
                .filter(ReportArtifact.run_id == run_id, ReportArtifact.name == p.name)
                .first()
            )
            if existing_artifact:
                existing_artifact.artifact_type = typ
                existing_artifact.url = str(p)
                existing_artifact.meta_json = json.dumps({"size_bytes": p.stat().st_size})
            else:
                db.add(
                    ReportArtifact(
                        run_id=run_id,
                        artifact_type=typ,
                        name=p.name,
                        url=str(p),
                        meta_json=json.dumps({"size_bytes": p.stat().st_size}),
                    )
                )

    run.status = "completed"
    db.commit()
    return {"run_id": run_id, "imported": imported}


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotent import of assessment results into assessment-api DB.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--assessment-json", required=True)
    parser.add_argument("--evidence-dir", default=None)
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = import_assessments(
            db=db,
            run_id=args.run_id,
            assessment_json=Path(args.assessment_json),
            evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
            report_dir=Path(args.report_dir) if args.report_dir else None,
        )
        print(json.dumps(result, ensure_ascii=False))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
