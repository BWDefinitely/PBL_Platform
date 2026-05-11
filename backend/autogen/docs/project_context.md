# 项目完整上下文（Project Context）

## 2026-05-08 | timeline_v2 output contract update

The current `timeline_v2` output contract is now:

- Human-readable transcript and behavior logs are split.
- `conversation_timeline.txt` is a pure timestamped transcript and no longer embeds behavior labels.
- `behavior_timeline.txt` and `behavior_events.jsonl` hold the behavior layer separately.
- Structured JSON remains the program interface and continues to expose project/session/message/event records.

This keeps the generator in `autogen` focused on dialogue-generation outputs while making the human review layer closer to real meeting transcripts plus an independent activity log.

这个文件用于在上下文不足时快速恢复整个项目的真实状态。`README.md` 负责对外入口，本文件负责给 AI 和开发者提供完整背景、架构边界、当前能力和未完成点。

## 1. 项目定位

当前仓库只负责一件事：

`在教育场景下，用多智能体接入 LLM，模拟学生团队围绕同一任务的自然对话，并输出可供下游评估项目使用的原始数据。`

边界需要明确：

- 本项目负责 `对话生成（dialogue generation）`
- 不负责 `学生表现评估（student-performance assessment）`
- 不负责 `对话质量打分或标签体系`
- 允许少量内部控制代理，但它们只服务于“让生成更自然、更稳定”

主项目是教育领域学生表现评估。由于缺少现成数据集，这个仓库先承担“数据生成前置工程”的角色，后续生成结果会被另一个项目拿去做评估研究。

## 2. 当前双轨结构

为了保留旧版本做对比，当前仓库已经拆成两条运行线：

- `legacy`
  原始单段群聊生成器。它的作用是提供一个稳定基线，方便回看最初的实现和结果格式。

- `timeline_v2`
  新研发的“自然学生团队对话生成器”。它面向当前主目标，支持项目级时间线、多次连续会议、自然收束和事件流模拟。

这两条线并存的原因：

- 避免在升级过程中破坏原始可运行版本
- 方便比较旧版单轮群聊和新版连续项目对话的差异
- 后续如果 timeline 版本出现问题，还能回退到 legacy 做定位

## 3. 当前项目目标

### 当前直接目标

- 从 `persona.json` 动态读取协作人格
- 用 AutoGen 0.2 `GroupChat` 构建多智能体学生讨论
- 按配置组出 4-5 人小组
- 在教育场景下生成更自然的学生团队对话
- 让同一任务可以跨多次会议连续推进
- 输出对话、项目状态演化和文本化操作事件
- 保持输出在中断情况下也尽量可恢复

### 当前不做的事情

- 不做学生表现评分
- 不做下游评估标签设计
- 不做真实图像/文件理解型多模态
- 不做复杂外部数据库或 Notion 集成

### 中长期目标

- 形成更真实的教育场景多智能体原始数据集
- 为后续评估项目提供连续时间线型输入数据
- 逐步沉淀出一套可复用的教育协作模拟框架

## 4. 当前技术选型

- `Python`
  项目主语言。

- `AutoGen 0.2`
  使用经典 `GroupChat` API，依赖固定为 `autogen-agentchat>=0.2,<0.3`。

- `OpenRouter`
  作为 OpenAI-compatible 接口。当前验证可用模型是 `qwen/qwen-2.5-7b-instruct`。

- `JSON 配置`
  用于存储 persona、实验组、timeline 场景和模型配置。

- `Markdown 文档体系`
  用于维护项目背景、开发日志、当前状态、决策和配置说明。

## 5. 当前目录结构

```text
autogen/
├─ AGENTS.md
├─ configs/
│  ├─ experiment_groups.json
│  ├─ experiment_groups_timeline.json
│  ├─ oai_config_list.example.json
│  ├─ oai_config_list.json
│  └─ scenarios_timeline.json
├─ docs/
├─ outputs/
├─ persona.json
├─ project_recording_template/
├─ requirements.txt
├─ run_experiments.py
├─ run_timeline_experiments.py
├─ scripts/
└─ src/
   ├─ persona_groupchat_dataset/
   └─ persona_project_timeline_dataset/
```

## 6. 两条运行线分别做什么

### `legacy` 运行线

入口：

- `run_experiments.py`
- `src/persona_groupchat_dataset/`

特点：

- 一次只生成一段群聊
- 使用 `configs/experiment_groups.json`
- 输出 `dialogues.jsonl`
- 仍保留显式结束标记逻辑

适用场景：

- 回看早期实现
- 验证基础 persona 组合是否正常
- 和 timeline_v2 做结果对比

### `timeline_v2` 运行线

入口：

- `run_timeline_experiments.py`
- `src/persona_project_timeline_dataset/`

特点：

- 一个 `project_id` 对应同一任务的完整时间线
- 一个项目包含多次 `session`
- 每次会议承接上一轮项目状态摘要
- 使用内部 controller/closer 做自然收束
- 生成文本化多模态事件流
- 输出 `projects.jsonl`
- 输出 `project_checkpoints.jsonl`

适用场景：

- 当前主研发方向
- 教育场景学生团队协作模拟
- 为下游评估项目提供原始数据

## 7. timeline_v2 当前已经实现的核心能力

### 7.1 项目级时间线

- 引入 `project instance` 概念
- 同一项目可生成 3-8 次连续会议
- 每次会议输入包含项目状态、最近事件、出勤情况和截止压力

### 7.2 自然收束

- 内部使用隐藏结束信号 `[[SESSION_END]]`
- 最终保存文本中会去掉内部结束标记
- controller 根据对话内容判断 `session_outcome`
- closer 在必要时补一条自然收尾消息

当前支持的会话结果：

- `progress_made_and_pause`
- `temporary_stalemate`
- `conflict_breakup`
- `task_completed_for_now`

### 7.3 团队动态

- 核心成员固定
- 支持 `active`、`passive`、`late`、`async_followup`、`absent`
- 每次会议成员出勤状态可波动

### 7.4 事件级多模态模拟

当前不做真实多模态推理，只做文本化事件模拟。

已实现首批事件类型：

- `search_material`
- `upload_document`
- `edit_outline`
- `edit_slides`
- `run_experiment`
- `share_result`
- `teacher_feedback`
- `deadline_reminder`

输出中同时保留：

- 独立 `events` 列表
- 消息上的 `event_refs`

### 7.5 输出与中断容错

- 每完成一个项目就追加到 `projects.jsonl`
- 每完成一个 session 就追加到 `project_checkpoints.jsonl`
- 运行期间持续更新 `state.json`
- 运行完成后汇总到 `final_dataset.json`
- 已支持在项目中途被打断时保留已完成 session 的部分结果

## 8. 当前验证状态

截至 `2026-05-06`，已完成：

- `legacy` dry-run 验证
- `timeline_v2` dry-run 验证
- `timeline_v2` 至少一组真实运行验证
- 发现并修复 `TaskHost` 污染保存消息的问题
- 发现并修复 AutoGen cache 在 timeline controller 调用中的兼容问题
- 增加讨论修补（repair loop），缓解单人独白式 session

当前仍在观察的问题：

- 某些 session 仍可能由少数成员主导
- 某些回复会出现一条消息里模拟多个人说话的伪对话格式
- 某些项目状态推进仍偏保守，容易停在 `early_progress`
- 事件抽取目前还是启发式，覆盖率有限
- timeline_v2 的运行成本和耗时高于 legacy

## 9. 当前未完成能力

- 没有真实多模态文件内容生成
- 没有系统化的对话质量评估
- 没有基于输出的自动摘要报告
- 没有真正的断点续跑，只是中断保留
- 没有将运行记录自动同步成结构化实验报告

## 10. 主要风险

- OpenRouter 模型路由会影响实际生成效果
- AutoGen 0.2 的 `GroupChat` 可控性有限
- 自然对话和可控终止之间存在张力
- timeline_v2 更依赖 prompt 和后处理，调参成本更高
- 文档如果不同步，会直接影响后续 AI 读取上下文的准确性

## 11. 给后续 AI 的工作提示

如果需要快速恢复上下文，建议按这个顺序读：

1. `README.md`
2. `docs/project_context.md`
3. `docs/project_status.md`
4. `docs/dev_journal.md`
5. `docs/architecture.md`
6. `docs/config_guide.md`
7. `docs/decisions.md`

继续开发前应先确认：

- 这次改动影响的是 `legacy` 还是 `timeline_v2`
- 是否需要同时维护两条运行线
- 是否改了配置文件，需要更新 `config_guide.md`
- 是否改了结构或边界，需要更新 `project_context.md` / `architecture.md`
- 是否改了当前阶段状态，需要更新 `project_status.md`
- 是否改了关键实现，需要更新 `dev_journal.md`
