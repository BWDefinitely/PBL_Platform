from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill a project history phase into docs/dev_journal.md.")
    parser.add_argument("--project-root", default=".", help="Target project directory.")
    parser.add_argument("--phase", required=True, help="Phase title.")
    parser.add_argument("--goal", required=True, help="Phase goal.")
    parser.add_argument("--summary", required=True, help="What was completed in this phase.")
    parser.add_argument("--problem", default="N/A", help="Main problem in this phase.")
    parser.add_argument("--root-cause", default="N/A", help="Main root cause.")
    parser.add_argument("--solution", default="N/A", help="Main solution.")
    parser.add_argument("--validation", default="N/A", help="Validation summary.")
    parser.add_argument("--impact", default="N/A", help="Impact summary.")
    parser.add_argument("--next-step", default="N/A", help="Next step after this phase.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    journal_path = Path(args.project_root).resolve() / "docs" / "dev_journal.md"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    if not journal_path.exists():
        journal_path.write_text("# Development Journal\n\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""## {timestamp} | backfill | {args.phase}

### Goal

{args.goal}

### What Happened

{args.summary}

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

    print(f"Backfilled project history into: {journal_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
