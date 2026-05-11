"""AutoGen integration router.

Wraps the standalone `backend/autogen/` toolset so it can be triggered
from the frontend as a test-only "AI 生成数据" feature.

Design:
- Each run gets a dedicated directory under `backend/autogen/runs/<job_id>/`.
- The autogen process is launched with `--output-dir runs/<job_id>` so all
  generated artifacts (and the captured stdout log) live inside that folder.
- Browsing is strictly scoped to `runs/` — users cannot wander into source code.
- Running jobs can be cancelled; cancellation kills the process tree AND
  deletes the incomplete run directory.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/autogen", tags=["autogen"])

# backend/src/modules/autogen/router.py -> backend/autogen
AUTOGEN_ROOT = Path(__file__).resolve().parents[3] / "autogen"
RUNS_ROOT = AUTOGEN_ROOT / "runs"
# Unified LLM config shared with generator-service. Single source of truth.
UNIFIED_LLM_CONFIG = AUTOGEN_ROOT.parent / "llm_config.json"

# In-memory job registry. Test-only feature, no DB persistence needed.
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()
# job_id -> Popen handle, used for cancellation
_PROCS: dict[str, subprocess.Popen] = {}


class RunRequest(BaseModel):
    mode: str = "timeline"  # "timeline" | "legacy"
    smoke_test: bool = True
    dry_run: bool = False
    only_groups: Optional[str] = None
    # Empty string => use the unified backend/llm_config.json shared with
    # generator-service. Set to a custom path only when you need to override.
    config_list_file: str = ""
    estimate_cost: bool = False


def _build_command(req: RunRequest, data_dir_rel: str) -> list[str]:
    script = (
        "run_timeline_experiments.py" if req.mode == "timeline" else "run_experiments.py"
    )
    # Route through `_run_entry.py` so a logging filter is installed before
    # autogen imports — this drops the spammy "Model ... is not found. The
    # cost will be 0." warning that would otherwise pollute the run log.
    cmd = [sys.executable, "-u", "_run_entry.py", script]
    if req.dry_run:
        cmd.append("--dry-run")
    else:
        # Use an absolute path so the autogen process resolves the unified
        # file regardless of its cwd (= AUTOGEN_ROOT).
        config_path = req.config_list_file or str(UNIFIED_LLM_CONFIG)
        cmd += ["--config-list-file", config_path]
    if req.smoke_test and req.mode == "timeline":
        cmd.append("--smoke-test")
    if req.estimate_cost and req.mode == "timeline":
        cmd.append("--estimate-cost")
    if req.only_groups:
        cmd += ["--only-groups", req.only_groups]
    cmd += ["--output-dir", data_dir_rel]
    return cmd


def _rmtree_quiet(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


def _run_job(job_id: str, cmd: list[str], run_dir: Path) -> None:
    job = _JOBS[job_id]
    logs_dir = run_dir / "logs"
    data_dir = run_dir / "data"
    logs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "run.log"
    job["log_path"] = str(log_path)
    job["run_dir"] = str(run_dir)
    job["logs_dir"] = str(logs_dir)
    job["data_dir"] = str(data_dir)
    proc = None
    try:
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"$ {' '.join(cmd)}\n")
            lf.write(f"# logs_dir={logs_dir}\n")
            lf.write(f"# data_dir={data_dir}\n\n")
            lf.flush()
            popen_kwargs = dict(
                cwd=str(AUTOGEN_ROOT),
                stdout=lf,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            if sys.platform.startswith("win"):
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_kwargs["start_new_session"] = True
            proc = subprocess.Popen(cmd, **popen_kwargs)
            _PROCS[job_id] = proc
            job["pid"] = proc.pid
            ret = proc.wait()
        if job.get("status") == "cancelled":
            # Keep the partial outputs and log on disk for inspection — the
            # user explicitly asked us not to wipe cancelled runs.
            job["return_code"] = ret
        else:
            job["status"] = "success" if ret == 0 else "failed"
            job["return_code"] = ret
    except Exception as e:  # noqa: BLE001
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        job["finished_at"] = datetime.utcnow().isoformat()
        _PROCS.pop(job_id, None)


def _terminate_proc(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if sys.platform.startswith("win"):
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:  # noqa: BLE001
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


@router.get("/status")
def status():
    return {
        "autogen_root": str(AUTOGEN_ROOT),
        "exists": AUTOGEN_ROOT.exists(),
        "runs_root": str(RUNS_ROOT),
        "runs_exists": RUNS_ROOT.exists(),
    }


@router.post("/run")
def run(req: RunRequest):
    if not AUTOGEN_ROOT.exists():
        raise HTTPException(500, f"autogen folder not found at {AUTOGEN_ROOT}")
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    run_dir = RUNS_ROOT / job_id
    data_dir_rel = f"runs/{job_id}/data"
    cmd = _build_command(req, data_dir_rel)
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "id": job_id,
            "status": "running",
            "cmd": cmd,
            "run_dir": str(run_dir),
            "logs_dir": str(run_dir / "logs"),
            "data_dir": str(run_dir / "data"),
            "started_at": datetime.utcnow().isoformat(),
        }
    t = threading.Thread(target=_run_job, args=(job_id, cmd, run_dir), daemon=True)
    t.start()
    return {
        "job_id": job_id,
        "cmd": cmd,
        "run_dir": f"runs/{job_id}",
        "data_dir": data_dir_rel,
        "logs_dir": f"runs/{job_id}/logs",
    }


@router.get("/jobs")
def list_jobs():
    with _JOBS_LOCK:
        return sorted(_JOBS.values(), key=lambda j: j.get("started_at", ""), reverse=True)


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@router.get("/jobs/{job_id}/log", response_class=PlainTextResponse)
def get_job_log(job_id: str, tail: int = 500):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    log_path_str = job.get("log_path")
    if not log_path_str:
        return ""
    log_path = Path(log_path_str)
    if not log_path.is_file():
        return ""
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-tail:])


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Kill a running job. The partial outputs on disk are preserved; use
    DELETE /jobs/{id} to remove them when you no longer need them."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != "running":
        raise HTTPException(400, f"job is not running (status={job['status']})")
    # Mark first so _run_job's finalizer keeps the dir instead of finalising
    # the status to success/failed.
    job["status"] = "cancelled"
    proc = _PROCS.get(job_id)
    if proc is not None:
        _terminate_proc(proc)
    return {"ok": True, "job_id": job_id, "status": "cancelled"}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Remove a finished job record and its run directory."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] == "running":
        raise HTTPException(400, "cancel the job before deleting it")
    run_dir = job.get("run_dir")
    if run_dir:
        _rmtree_quiet(Path(run_dir))
    with _JOBS_LOCK:
        _JOBS.pop(job_id, None)
    return {"ok": True}


# --- Browsing: strictly scoped to RUNS_ROOT ---------------------------------

def _safe_resolve_run(rel: str) -> Path:
    """Resolve `rel` strictly under RUNS_ROOT. Empty string == RUNS_ROOT."""
    base = RUNS_ROOT.resolve()
    p = (base / rel).resolve() if rel else base
    if p != base and base not in p.parents:
        raise HTTPException(400, "path escapes runs root")
    return p


def _rel_to_runs(p: Path) -> str:
    base = RUNS_ROOT.resolve()
    if p == base:
        return ""
    return str(p.relative_to(base)).replace("\\", "/")


@router.get("/browse")
def browse(path: str = Query("", description="path relative to runs/")):
    if not RUNS_ROOT.exists():
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    target = _safe_resolve_run(path)
    if not target.exists():
        raise HTTPException(404, f"not found: {path}")
    if target.is_file():
        return {
            "type": "file",
            "path": _rel_to_runs(target),
            "size": target.stat().st_size,
        }
    entries = []
    for child in sorted(target.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
        try:
            stat = child.stat()
        except OSError:
            continue
        entries.append(
            {
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
                "size": stat.st_size if child.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": _rel_to_runs(child),
            }
        )
    base = RUNS_ROOT.resolve()
    parent = None
    if target != base:
        parent = _rel_to_runs(target.parent) if target.parent != base else ""
    return {
        "type": "dir",
        "path": _rel_to_runs(target),
        "parent": parent,
        "entries": entries,
    }


@router.get("/file", response_class=PlainTextResponse)
def read_file(path: str = Query(...), max_bytes: int = 200_000):
    target = _safe_resolve_run(path)
    if not target.is_file():
        raise HTTPException(404, "file not found")
    size = target.stat().st_size
    with open(target, "rb") as f:
        data = f.read(max_bytes)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    suffix = f"\n\n... [truncated, total {size} bytes]" if size > max_bytes else ""
    return text + suffix


@router.get("/download")
def download(path: str = Query(...)):
    target = _safe_resolve_run(path)
    if not target.is_file():
        raise HTTPException(404, "file not found")
    return FileResponse(str(target), filename=target.name)


@router.post("/reveal")
def reveal_in_explorer(path: str = Query("")):
    """Open the path in the host OS file explorer (server-side, scoped to runs/)."""
    target = _safe_resolve_run(path)
    if not target.exists():
        raise HTTPException(404, "path not found")
    try:
        if sys.platform.startswith("win"):
            if target.is_file():
                subprocess.Popen(["explorer", "/select,", str(target)])
            else:
                subprocess.Popen(["explorer", str(target)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return {"ok": True, "opened": str(target)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"failed to open: {e}") from e
