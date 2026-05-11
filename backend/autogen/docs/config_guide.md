# 配置说明（Configuration Guide）

## 2026-05-08 Output Files

`timeline_v2` now writes three review-oriented files:

- `conversation_timeline.txt`
  Pure timestamped transcript.
- `behavior_timeline.txt`
  Human-readable behavior timeline.
- `behavior_events.jsonl`
  Structured event stream with one JSON object per event.

Useful structured fields now available in output JSON:

- `project_anchor_time`
- `session_start_time`
- `session_end_time`
- `message_timestamp`
- `event.timestamp`
- `event.source_basis`
- `event.visibility`

`event_refs` are still kept in structured JSON for programmatic linkage, but they are no longer rendered into the transcript file.

本文件说明当前项目中所有适合人工调整的配置文件。它的目标是让你知道“能改哪里、字段是什么意思、改错会导致什么问题、哪些内容不能公开”。

## 1. 配置维护原则

- 修改配置前，先确认你要改变的是角色行为、实验分组、模型访问，还是项目记录规则。
- 修改配置后，优先运行 `python run_experiments.py --dry-run` 检查结构是否能加载。
- 涉及真实 API key 的文件不要提交到公开仓库，也不要粘贴到公开文档。
- 改动配置后，如果字段含义或使用方式变化，应同步更新本文件。
- 如果配置变化会影响实验结论，应同步记录到 `docs/dev_journal.md` 或 `docs/decisions.md`。

## 2. `persona.json`

### 用途

`persona.json` 定义所有可用角色。每个角色会被转换成一个 AutoGen agent，用于参与群聊。

### 常见字段

- `role_id`
  角色唯一编号。实验分组会通过这个字段引用角色。

- `name`
  角色显示名称。它帮助后续阅读对话时识别人物。

- `category`
  角色类别，例如正向推进、正向维护、负面失调。

- `description`
  角色行为简介，方便人类理解。

- `system_message`
  给模型的系统提示词（system prompt），直接影响角色发言方式。

### 什么时候需要修改

- 需要新增或删除 persona。
- 需要调整某个角色的协作风格。
- 需要让角色更贴近教育场景中的学生表现。
- 需要降低过度极端或不自然的行为。

### 常见错误

- `role_id` 重复，会导致分组引用混乱。
- 修改 `role_id` 后没有同步修改 `configs/experiment_groups.json`。
- `system_message` 太短，角色行为不稳定。
- `system_message` 太强，角色可能反复重复同一种行为。

### 建议

如果只是微调角色行为，优先改 `system_message`，不要频繁改 `role_id`。`role_id` 更像数据库里的主键（primary key），一旦被其他配置引用，就应保持稳定。

## 3. `configs/experiment_groups.json`

### 用途

这个文件定义实验任务和对照组。它决定每次运行有哪些 group、每个 group 有哪些成员、重复几次、最多对话多少轮。

### 关键字段

- `default_task`
  默认任务描述。所有未单独设置任务的 group 会使用它。

- `output_prefix`
  输出目录前缀。用于生成 `outputs/<run_id>/`。

- `manager_system_message`
  群聊管理者的系统提示，影响 AutoGen manager 如何协调发言。

- `default_groupchat.max_round`
  默认最大对话轮数。用于避免对话无限运行。

- `default_groupchat.allow_repeat_speaker`
  是否允许同一个 agent 连续发言。当前建议保持 `false`，减少单一角色刷屏。

- `groups[].group_id`
  对照组唯一编号。

- `groups[].member_role_ids`
  当前组使用哪些 persona。这里的值必须能在 `persona.json` 中找到。

- `groups[].repeats`
  当前组重复生成几次。

### 什么时候需要修改

- 想增加新的对照组。
- 想改变每组人数，例如从 4 人改为 5 人。
- 想改变任务场景。
- 想缩短或延长对话。
- 想增加重复次数来扩大数据量。

### 常见错误

- `member_role_ids` 引用了不存在的 `role_id`。
- `max_round` 设置过大，导致输出成本增加且后期对话漂移。
- `repeats` 设置过大，导致一次运行时间过长。
- 多个 group 的 `group_id` 重复，导致后续分析混乱。

### 建议

调试阶段建议：

```json
"max_round": 8,
"repeats": 1
```

正式生成阶段可以逐步增加轮数和重复次数，但每次改动后先跑一个小 group 验证质量。

## 4. `configs/scenarios_timeline.json`

### 用途

这个文件只给 `timeline_v2` 使用。它定义教育场景任务模板，而不是把任务全文直接写死在实验组里。

### 关键字段

- `scenario_id`
  场景唯一编号，供 `experiment_groups_timeline.json` 引用。

- `title`
  项目标题。

- `task_type`
  任务类型，例如 `course_project`、`lab_project`、`teaching_design`。

- `course_context`
  所属课程或教学场景。

- `deliverable_type`
  最终交付物类型。

- `deadline_span`
  时间跨度描述。

- `difficulty`
  任务难度。

- `artifact_types`
  该场景常见产物类型。

- `project_brief`
  项目简介。

- `initial_context`
  给连续会议开局用的初始背景。

- `common_operations`
  当前场景中常见的学生操作，例如查资料、搭框架、运行实验、编辑 PPT。

- `conflict_points`
  当前场景中容易自然出现的分歧来源。

- `natural_endings`
  当前场景中合理的自然结束方式，例如阶段性暂停、僵持散会、被迫提交。

### 什么时候需要修改

- 新增新的教育任务场景
- 调整当前场景的交付物或项目背景
- 想比较不同课程项目的对话风格

### 常见错误

- `scenario_id` 重复
- 删除了某个 `scenario_id`，但 `experiment_groups_timeline.json` 还在引用
- `project_brief` 太空，导致 session 开场不稳定

## 5. `configs/experiment_groups_timeline.json`

### 用途

这个文件只给 `timeline_v2` 使用。它定义项目级时间线实验组，包括场景引用、连续会议数和团队动态参数。

### 关键字段

- `schema_version`
  当前应为 `project_timeline_v2`。

- `dataset_name`
  数据集名称。

- `output_prefix`
  timeline 运行的输出目录前缀。

- `manager_system_message`
  流程协调者提示词。

- `default_groupchat.max_round`
  每个 session 的最大轮数。

- `groups[].group_id`
  组 ID。

- `groups[].scenario_id`
  引用 `scenarios_timeline.json` 中的某个场景。

- `groups[].member_role_ids`
  该组成员 persona。

- `groups[].session_count_range`
  同一项目会生成多少次会议。

- `groups[].offtopic_tendency`
  跑题程度，当前支持 `low` / `medium` / `high`。

- `groups[].attendance_variability`
  出勤波动程度，影响 `passive`、`late`、`async_followup`、`absent` 的分配概率。

- `groups[].deadline_pressure_curve`
  截止压力曲线。

### `generation_settings`

`generation_settings` 是 `timeline_v2` 的生成策略配置，用来减少硬编码。

常见字段：

- `min_effective_messages`
  每个 session 期望的最低有效消息数。过低容易讨论太浅，过高会增加成本。

- `min_participating_speakers`
  每个 session 期望的最低参与成员数。

- `repair_max_rounds`
  当讨论太短或参与不足时，最多追加几轮 repair prompt。

- `enable_closer`
  是否允许 closer 补一条自然收尾消息。

- `enable_event_controller`
  预留开关。当前默认关闭，本轮仍以关键词事件抽取为主。

- `enable_quality_diagnostics`
  是否输出 `quality_report.md` 和 `quality_report.json`。

- `session_timeout_seconds`
  单次模型调用超时时间。

- `incremental_conversation_timeline`
  是否每完成一个 session 就追加写入 `conversation_timeline.txt`。

### 什么时候需要修改

- 想增加 timeline 实验组
- 想控制连续会议数量
- 想提高或降低生活化闲聊程度
- 想增加更不稳定或更稳定的成员出勤

### 调试建议

调试 `timeline_v2` 时，优先把：

```json
"session_count_range": [3, 3]
```

这样可以缩短一次真实运行时间，先看生成质量，再放开范围。

## 6. `configs/experiment_groups_persona_composition.json`

### 用途

这个文件专门用于 persona 组合实验。它不覆盖 `experiment_groups_timeline.json`，而是单独定义 12 组不同学生 persona 组合，用于生成不同类型的学生团队对话。

### 当前组合类型

- 正向均衡组
- 高功能正向 5 人组
- 创意与批判拉扯组
- 执行导向组
- 维护导向组
- 搭便车但有人管理组
- 搭便车且缺少管理组
- 支配者有缓冲组
- 支配者缺少缓冲组
- 阻碍者冲突组
- 独狼冲突组
- 高失调组

### 常用命令

只检查配置，不调用模型：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition.json --dry-run
```

估算运行规模：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition.json --estimate-cost
```

小批量真实生成：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition.json --only-groups composition_positive_balanced_4,composition_free_rider_managed,composition_high_dysfunction
```

完整生成：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition.json
```

### 当前规模

当前配置包含 12 个 group。每组 `repeats=1`，预计一次完整运行生成：

- 12 个 project
- 36-57 个 session

这不是费用估算，只是运行规模估算。真实成本取决于模型、消息长度和 AutoGen 的 speaker selection 调用次数。

## 7. `configs/oai_config_list.json`

### 用途

这个文件定义模型访问配置。当前推荐通过简易 API 使用 OpenAI 兼容接口（OpenAI-compatible API）。

`timeline_v2` 支持双模型配置：

- `dialogue`
  学生 agent 和 GroupChat manager 使用的主对话模型。

- `controller`
  session controller、closer 等内部控制调用使用的模型。

旧版 `legacy` 会读取 `dialogue` 作为自己的模型配置。

### 当前推荐模板

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

### 字段说明

- `dialogue[].model`
  主对话模型。当前建议先用 `gemini-2.5-flash`，用于学生团队自然对话生成。

- `controller[].model`
  内部控制模型。当前建议先用 `gpt-4.1-mini`，用于 JSON 分析、收束判断和简短收尾生成。

- `api_key`
  简易 API key。真实 key 不能公开。

- `base_url`
  简易 API 的 OpenAI 兼容接口地址，当前使用 `https://jeniya.cn/v1`。

### 什么时候需要修改

- 更换模型。
- 更换 API key。
- 从简易 API 切换到其他 OpenAI 兼容服务。
- 测试不同模型对对话质量的影响。

### 常见错误

- `api_key` 写错，通常会导致 401。
- 模型在当前 API 提供商上不可用，可能导致 404、403 或路由错误。
- `base_url` 漏掉 `/v1`，可能导致请求路径错误。
- 模型能力较弱，可能导致角色不稳定或无法按格式停止。

### 安全规则

不要在以下位置写入真实 key：

- `README.md`
- `docs/`
- `configs/oai_config_list.example.json`
- 任何准备公开分享的截图或日志

如果需要给 AI 排查配置问题，可以只提供错误信息和脱敏后的配置结构。

## 8. `configs/oai_config_list.example.json`

### 用途

示例配置文件。它应该只包含占位符，不包含真实密钥。

### 维护规则

- 当 `oai_config_list.json` 的字段结构变化时，同步更新 example。
- example 中的 `api_key` 必须使用占位符，例如 `YOUR_JENIYA_API_KEY`。
- example 应保留一个可理解的模型 ID，方便新用户照着改。

## 9. `requirements.txt`

### 用途

记录 Python 依赖。它决定项目在 `autogen_env` 环境中安装哪些包。

### 当前重点依赖

- `autogen-agentchat>=0.2,<0.3`
  固定 AutoGen 0.2 经典 API，避免安装到 0.7.x 后接口不兼容。

### 什么时候需要修改

- 新增功能需要新依赖。
- 现有依赖版本存在 bug。
- 需要提升兼容性或复现实验环境。

### 常见错误

- 使用过宽版本范围，导致未来安装到不兼容版本。
- 修改依赖后没有重新安装。
- 在错误的 conda 环境中安装依赖。

建议使用：

```powershell
conda activate autogen_env
pip install -r requirements.txt
```

## 10. `AGENTS.md`

### 用途

项目级 AI 工作规则。它不是运行配置，但会影响 AI 后续如何修改代码、如何更新文档、如何记录日志。

### 什么时候需要修改

- 项目记录规则变化。
- 希望 AI 每次代码修改后自动维护特定文档。
- 需要增加项目特定的命名规则或安全规则。

### 维护建议

`AGENTS.md` 应写规则，不应写过多项目历史。项目历史放在 `docs/dev_journal.md`，完整上下文放在 `docs/project_context.md`。

## 11. `docs/` 记录文件

这些文件不是程序运行必需配置，但属于项目长期维护配置的一部分。

维护边界：

- `README.md`
  对外入口和快速入门。

- `docs/project_context.md`
  全局上下文恢复文件。

- `docs/dev_journal.md`
  实时开发日志。

- `docs/project_status.md`
  当前状态快照。

- `docs/decisions.md`
  长期技术决策。

- `docs/learning_notes.md`
  技术学习记录。

- `docs/file_roles.md`
  文件职责和维护规则。

- `docs/case_study.md`
  面试、论文和阶段复盘素材。

具体分工见 `docs/file_roles.md`。

## 12. 运行入口文件

### `run_experiments.py`

旧版基线入口，运行单段群聊生成。

常用命令：

```powershell
python run_experiments.py --dry-run
python run_experiments.py --config-list-file configs/oai_config_list.json
```

### `run_timeline_experiments.py`

新版 timeline 入口，运行项目级连续会议生成。

常用命令：

```powershell
python run_timeline_experiments.py --dry-run
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --only-groups timeline_positive_4
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --smoke-test
python run_timeline_experiments.py --estimate-cost --smoke-test
```

`timeline_smoke_test` 默认不会混入全量运行，只有使用 `--smoke-test` 或 `--only-groups timeline_smoke_test` 时才会运行。

### 什么时候选哪个

- 只想验证旧版单段群聊：用 `run_experiments.py`
- 想生成当前主方向的项目时间线数据：用 `run_timeline_experiments.py`

### timeline_v2 结果怎么看

`run_timeline_experiments.py` 每次正式运行会生成 `outputs/persona_project_timeline_dataset_<timestamp>/`。

如果你只是想快速阅读“学生到底聊了什么、做了什么操作”，优先打开：

```text
conversation_timeline.txt
```

这个文件按项目和 session 顺序展示：

- `说话人：发言内容`
- `【操作】学生 | 操作类型 | 状态 | 操作摘要`

如果你要给下游程序使用完整结构化数据，再读取 `final_dataset.json`、`projects.jsonl` 或 `state.json`。

如果你要排查生成质量，优先打开：

```text
quality_report.md
```

这个文件会提示参与度是否失衡、事件是否过少、是否出现伪多人发言、终局判断是否可能矛盾。

## 13. `scripts/` 记录命令

这些脚本用于让记录流程更固定。

### `scripts/log_dev_event.py`

用于追加实时开发事件。

示例：

```powershell
python scripts/log_dev_event.py --project-root . --event-type code_change --title "更新配置说明" --goal "让配置文件可维护" --what-happened "补充各配置文件字段说明"
```

### `scripts/backfill_project_history.py`

用于给已经开始的项目补录历史阶段。

示例：

```powershell
python scripts/backfill_project_history.py --project-root . --phase "项目初始化" --goal "补齐早期开发背景" --summary "从 persona.json 搭建 AutoGen 群聊生成器"
```

### `scripts/capture_run_context.py`

用于记录一次运行的命令、状态和上下文。

示例：

```powershell
python scripts/capture_run_context.py --project-root . --label dry_run --command "python run_experiments.py --dry-run" --status success
```

## 14. 配置修改后的检查清单

每次修改配置后建议检查：

- JSON 文件是否仍然合法。
- `role_id` 和 `member_role_ids` 是否能对应。
- `scenario_id` 是否能在 timeline 场景库中找到。
- `max_round` 和 `repeats` 是否符合当前成本预期。
- `session_count_range` 是否过大，导致 timeline 运行时间失控。
- 简易 API 模型是否已做最小化测试。
- 是否误写入真实 API key。
- 是否需要更新 `README.md`、`config_guide.md` 或 `project_status.md`。
- 是否需要把重要技术选择记录到 `decisions.md`。

## 15. `timeline_v2` 自发发言配置

`timeline_v2` 支持两类说话人选择方式：

- `auto`：AutoGen 默认方式，会额外调用模型判断下一位 speaker，质量较稳但运行较慢。
- `urgency_queue`：本项目新增的本地自发发言策略，通过 `urgency_score` 判断谁更想说话，不额外调用模型选人。

推荐用于 persona 组合实验的配置文件：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition_urgency.json --dry-run
```

小规模真实验证命令：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition_urgency.json --only-groups composition_positive_balanced_4,composition_free_rider_managed,composition_high_dysfunction
```

可调参数写在 `turn_taking` 中：

```json
{
  "speaker_selection_method": "urgency_queue",
  "turn_taking": {
    "interrupt_threshold": 0.78,
    "silence_threshold": 0.34,
    "underparticipation_boost": 0.18,
    "direct_mention_boost": 0.55,
    "last_speaker_penalty": 0.35,
    "max_consecutive_turns": 1,
    "min_turns_before_silence": 7
  }
}
```

字段含义：

- `interrupt_threshold`：高于该分数时，系统会把该 turn 标记为抢话/插话式发言。
- `silence_threshold`：对话已有足够轮数后，如果最高紧迫度低于该值，可以自然停止。
- `underparticipation_boost`：长期未发言成员的补偿权重。
- `direct_mention_boost`：被点名成员的发言权重。
- `last_speaker_penalty`：刚发过言的成员会被扣分，避免单人连续主导。
- `max_consecutive_turns`：允许同一成员连续发言的最大次数。
- `min_turns_before_silence`：至少生成多少轮后才允许低紧迫度自然停止。

输出检查：

- `final_dataset.json` 的 session 中会出现 `speaker_selection_policy`、`interruption_like_turns`、`silence_stop_used`、`speaker_selection_trace`。
- `quality_report.md` 会显示每个 session 使用的 speaker policy、插话 turn 和自然停止情况。
## 16. persona 组合结果统一汇总 collection

当同一功能模块、同一 API 模型配置下运行多个 persona 分组时，建议把所有批次结果统一汇总到一个 collection 目录，避免多个 timestamp 输出目录难以对照。

本轮 urgency persona composition 实验的统一目录是：

```text
outputs/persona_composition_urgency_collection_20260507/
```

新增汇总命令：

```powershell
python scripts/collect_timeline_results.py --collection-dir outputs/persona_composition_urgency_collection_20260507 --scan-collection-runs --copy-source-files
```

如果还需要纳入 collection 外部的历史运行目录，可以重复传入 `--run-dir`：

```powershell
python scripts/collect_timeline_results.py --collection-dir outputs/persona_composition_urgency_collection_20260507 --scan-collection-runs --run-dir outputs/persona_composition_urgency_timeline_dataset_20260506_234830 --copy-source-files
```

汇总后重点查看：

- `README.md`：collection 文件说明和推荐阅读顺序。
- `group_overview.md/json`：分组索引，记录每组对应的 source run、session 数、结局和结果文件。
- `persona_difference_report.md`：不同 persona 组合差异的复查报告。
- `final_dataset_combined.json`：所有分组的结构化合并结果。
- `conversation_timeline_combined.txt`：所有分组的合并直观转写。
- `groups/<group_id>/`：单个分组的独立结果目录。
