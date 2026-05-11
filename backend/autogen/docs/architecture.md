# 技术架构说明（Architecture）

## 2026-05-08 Output Layer Split

`timeline_v2` now has two human-readable output layers:

1. `conversation_timeline.txt`
   - Pure transcript only
   - Session header + simulated time + speaker + utterance
   - No embedded behavior markers

2. `behavior_timeline.txt` / `behavior_events.jsonl`
   - Separate behavior stream
   - Carries `timestamp`, `source_basis`, and `visibility`
   - Includes both explicit in-dialogue events and constrained between-session follow-up events

The machine-readable interface is still the project JSON itself. The split only changes the human review surface, not the generator/evaluator boundary.

本文件只记录项目技术结构、模块职责和运行链路。项目背景看 `project_context.md`，当前状态看 `project_status.md`，时间线变化看 `dev_journal.md`。

## 1. 架构目标

当前架构目标不是做学生评估系统，而是把“教育场景学生团队对话生成”拆成稳定、可扩展、可对照的两条工程线：

- 一条保留原始基线
- 一条持续迭代自然性和时间线能力

核心设计原则：

- `configuration-driven`
  角色、分组、场景、会话数和运行参数尽量通过 JSON 配置

- `dual-track`
  保留 `legacy` 基线，同时让 `timeline_v2` 独立演进

- `incremental persistence`
  运行过程中持续写出状态和 checkpoint

- `natural-but-bounded`
  对话尽量自然，但必须有控制层避免无限空转

- `project-level output`
  新版输出不只是一段对话，而是一个项目时间线

- `diagnostics-not-labels`
  质量诊断只用于排查生成问题，不作为学生表现评估标签

## 2. 总体结构

```text
persona.json
      │
      ├──────────────► legacy configs ───────────────► run_experiments.py
      │                                                 │
      │                                                 ▼
      │                                      src/persona_groupchat_dataset/
      │                                                 │
      │                                                 ▼
      │                                       single dialogue outputs
      │
      └──────────────► timeline configs ─────────────► run_timeline_experiments.py
                                                        │
                                                        ▼
                                      src/persona_project_timeline_dataset/
                                                        │
                                                        ▼
                                        project timeline + events outputs
```

## 3. legacy 运行线

### 入口

- `run_experiments.py`
- `src/persona_groupchat_dataset/cli.py`

### 输入

- `persona.json`
- `configs/experiment_groups.json`
- `configs/oai_config_list.json`

### 核心流程

1. 读取 persona 和 group 配置
2. 组装多个 `AssistantAgent`
3. 创建一个 `GroupChat`
4. 跑完一段群聊
5. 写出 `dialogues.jsonl`、`state.json`、`final_dataset.json`

### 特点

- 结构简单
- 是基线版本
- 一次只处理单段对话

## 4. timeline_v2 运行线

### 入口

- `run_timeline_experiments.py`
- `src/persona_project_timeline_dataset/cli.py`

### 输入

- `persona.json`
- `configs/scenarios_timeline.json`
- `configs/experiment_groups_timeline.json`
- `configs/oai_config_list.json`

### 核心对象

- `ScenarioDefinition`
  描述教育场景任务模板

- `GroupDefinition`
  描述组员、session 数范围、出勤波动、deadline 曲线等

- `project_state`
  当前项目状态，包括目标、结论、遗留问题、分工、进度、截止压力、团队情绪

- `session_record`
  单次会议记录

### 一次项目实例的运行流程

1. 根据 group 选出一组 persona，生成固定成员名字
2. 根据 `session_count_range` 决定该项目要开多少次会
3. 初始化 `project_state`
4. 对每个 meeting：
   - 随机分配出勤状态
   - 计算截止压力
   - 生成当次 `session_prompt`
   - 启动 AutoGen `GroupChat`
   - 对过短或参与不足的讨论做 repair
   - 用 controller 分析本轮结果
   - 必要时由 closer 补一条自然收尾
   - 从消息中提取事件
   - 更新 `project_state`
   - 生成 artifact 汇总和质量诊断
5. 形成 `project_outcome`
6. 写出项目级结果

## 5. timeline_v2 内部模块职责

### `loader.py`

负责读取：

- persona
- scenario
- timeline experiment config

只做加载和校验，不负责模型调用。

### `models.py`

定义 persona、scenario、group、experiment 的数据结构，让 timeline 配置字段更清晰。

### `runner.py`

这是当前最核心的模块，负责：

- 构建成员 profile 和可读名字
- 分配出勤状态
- 生成 session prompt
- 启动群聊
- 执行讨论修补
- 执行 controller 分析
- 生成收尾消息
- 提取事件
- 更新项目状态
- 增量保存项目级结果
- 在 session 结束后写入项目快照
- 生成 artifact 汇总和质量诊断信息

### `cli.py`

负责 timeline 版本的命令行入口、dry-run、路径解析、日志初始化和 checkpoint 调度。

## 6. 自然收束架构

timeline_v2 不再把显式结束 token 暴露到最终文本，而是采用“内部控制 + 输出清洗”。

### 组成

- agent prompt
  允许在自然停点给出内部结束信号 `[[SESSION_END]]`

- GroupChat manager
  负责在会话中抑制明显空转

- repair prompt
  在对话过短或成员过少时补充引导

- controller
  对 session 做结构化分析，输出 `session_outcome`、`carryover_summary`、`state_after_session`

- closer
  当最后停得太硬时，补一条自然收尾消息

### 设计目的

- 不让最终对话里出现生硬控制 token
- 保持自然停点
- 避免 session 在无效空转中无限拉长

## 7. 事件层多模态模拟

当前多模态不是接真实视觉模型，而是做 `event layer simulation`。

### 事件触发方式

从学生消息中基于关键词抽取事件，例如：

- 查资料
- 上传文档
- 改大纲
- 改 PPT
- 跑实验
- 分享结果
- 老师反馈
- deadline 提醒

### 输出方式

- `events`
  项目级独立事件流

- `message.event_refs`
  对话内部对事件的引用

这种设计的价值是：即使当前没有真实文件内容，仍然可以模拟学生“做了什么”。

## 8. 输出结构

### legacy 输出

```text
outputs/persona_groupchat_dataset_<timestamp>/
```

关键文件：

- `dialogues.jsonl`
- `state.json`
- `metadata.json`
- `final_dataset.json`
- `run.log`

### timeline_v2 输出

```text
outputs/persona_project_timeline_dataset_<timestamp>/
```

关键文件：

- `projects.jsonl`
- `project_checkpoints.jsonl`
- `conversation_timeline.txt`
- `quality_report.md`
- `quality_report.json`
- `state.json`
- `metadata.json`
- `final_dataset.json`
- `run.log`

### timeline 项目级结构

一个项目至少包含：

- `project_id`
- `scenario`
- `team_members`
- `project_state_history`
- `events`
- `sessions`
- `project_outcome`

一个 session 至少包含：

- `session_id`
- `meeting_index`
- `participants_present`
- `carryover_summary`
- `messages`
- `session_outcome`
- `state_after_session`

### timeline 中断容错策略

- `project_checkpoints.jsonl`
  每完成一个 session 就写入当前 project 快照

- `state.json`
  保存当前 run 下所有已知 project 的最新状态，包括 `in_progress` 项目

- `projects.jsonl`
  只保留完整 project 的最终结果

- `conversation_timeline.txt`
  面向人工阅读的直观对话时间线。当前按 session 级增量写入，把对话转写成“说话人：发言内容”的形式，并在相关轮次插入 `【操作】` 行展示学生行为事件。

- `quality_report.md` / `quality_report.json`
  生成质量诊断报告，用于发现参与度失衡、伪多人发言、重复空转、事件过少和终局判断矛盾等生成问题。它们不是学生表现评估标签。

这样做的目的，是把“运行中快照”和“最终完整产物”分开，既能保留中途结果，也不会污染最终完整样本集合。

## 9. 文档与记录层

仓库同时有一层独立于运行逻辑的记录架构：

```text
AGENTS.md
docs/
project_recording_template/
scripts/
```

这层不直接生成对话，但承担：

- 研发上下文恢复
- 技术决策沉淀
- 开发时间线记录
- 配置说明与维护规范

## 10. 当前扩展点

当前最值得继续扩展的位置是 `src/persona_project_timeline_dataset/runner.py`，因为自然性、事件抽取、状态推进和收尾策略都集中在这里。

后续可扩展方向：

- 更强的事件抽取规则
- 更稳的 controller JSON 约束
- 断点续跑
- 数据质量筛查
- 更多教育场景模板
- 更完整的 artifact 生命周期模拟

## 11. 自发发言机制：`urgency_queue`

`timeline_v2` 新增一条可选的发言调度路径：

```text
AutoGen GroupChat
  speaker_selection_method="urgency_queue"
        ↓
src/persona_project_timeline_dataset/turn_taking.py
        ↓
本地 urgency_score 选择下一位学生
```

这个模块的作用是替换 AutoGen 默认 `auto` 选人，避免每轮额外调用 LLM 判断下一个 speaker。它不是新的 agent，也不是学生表现评估器，只是一个本地 turn-taking policy。

`urgency_score` 主要参考：

- persona 角色倾向
- 当前成员出勤状态
- 是否被直接点名
- 是否长期未发言
- 上一轮是否出现冲突、问题、分工、deadline 等信号
- 当前项目 deadline 压力
- 是否需要阻止同一成员连续占据发言权

该机制可以模拟：

- 主动插话
- 抢话式反驳
- 被点名后回应
- 潜水成员少量短回应
- 低紧迫度时自然沉默收束

当前文本 GroupChat 仍是 turn-based，因此“抢话”不是语音层面的真实重叠，而是通过高 urgency 成员紧接上一条消息发出短 turn 来模拟。
