from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


PLACEHOLDERS = {
    "__DATE__": datetime.now().strftime("%Y-%m-%d"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a project recording skeleton.")
    parser.add_argument("--project-root", default=".", help="Target project directory.")
    parser.add_argument("--project-name", help="Human-readable project name.")
    parser.add_argument(
        "--mode",
        choices=["new", "existing"],
        default="existing",
        help="Use 'new' for a fresh project and 'existing' to add missing files only.",
    )
    parser.add_argument(
        "--template-root",
        default=str(Path(__file__).resolve().parents[1] / "project_recording_template"),
        help="Template source directory.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def render_text(text: str, project_name: str, project_slug: str) -> str:
    rendered = text.replace("__PROJECT_NAME__", project_name)
    rendered = rendered.replace("__PROJECT_SLUG__", project_slug)
    for key, value in PLACEHOLDERS.items():
        rendered = rendered.replace(key, value)
    return rendered


def copy_templates(project_root: Path, template_root: Path, project_name: str, force: bool) -> None:
    project_slug = slugify(project_name)
    for template_path in template_root.rglob("*"):
        if template_path.is_dir():
            continue
        relative = template_path.relative_to(template_root)
        target_relative = normalize_template_path(relative)
        target_path = project_root / target_relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and not force:
            continue
        content = template_path.read_text(encoding="utf-8")
        target_path.write_text(render_text(content, project_name, project_slug), encoding="utf-8")


def normalize_template_path(relative: Path) -> Path:
    name = relative.name
    if name.endswith(".template.md"):
        return relative.with_name(name.replace(".template.md", ".md"))
    if name.endswith(".md.template"):
        return relative.with_name(name.replace(".md.template", ".md"))
    if name.endswith(".template"):
        return relative.with_name(name.replace(".template", ""))
    return relative


def slugify(project_name: str) -> str:
    chars = []
    for char in project_name.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "project"


def ensure_runtime_dirs(project_root: Path) -> None:
    for relative in ["docs", "scripts", "records", "outputs"]:
        (project_root / relative).mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    template_root = Path(args.template_root).resolve()
    project_name = args.project_name or project_root.name

    ensure_runtime_dirs(project_root)
    copy_templates(project_root, template_root, project_name, args.force)

    print(f"Initialized recording skeleton at: {project_root}")
    print(f"Mode: {args.mode}")
    print("Created or preserved docs/, outputs/, and records/ directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
