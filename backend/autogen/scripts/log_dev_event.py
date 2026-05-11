from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a structured entry to docs/dev_journal.md.")
    parser.add_argument("--project-root", default=".", help="Target project directory.")
    parser.add_argument("--event-type", required=True, help="discussion | code_change | debug | run | decision")
    parser.add_argument("--title", required=True, help="Short event title.")
    parser.add_argument("--goal", required=True, help="Goal of this step.")
    parser.add_argument("--what-happened", required=True, help="What happened.")
    parser.add_argument("--problem", default="N/A", help="Problem encountered.")
    parser.add_argument("--root-cause", default="N/A", help="Root cause.")
    parser.add_argument("--solution", default="N/A", help="Solution used.")
    parser.add_argument("--validation", default="N/A", help="How it was validated.")
    parser.add_argument("--impact", default="N/A", help="Impact of the change.")
    parser.add_argument("--next-step", default="N/A", help="Next follow-up step.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    journal_path = project_root / "docs" / "dev_journal.md"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    if not journal_path.exists():
        journal_path.write_text("# Development Journal\n\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""## {timestamp} | {args.event_type} | {args.title}

### Goal

{args.goal}

### What Happened

{args.what_happened}

### Problem

{args.problem}

### Root Cause

{args.root_cause}

### Solution

{args.solution}

### Validation

{args.validation}

### Impact

{args.impact}

### Next

{args.next_step}

"""
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    print(f"Appended event to: {journal_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
