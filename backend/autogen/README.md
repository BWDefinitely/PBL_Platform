# Persona 群聊数据生成器（Persona GroupChat Dataset Generator）

## 2026-05-08 Output Update

`timeline_v2` now separates the human-readable output layer into:

- `conversation_timeline.txt`: timestamped pure dialogue transcript only
- `behavior_timeline.txt`: human-readable behavior event timeline
- `behavior_events.jsonl`: structured behavior event stream for downstream parsing

The structured JSON interface is still preserved in `final_dataset.json` and `projects.jsonl`.

New timeline fields:

- project-level: `project_anchor_time`
- session-level: `session_start_time`, `session_end_time`
- message-level: `message_timestamp`
- event-level: `timestamp`, `source_basis`, `visibility`

Behavior labels are no longer mixed into the transcript file.

## 这个项目是什么

本项目使用 `AutoGen 0.2` 和 OpenAI-compatible 模型接口，基于 `persona.json` 中定义的多种协作人格，自动生成多智能体群聊对话数据。

当前分支的直接目标是生成可控的模拟对话数据。长期目标是为“基于 LLM multi-agent 框架的学生表现评估”提供数据来源和工程基础。

当前仓库已同时保留两条运行线：

- `legacy` 版本：原始单段群聊生成器，方便和旧结果对比
- `timeline_v2` 版本：新研发的“自然学生团队对话生成器”，支持连续会议、项目状态承接和事件流模拟

## 这个项目能做什么

- 从 `persona.json` 读取不同协作角色
- 按 `configs/experiment_groups.json` 动态组成 4-5 人对照组
- 使用 AutoGen `GroupChat` 运行多智能体群聊
- 将对话结果增量保存到 `outputs/<run_id>/`
- 记录运行日志、元数据、最终数据集和中间状态
- 生成同一任务下的连续多次会议时间线
- 模拟学生缺席、潜水、迟到和会后补一句等参与波动
- 从自然对话中抽取文本化操作事件，例如查资料、上传文档、编辑提纲、改 PPT
- 输出生成质量诊断报告，用于排查参与度、事件覆盖、伪多人发言和终局判断问题
- 支持 `timeline_v2` 的 smoke test 和运行规模估算
- 提供一套可迁移到其他项目的项目记录体系

## 快速运行

安装依赖：

```powershell
conda activate autogen_env
pip install -r requirements.txt
```

先做配置校验，不调用模型：

```powershell
python run_experiments.py --dry-run
```

正式运行：

```powershell
python run_experiments.py --config-list-file configs/oai_config_list.json
```

运行新版本时间线生成器：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json
```

快速跑一个短程 smoke test：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --smoke-test
```

估算一次 timeline 运行规模，不调用模型：

```powershell
python run_timeline_experiments.py --estimate-cost --smoke-test
```

只运行指定分组：

```powershell
python run_experiments.py --config-list-file configs/oai_config_list.json --only-groups positive_control_4
```

只运行时间线版本中的一个实验组：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --only-groups timeline_positive_4
```

## 主要目录和文件

```text
autogen/
├─ AGENTS.md
├─ configs/
├─ docs/
├─ outputs/
├─ persona.json
├─ project_recording_template/
├─ requirements.txt
├─ run_experiments.py
├─ scripts/
└─ src/
```

## 文件功能概览

- `README.md`
  项目入口说明，面向第一次接触项目的人。

- `persona.json`
  定义所有可用的 persona 角色。

- `configs/experiment_groups.json`
  `legacy` 版本的实验配置。

- `configs/experiment_groups_timeline.json`
  `timeline_v2` 版本的实验配置，定义连续会议数量、出勤波动和场景引用。

- `configs/scenarios_timeline.json`
  `timeline_v2` 版本的教育场景库。

- `configs/oai_config_list.json`
  定义模型访问配置。`timeline_v2` 支持主对话模型和控制器模型分开配置。

- `run_experiments.py`
  `legacy` 版本主入口，用于启动单段群聊生成。

- `run_timeline_experiments.py`
  `timeline_v2` 版本主入口，用于启动项目级时间线生成。

- `src/persona_groupchat_dataset/`
  原始单段群聊版本代码。

- `src/persona_project_timeline_dataset/`
  新版时间线生成器代码，包括项目状态承接、连续 session 和事件流输出。

- `outputs/<run_id>/`
  每次运行自动生成的结果目录，包括 `run.log`、`metadata.json`、`state.json`、`dialogues.jsonl`、`projects.jsonl`、`conversation_timeline.txt` 和 `final_dataset.json`。

- `docs/`
  项目记录、架构、状态、开发日志、技术学习和配置说明。

- `AGENTS.md`
  项目级 AI 工作规则，约束后续开发和记录方式。

更完整的文件职责见 [docs/file_roles.md](docs/file_roles.md)。

## 项目文档入口

- [docs/project_context.md](docs/project_context.md)
  项目完整上下文。AI 或人类在上下文不足时应优先阅读。

- [docs/architecture.md](docs/architecture.md)
  技术架构说明。记录模块职责、数据流、运行链路和扩展点。

- [docs/project_status.md](docs/project_status.md)
  当前状态快照，适合隔几天后快速恢复开发状态。

- [docs/dev_journal.md](docs/dev_journal.md)
  从项目开始到现在的开发时间线、问题、根因、修复和验证。

- [docs/decisions.md](docs/decisions.md)
  长期有效的关键技术决策索引。

- [docs/learning_notes.md](docs/learning_notes.md)
  面向新手的技术知识、原理和方案比较记录。

- [docs/config_guide.md](docs/config_guide.md)
  所有可人工配置文件的使用说明。

- [docs/case_study.md](docs/case_study.md)
  面向面试、论文和阶段复盘的案例素材。

- [docs/file_roles.md](docs/file_roles.md)
  所有骨架文件的作用和维护规则。

## 模型配置示例

`configs/oai_config_list.json` 示例：

```json
{
  "dialogue": [
    {
      "model": "gemini-2.5-flash",
      "api_key": "YOUR_JENIYA_API_KEY",
      "base_url": "https://jeniya.cn/v1"
    }
  ],
  "controller": [
    {
      "model": "gpt-4.1-mini",
      "api_key": "YOUR_JENIYA_API_KEY",
      "base_url": "https://jeniya.cn/v1"
    }
  ]
}
```

不要把真实 API key 写进公开文档。

## 输出文件说明

每次正式运行会创建类似下面的目录：

```text
outputs/persona_groupchat_dataset_20260427_182123/
```

主要文件：

- `run.log`
  运行日志。

- `metadata.json`
  本次运行的模型、配置、输出路径等元数据。

- `state.json`
  增量保存的当前状态。

- `dialogues.jsonl`
  `legacy` 版本每完成一段对话就追加一条，防止中断丢失结果。

- `projects.jsonl`
  `timeline_v2` 版本每完成一个项目实例就追加一条，包含多次会议、项目状态和事件流。

- `conversation_timeline.txt`
  `timeline_v2` 版本的直观对话转写文件。它按项目时间线整理每一次 session，只保留说话人、发言内容和学生行为操作，适合人工快速阅读生成结果。

- `quality_report.md`
  `timeline_v2` 版本的人工可读质量诊断报告，只用于生成调试，不是学生表现评估标签。

- `quality_report.json`
  `timeline_v2` 版本的结构化质量诊断结果，方便后续批量筛查生成质量。

- `final_dataset.json`
  本次运行结束后的最终数据集。

## 记录体系命令

追加一条开发日志：

```powershell
python scripts/log_dev_event.py --project-root . --event-type code_change --title "标题" --goal "目标" --what-happened "发生了什么"
```

补录历史阶段：

```powershell
python scripts/backfill_project_history.py --project-root . --phase "阶段名称" --goal "阶段目标" --summary "阶段总结"
```

采集运行上下文：

```powershell
python scripts/capture_run_context.py --project-root . --label baseline --command "python run_experiments.py --dry-run" --status success
```
