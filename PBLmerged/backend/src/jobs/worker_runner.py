from __future__ import annotations

import json
import time
from datetime import datetime

from src.db.session import SessionLocal
from src.models import AssessmentRun
from src.modules.assessment.router import _run_assessment_job


def run_once() -> bool:
    db = SessionLocal()
    try:
        run = (
            db.query(AssessmentRun)
            .filter(AssessmentRun.status == "queued")
            .order_by(AssessmentRun.id.asc())
            .first()
        )
        if not run:
            return False
        payload = json.loads(run.job_payload_json) if run.job_payload_json else {}
        try:
            _run_assessment_job(db=db, run=run, payload=payload)
        except Exception as exc:  # noqa: BLE001
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            db.commit()
            print(f"[failed] run_id={run.run_id} error={exc}")
            return True
        print(f"[done] run_id={run.run_id}")
        return True
    finally:
        db.close()


def main() -> int:
    print("[worker] started, polling queued runs...")
    while True:
        handled = run_once()
        if not handled:
            time.sleep(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
