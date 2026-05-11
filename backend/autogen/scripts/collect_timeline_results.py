from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect multiple timeline_v2 run directories into one reviewable collection."
    )
    parser.add_argument(
        "--collection-dir",
        required=True,
        help="Target collection directory. Existing summary files will be overwritten.",
    )
    parser.add_argument(
        "--run-dir",
        action="append",
        default=[],
        help="A run directory containing final_dataset.json or state.json. Can be repeated.",
    )
    parser.add_argument(
        "--scan-collection-runs",
        action="store_true",
        help="Also scan collection-dir/runs/* as source run directories.",
    )
    parser.add_argument(
        "--experiment-file",
        default="configs/experiment_groups_persona_composition_urgency.json",
        help="Optional experiment file used to list expected group IDs.",
    )
    parser.add_argument(
        "--copy-source-files",
        action="store_true",
        help="Copy each source run's core output files into collection/source_runs/.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    collection_dir = resolve_path(args.collection_dir)
    run_dirs = [resolve_path(path) for path in args.run_dir]
    if args.scan_collection_runs:
        run_dirs.extend(scan_collection_runs(collection_dir))
    run_dirs = dedupe_paths(run_dirs)
    experiment_path = resolve_path(args.experiment_file)

    collection_dir.mkdir(parents=True, exist_ok=True)
    groups_dir = collection_dir / "groups"
    groups_dir.mkdir(parents=True, exist_ok=True)

    expected_groups = load_expected_groups(experiment_path)
    records = collect_project_records(run_dirs)
    latest_records = choose_latest_record_per_group(records)

    combined_dataset = build_combined_dataset(
        collection_dir=collection_dir,
        run_dirs=run_dirs,
        records=latest_records,
        expected_groups=expected_groups,
    )
    overview = build_group_overview(
        records=latest_records,
        expected_groups=expected_groups,
    )

    write_group_files(groups_dir, latest_records)
    write_collection_files(collection_dir, combined_dataset, overview)
    if args.copy_source_files:
        copy_source_files(collection_dir, run_dirs)

    print(f"Collection written to: {collection_dir}")
    print(f"Groups summarized: {len(latest_records)}")
    print(f"Expected groups: {len(expected_groups)}")
    print(f"Missing groups: {len(overview['missing_groups'])}")
    print(f"Partial groups: {len(overview['partial_groups'])}")
    return 0


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def scan_collection_runs(collection_dir: Path) -> list[Path]:
    runs_dir = collection_dir / "runs"
    if not runs_dir.exists():
        return []
    return [path for path in runs_dir.iterdir() if path.is_dir()]


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path.resolve()).lower()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def format_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_expected_groups(experiment_path: Path) -> list[dict[str, Any]]:
    if not experiment_path.exists():
        return []
    payload = read_json(experiment_path)
    if "extends" in payload:
        base_path = Path(payload["extends"])
        if not base_path.is_absolute():
            base_path = experiment_path.parent / base_path
        base_payload = read_json(base_path)
        groups = base_payload.get("groups", [])
    else:
        groups = payload.get("groups", [])
    return [
        {
            "group_id": group["group_id"],
            "member_role_ids": group.get("member_role_ids", []),
            "scenario_id": group.get("scenario_id"),
            "tags": group.get("tags", []),
        }
        for group in groups
        if "smoke_test" not in group.get("tags", [])
    ]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_project_records(run_dirs: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        dataset_path = run_dir / "final_dataset.json"
        if not dataset_path.exists():
            dataset_path = run_dir / "state.json"
        if not dataset_path.exists():
            continue
        dataset = read_json(dataset_path)
        source_status = dataset.get("status", "unknown")
        for project in dataset.get("projects", []):
            group_id = infer_group_id(project)
            records.append(
                {
                    "group_id": group_id,
                    "project": project,
                    "source_run_dir": format_path(run_dir),
                    "source_dataset_path": format_path(dataset_path),
                    "source_run_status": source_status,
                    "generated_at": dataset.get("generated_at"),
                    "updated_at": dataset.get("updated_at"),
                    "model_config_summary": dataset.get("model_config_summary"),
                }
            )
    return records


def infer_group_id(project: dict[str, Any]) -> str:
    project_id = str(project.get("project_id", "unknown"))
    if "__project_" in project_id:
        return project_id.split("__project_", 1)[0]
    return project.get("group_id") or project_id


def choose_latest_record_per_group(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: dict[str, dict[str, Any]] = {}
    for record in records:
        group_id = record["group_id"]
        previous = ranked.get(group_id)
        if previous is None or record_rank(record) > record_rank(previous):
            ranked[group_id] = record
    return [ranked[key] for key in sorted(ranked)]


def record_rank(record: dict[str, Any]) -> tuple[int, int, str]:
    project = record["project"]
    is_completed = 1 if project.get("status") == "completed" else 0
    generated_sessions = int(
        project.get("generated_session_count") or len(project.get("sessions", []))
    )
    updated_at = str(record.get("updated_at") or record.get("generated_at") or "")
    return (generated_sessions, is_completed, updated_at)


def build_combined_dataset(
    collection_dir: Path,
    run_dirs: list[Path],
    records: list[dict[str, Any]],
    expected_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "collection_name": collection_dir.name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_run_dirs": [format_path(path) for path in run_dirs],
        "expected_group_ids": [group["group_id"] for group in expected_groups],
        "project_count": len(records),
        "projects": [record["project"] for record in records],
    }


def build_group_overview(
    records: list[dict[str, Any]],
    expected_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_by_id = {group["group_id"]: group for group in expected_groups}
    record_by_id = {record["group_id"]: record for record in records}
    summaries = []
    for group_id in sorted(record_by_id):
        record = record_by_id[group_id]
        project = record["project"]
        sessions = project.get("sessions", [])
        all_messages = [
            message
            for session in sessions
            for message in session.get("messages", [])
        ]
        session_outcomes = Counter(session.get("session_outcome") for session in sessions)
        role_counts = Counter(
            message.get("role_id") or message.get("speaker")
            for message in all_messages
        )
        final_status = classify_group_result(project)
        summaries.append(
            {
                "group_id": group_id,
                "expected_members": expected_by_id.get(group_id, {}).get("member_role_ids", []),
                "scenario_id": expected_by_id.get(group_id, {}).get("scenario_id"),
                "source_run_dir": record["source_run_dir"],
                "source_dataset_path": record["source_dataset_path"],
                "source_run_status": record["source_run_status"],
                "project_id": project.get("project_id"),
                "project_status": project.get("status"),
                "project_outcome": project.get("project_outcome"),
                "planned_session_count": project.get("planned_session_count"),
                "generated_session_count": project.get("generated_session_count"),
                "message_count": len(all_messages),
                "event_count": len(project.get("events", [])),
                "session_outcomes": dict(session_outcomes),
                "speaker_message_counts": dict(role_counts),
                "profile_interpretation": final_status,
                "review_files": {
                    "conversation": f"groups/{group_id}/conversation_timeline.txt",
                    "behavior": f"groups/{group_id}/behavior_timeline.txt",
                    "project_json": f"groups/{group_id}/project.json",
                    "summary": f"groups/{group_id}/summary.md",
                },
            }
        )

    missing_groups = sorted(set(expected_by_id) - set(record_by_id))
    partial_groups = [
        item["group_id"]
        for item in summaries
        if item["project_status"] != "completed"
        or item["generated_session_count"] != item["planned_session_count"]
    ]
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "generated_group_count": len(summaries),
        "expected_group_count": len(expected_groups),
        "missing_groups": missing_groups,
        "partial_groups": partial_groups,
        "groups": summaries,
    }


def classify_group_result(project: dict[str, Any]) -> str:
    group_id = infer_group_id(project)
    outcome = project.get("project_outcome")
    generated = project.get("generated_session_count")
    planned = project.get("planned_session_count")
    sessions = project.get("sessions", [])
    text = " ".join(
        str(message.get("content", ""))
        for session in sessions
        for message in session.get("messages", [])
    )
    has_conflict_language = any(
        token in text
        for token in [
            "不行",
            "别废话",
            "算了",
            "吵",
            "谈不拢",
            "拖",
            "放弃",
            "没人做",
        ]
    )

    if "high_dysfunction" in group_id:
        if outcome in {"abandoned", "stalled"} or has_conflict_language:
            return "高失调组表现符合预期：冲突、拖延或不了了之倾向明显。"
        return "高失调组已生成，但结局偏推进，需要人工复查是否过于顺利。"
    if "positive" in group_id or "execution_heavy" in group_id:
        if outcome in {"completed", "forced_submission"} and generated == planned:
            return "正向/执行型组表现符合预期：能持续推进到交付或被迫交付。"
        return "正向/执行型组未充分完成，需要检查是否被过早截断。"
    if any(token in group_id for token in ["free_rider", "dominator", "blocker", "lone_wolf"]):
        if outcome in {"abandoned", "stalled"} or has_conflict_language:
            return "混合失调组表现符合预期：出现阻滞、支配、搭便车或冲突迹象。"
        return "混合失调组仍能推进，需要人工判断角色差异是否足够明显。"
    return "已生成，需要结合对话内容人工复查差异。"


def write_group_files(groups_dir: Path, records: list[dict[str, Any]]) -> None:
    for record in records:
        group_id = record["group_id"]
        project = record["project"]
        target = groups_dir / group_id
        target.mkdir(parents=True, exist_ok=True)
        (target / "project.json").write_text(
            json.dumps(project, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (target / "conversation_timeline.txt").write_text(
            format_project_conversation(project),
            encoding="utf-8",
        )
        (target / "behavior_timeline.txt").write_text(
            format_project_behavior(project),
            encoding="utf-8",
        )
        (target / "summary.md").write_text(
            format_group_summary(record),
            encoding="utf-8",
        )


def format_project_conversation(project: dict[str, Any]) -> str:
    lines = [
        f"项目：{project.get('project_id')}",
        f"场景：{project.get('scenario', {}).get('title')}",
        f"结局：{project.get('project_outcome')}",
        "",
    ]
    for session in project.get("sessions", []):
        lines.extend(
            [
                f"===== 第 {session.get('meeting_index')} 次对话 =====",
                f"session_outcome: {session.get('session_outcome')}",
                f"project_end_signal: {session.get('project_end_signal')}",
                "",
            ]
        )
        events_by_turn: dict[Any, list[dict[str, Any]]] = {}
        for event in session.get("events", []):
            events_by_turn.setdefault(event.get("timestamp_index"), []).append(event)
        for message in session.get("messages", []):
            lines.append(f"{message.get('speaker')}：{message.get('content')}")
            for event in events_by_turn.get(message.get("turn"), []):
                lines.append(
                    f"【操作】{event.get('actor')} | {event.get('event_type')} | "
                    f"{event.get('status')} | {event.get('artifact_summary')}"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_project_conversation(project: dict[str, Any]) -> str:
    lines = [
        f"Project: {project.get('project_id')}",
        f"Scenario: {project.get('scenario', {}).get('title')}",
        f"Project anchor time: {format_timestamp(project.get('project_anchor_time'))}",
        f"Outcome: {project.get('project_outcome')}",
        "",
    ]
    for session in project.get("sessions", []):
        lines.extend(
            [
                f"===== Session {session.get('meeting_index')} =====",
                f"Date: {format_date(session.get('session_start_time'))}",
                f"Start: {format_timestamp(session.get('session_start_time'))}",
                "",
            ]
        )
        for message in session.get("messages", []):
            lines.append(
                f"[{format_timestamp(message.get('message_timestamp'))}] "
                f"{message.get('speaker')}: {message.get('content')}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_project_behavior(project: dict[str, Any]) -> str:
    lines = [f"Project: {project.get('project_id')}", ""]
    for session in project.get("sessions", []):
        in_session_events = session.get("events", [])
        for event in in_session_events:
            lines.append(format_behavior_event(event))
        for event in session.get("between_session_events_after", []):
            lines.append(format_behavior_event(event))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_behavior_event(event: dict[str, Any]) -> str:
    return f"[{format_timestamp(event.get('timestamp'))}] {event.get('actor')} | {event.get('artifact_summary')}"


def format_timestamp(raw_value: Any) -> str:
    if not raw_value:
        return "unknown"
    try:
        return datetime.fromisoformat(str(raw_value)).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(raw_value)


def format_date(raw_value: Any) -> str:
    if not raw_value:
        return "unknown"
    try:
        return datetime.fromisoformat(str(raw_value)).strftime("%Y-%m-%d")
    except ValueError:
        return str(raw_value)


def format_group_summary(record: dict[str, Any]) -> str:
    project = record["project"]
    sessions = project.get("sessions", [])
    return "\n".join(
        [
            f"# {record['group_id']}",
            "",
            f"- project_id: `{project.get('project_id')}`",
            f"- source_run_dir: `{record['source_run_dir']}`",
            f"- source_run_status: `{record['source_run_status']}`",
            f"- project_status: `{project.get('status')}`",
            f"- project_outcome: `{project.get('project_outcome')}`",
            f"- planned/generated sessions: `{project.get('planned_session_count')}` / `{project.get('generated_session_count')}`",
            f"- message_count: `{sum(session.get('message_count', 0) for session in sessions)}`",
            f"- event_count: `{len(project.get('events', []))}`",
            f"- interpretation: {classify_group_result(project)}",
            "",
            "## Sessions",
            "",
            *[
                f"- 第 {session.get('meeting_index')} 次：messages={session.get('message_count')}, "
                f"outcome={session.get('session_outcome')}, end_signal={session.get('project_end_signal')}, "
                f"silence_stop={session.get('silence_stop_used')}"
                for session in sessions
            ],
            "",
        ]
    )


def write_collection_files(
    collection_dir: Path,
    combined_dataset: dict[str, Any],
    overview: dict[str, Any],
) -> None:
    (collection_dir / "final_dataset_combined.json").write_text(
        json.dumps(combined_dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (collection_dir / "group_overview.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (collection_dir / "group_overview.md").write_text(
        format_overview_markdown(overview),
        encoding="utf-8",
    )
    (collection_dir / "conversation_timeline_combined.txt").write_text(
        "\n\n".join(
            format_project_conversation(project)
            for project in combined_dataset.get("projects", [])
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (collection_dir / "behavior_timeline_combined.txt").write_text(
        "\n\n".join(
            format_project_behavior(project)
            for project in combined_dataset.get("projects", [])
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (collection_dir / "persona_difference_report.md").write_text(
        format_difference_report(overview),
        encoding="utf-8",
    )
    (collection_dir / "README.md").write_text(
        format_collection_readme(overview),
        encoding="utf-8",
    )


def format_overview_markdown(overview: dict[str, Any]) -> str:
    lines = [
        "# Persona Composition Timeline Collection",
        "",
        "本汇总只用于检查不同 persona 分组生成的原始对话差异，不是学生表现评分。",
        "",
        f"- created_at: `{overview['created_at']}`",
        f"- generated groups: `{overview['generated_group_count']}` / `{overview['expected_group_count']}`",
        f"- partial groups: `{', '.join(overview['partial_groups']) or 'none'}`",
        f"- missing groups: `{', '.join(overview['missing_groups']) or 'none'}`",
        "",
        "## Group Index",
        "",
        "| group | status | sessions | outcome | interpretation | files |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in overview["groups"]:
        files = (
            f"[conversation]({item['review_files']['conversation']}) / "
            f"[behavior]({item['review_files']['behavior']}) / "
            f"[summary]({item['review_files']['summary']})"
        )
        lines.append(
            f"| {item['group_id']} | {item['project_status']} | "
            f"{item['generated_session_count']}/{item['planned_session_count']} | "
            f"{item['project_outcome']} | {item['profile_interpretation']} | {files} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def format_difference_report(overview: dict[str, Any]) -> str:
    groups = overview["groups"]
    positive = [
        item
        for item in groups
        if "positive" in item["group_id"]
        or item["group_id"] in {"composition_execution_heavy", "composition_maintenance_heavy"}
    ]
    mixed_dysfunction = [
        item
        for item in groups
        if any(
            token in item["group_id"]
            for token in ["free_rider", "dominator", "blocker", "lone_wolf"]
        )
    ]
    high_dysfunction = [
        item for item in groups if "high_dysfunction" in item["group_id"]
    ]

    lines = [
        "# Persona Difference Report",
        "",
        "本文件用于快速复查不同 persona 组合是否生成了差异化对话。它只描述生成现象，不做学生表现评分。",
        "",
        "## 总体结论",
        "",
        f"- 已生成分组：`{overview['generated_group_count']}` / `{overview['expected_group_count']}`。",
        f"- 缺失分组：`{', '.join(overview['missing_groups']) or 'none'}`。",
        f"- 未完整分组：`{', '.join(overview['partial_groups']) or 'none'}`。",
        f"- 正向/执行/维护型分组平均消息数：`{average_metric(positive, 'message_count')}`。",
        f"- 混合失调分组平均消息数：`{average_metric(mixed_dysfunction, 'message_count')}`。",
        f"- 高失调分组平均消息数：`{average_metric(high_dysfunction, 'message_count')}`。",
        "",
        "## 现象判断",
        "",
        "- 正向和执行型分组多数能持续推进到 `completed` 或 `forced_submission`，适合作为协作推进型样本。",
        "- 搭便车、支配者、阻碍者、独狼等混合失调分组虽然仍可能完成项目，但更容易出现临时僵持、强势分配、任务拖延或需要被迫提交。",
        "- 高失调分组应重点查看 `temporary_stalemate`、低事件数、成员发言失衡和是否出现放弃/互相推责语言。",
        "- 如果某个负面组结局仍然过于顺利，应保留该结果作为“失调但仍完成”的样本，同时可以后续单独提高冲突倾向重新生成对照样本。",
        "",
        "## 分组对比表",
        "",
        "| group | sessions | outcome | messages | events | session outcomes | interpretation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in groups:
        session_outcomes = "; ".join(
            f"{key}={value}" for key, value in item["session_outcomes"].items()
        )
        lines.append(
            f"| {item['group_id']} | {item['generated_session_count']}/{item['planned_session_count']} | "
            f"{item['project_outcome']} | {item['message_count']} | {item['event_count']} | "
            f"{session_outcomes} | {item['profile_interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## 人工复查建议",
            "",
            "- 先读 `conversation_timeline_combined.txt` 获取所有对话的连续视图。",
            "- 再进入 `groups/<group_id>/conversation_timeline.txt` 查看单个分组。",
            "- 优先复查 `composition_high_dysfunction`、`composition_blocker_conflict`、`composition_dominator_unbuffered` 是否体现负面角色差异。",
            "- 如果要做论文或面试材料，可以把正向组、混合失调组、高失调组分别作为三类代表案例。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def average_metric(groups: list[dict[str, Any]], metric_name: str) -> str:
    if not groups:
        return "n/a"
    values = [float(item.get(metric_name, 0) or 0) for item in groups]
    return f"{sum(values) / len(values):.1f}"


def format_collection_readme(overview: dict[str, Any]) -> str:
    lines = [
        "# Persona Composition Urgency Collection",
        "",
        "这是同一功能模块 `timeline_v2`、同一 API 配置、同一 `urgency_queue` 发言机制下，不同 persona 分组生成结果的统一汇总目录。",
        "",
        "## 入口文件",
        "",
        "- `group_overview.md`：总索引，说明每个分组的生成状态、结局和对应文件。",
        "- `persona_difference_report.md`：差异复查报告，用于判断不同 persona 组合是否产生了不同对话走向。",
        "- `conversation_timeline_combined.txt`：所有分组对话的合并直观转写。",
        "- `final_dataset_combined.json`：所有分组的结构化合并数据，可交给下游项目使用。",
        "- `groups/<group_id>/conversation_timeline.txt`：单个分组的直观对话。",
        "- `groups/<group_id>/summary.md`：单个分组的简要统计和解释。",
        "- `groups/<group_id>/project.json`：单个分组的完整结构化项目数据。",
        "- `runs/`：本 collection 内直接产生的原始运行目录。",
        "- `source_runs/`：从 collection 外部纳入汇总的历史运行核心文件备份。",
        "",
        "## 当前状态",
        "",
        f"- 已生成分组：`{overview['generated_group_count']}` / `{overview['expected_group_count']}`。",
        f"- 缺失分组：`{', '.join(overview['missing_groups']) or 'none'}`。",
        f"- 未完整分组：`{', '.join(overview['partial_groups']) or 'none'}`。",
        "",
        "## 推荐阅读顺序",
        "",
        "1. 先看 `group_overview.md` 确认每个分组的位置。",
        "2. 再看 `persona_difference_report.md` 判断整体差异。",
        "3. 最后按需进入 `groups/<group_id>/conversation_timeline.txt` 读原始对话。",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def copy_source_files(collection_dir: Path, run_dirs: list[Path]) -> None:
    source_root = collection_dir / "source_runs"
    source_root.mkdir(parents=True, exist_ok=True)
    core_names = [
        "final_dataset.json",
        "state.json",
        "conversation_timeline.txt",
        "behavior_timeline.txt",
        "behavior_events.jsonl",
        "quality_report.md",
        "quality_report.json",
        "metadata.json",
        "run.log",
    ]
    for run_dir in run_dirs:
        target = source_root / run_dir.name
        target.mkdir(parents=True, exist_ok=True)
        for name in core_names:
            source = run_dir / name
            if source.exists():
                shutil.copy2(source, target / name)


if __name__ == "__main__":
    raise SystemExit(main())
