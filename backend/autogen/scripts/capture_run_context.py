from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture run context into records/run_contexts.")
    parser.add_argument("--project-root", default=".", help="Target project directory.")
    parser.add_argument("--label", required=True, help="Short label for this run context.")
    parser.add_argument("--command", required=True, help="Executed command.")
    parser.add_argument("--status", default="unknown", help="Run status.")
    parser.add_argument("--notes", default="", help="Optional notes.")
    parser.add_argument("--config-file", action="append", default=[], help="Config file path.")
    parser.add_argument("--output-path", action="append", default=[], help="Output path.")
    return parser.parse_args()


def git_value(project_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    target_dir = project_root / "records" / "run_contexts"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "label": args.label,
        "command": args.command,
        "status": args.status,
        "notes": args.notes,
        "project_root": str(project_root),
        "git_branch": git_value(project_root, "branch", "--show-current"),
        "git_commit": git_value(project_root, "rev-parse", "HEAD"),
        "config_files": args.config_file,
        "output_paths": args.output_path,
    }
    output_path = target_dir / f"{timestamp}__{slugify(args.label)}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Captured run context at: {output_path}")
    return 0


def slugify(value: str) -> str:
    chars = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "run"


if __name__ == "__main__":
    raise SystemExit(main())
