# 开发日志（Development Journal）

## 2026-05-08 | Document validation terminology for later learning

### Goal

Explain the validation terms used during the recent timeline work and record them in project documentation for later study.

### Problem

Terms such as `static check`, `function-level spot check`, `dry-run`, and `smoke test` were used during implementation and validation, but they were not yet explained in the repo's learning-oriented docs.

### Root Cause

The project had already accumulated engineering shorthand during code and experiment discussions, while `docs/learning_notes.md` had not yet been expanded into a validation vocabulary reference.

### Solution

- Added a new "Validation terminology used in this repo" section to `docs/learning_notes.md`.
- Defined `static check`, `function-level spot check`, `dry-run`, `compileall`, and `smoke test`.
- Mapped each term back to the recent `timeline_v2` behavior-layer task so the explanations stay concrete instead of abstract.

### Validation

- Reviewed the current `learning_notes.md` structure and inserted the new glossary-style section near the top for visibility.
- Confirmed the new notes use repo-specific examples such as `python -m compileall src` and `run_timeline_experiments.py --dry-run`.

### Impact

The repo now keeps a reusable explanation of common validation jargon, which should make later discussions easier to follow and reduce ambiguity when describing verification work.

### Next

Continue adding short glossary-style notes when repeated engineering terms start appearing in project discussions or docs.

## 2026-05-08 | Split timeline_v2 transcript and behavior outputs

### Goal

Change `timeline_v2` so the human-readable output becomes a timestamped pure transcript plus an independent behavior event stream, while preserving structured JSON for programmatic use.

### Problem

The previous `conversation_timeline.txt` mixed dialogue lines with behavior annotations such as operation/event markers. That made the output convenient for debugging, but it no longer resembled a natural meeting transcript. It also lacked explicit message-level timestamps and did not record behavior provenance such as `source_basis` or `visibility`.

### Root Cause

The old output layer treated the transcript as both a human-reading artifact and an event-debug artifact at the same time. As a result, behavior extraction details leaked directly into the transcript surface.

### Solution

- Added simulated project/session/message timestamps with:
  - `project_anchor_time`
  - `session_start_time`
  - `session_end_time`
  - `message_timestamp`
- Kept `conversation_timeline.txt`, but converted it into a pure timestamped transcript.
- Added `behavior_timeline.txt` as a separate human-readable behavior log.
- Added `behavior_events.jsonl` as a structured event stream.
- Extended event records with `timestamp`, `source_basis`, and `visibility`.
- Added constrained between-session follow-up event synthesis so the behavior stream can reflect realistic project work between meetings without inventing ungrounded major milestones.
- Updated `collect_timeline_results.py` so collection outputs also preserve the transcript/behavior split.

### Validation

- `E:\\CondaConfig\\envs\\autogen_env\\python.exe -m compileall src/persona_project_timeline_dataset scripts/collect_timeline_results.py`
- `E:\\CondaConfig\\envs\\autogen_env\\python.exe run_timeline_experiments.py --dry-run`
- Lightweight Python formatting checks for both runner and collection script output functions

### Impact

The primary human review surface is now closer to a meeting transcript plus a separate activity log. Structured JSON remains intact for downstream consumers.

### Next

Run a small real `timeline_v2` generation and manually inspect whether:

- transcript timestamps are monotonic and natural
- transcript file contains no behavior labels
- behavior events look grounded and not over-inferred

这个文件记录项目从开始到现在的时间线。它强调“当时发生了什么、为什么这样改、怎么验证”。当前状态快照请看 `project_status.md`，长期设计决策索引请看 `decisions.md`。

## 2026-04-27 | 项目初始化：从 persona.json 到可运行骨架

### 当时目标

将只有 `persona.json` 的目录改造成一个可运行的 AutoGen 多智能体对话生成项目。

### 当时进展

- 新建 Python 项目结构
- 增加 `run_experiments.py` 入口
- 增加 `src/persona_groupchat_dataset/` 包
- 增加配置目录 `configs/`
- 增加输出目录 `outputs/`

### 遇到的问题

初始目录只有角色配置，没有工程结构、运行入口、实验分组配置和输出逻辑。

### 根本原因

项目需求已经明确，但还没有把“读取 persona、创建 agent、运行群聊、保存结果”串成工程链路。

### 解决方案

实现以下模块：

- `loader.py` 读取 persona 和实验配置
- `models.py` 定义配置数据结构
- `runner.py` 执行群聊和保存结果
- `cli.py` 提供命令行入口

### 验证

运行 `python run_experiments.py --dry-run`，确认能正确加载 11 个 persona 和 5 个对照组。

### 影响

项目从单个配置文件变成了可运行的数据生成器。

## 2026-04-27 | AutoGen 版本问题：固定到 0.2

### 当时目标

使用 AutoGen 的 `GroupChat` 框架运行多角色群聊。

### 遇到的问题

最初安装 `autogen-agentchat~=0.2` 时，pip 实际装到了 0.7.x 版本。新版 API 和经典 `GroupChat` 不兼容。

### 排查过程

- 检查 `autogen_env` 中是否安装 AutoGen
- 发现环境最初没有 `autogen`
- 安装后发现版本为 0.7.x
- 对比需求后确认项目需要经典 `GroupChat`

### 根本原因

Python 版本约束 `~=0.2` 会放宽到 `<1.0`，因此可能安装到 0.7.x，而不是预期的 0.2.x。

### 解决方案

将依赖改为：

```text
autogen-agentchat>=0.2,<0.3
```

### 验证

确认环境中的 `autogen.__version__` 为 `0.2.40`，且存在 `GroupChat` 和 `AssistantAgent`。

### 影响

项目运行 API 和代码实现保持一致，避免后续因为版本漂移导致运行失败。

## 2026-04-27 | OpenRouter 接入与模型路由问题

### 当时目标

使用用户已有的 OpenRouter API 运行真实模型调用。

### 遇到的问题

使用 `openai/gpt-4o-mini` 时返回 403：

```text
The request is prohibited due to a violation of provider Terms Of Service.
```

### 排查过程

- 验证 OpenRouter key 是否有效
- 查询 credits 接口，确认 key 和余额正常
- 用同一个 key 做最小化 `hello` 请求
- 测试多个模型 ID

### 根本原因

问题不是项目代码，也不是 API key 无效，而是 OpenRouter 上 `openai/gpt-4o-mini` 当前路由对该请求不可用。

### 解决方案

将模型切换为已验证可用的：

```text
qwen/qwen-2.5-7b-instruct
```

### 验证

最小化请求成功返回，并且后续真实单组运行可以进入对话生成。

### 影响

项目可以使用 OpenRouter 正常生成数据，但未来更换模型时需要先做最小化测试。

## 2026-04-27 | 输出保存改进：从最终保存改为增量保存

### 当时目标

避免长时间对话生成过程中断后丢失已经生成的内容。

### 遇到的问题

原始逻辑是所有对话跑完后才写出最终 JSON。如果用户手动终止或系统异常退出，前面已经生成的对话不会保存。

### 根本原因

保存逻辑只在完整流程结束后触发，没有每段对话完成后的 checkpoint。

### 解决方案

每次运行创建独立目录：

```text
outputs/<run_id>/
```

并写出：

- `state.json`
- `dialogues.jsonl`
- `final_dataset.json`
- `metadata.json`
- `run.log`

### 验证

运行单个 group 后成功生成对应输出目录和文件。

### 影响

即使运行被中断，也能保留已经完成的对话。

## 2026-04-27 | 对话无法自然收束的问题

### 当时目标

让多智能体对话尽量自然结束，同时避免无限运行。

### 遇到的问题

对话后期容易重复、空转，无法稳定输出结束标记。

### 排查过程

- 观察生成结果
- 检查 `max_round` 行为
- 检查 termination token 判断逻辑

### 根本原因

多智能体对话本身不一定会主动总结；同时如果只靠 prompt 约束，模型未必稳定遵守。

### 解决方案

- 设置最大轮数 `max_round`
- 默认禁止连续重复发言 `allow_repeat_speaker=false`
- 增加结束标记 `[GROUP_COMPLETE]`
- 在输出中记录 `termination_reason`

### 验证

真实运行可以在最大轮数内停止，并写出 `termination_reason`。

### 遗留问题

目前仍可能出现 `stopped_without_token`，说明对话停止了，但没有自然总结。后续可增加总结代理或裁判代理。

## 2026-04-30 | 建立跨项目记录体系

### 当时目标

将项目记录从“当前项目临时记录”升级为“未来所有项目可复用的记录体系”。

### 当时进展

新增：

- `AGENTS.md`
- `docs/`
- `project_recording_template/`
- `scripts/init_project_recording.py`
- `scripts/log_dev_event.py`
- `scripts/backfill_project_history.py`
- `scripts/capture_run_context.py`

### 遇到的问题

原本只有运行日志，缺少项目背景、技术决策、开发日志、配置说明和学习记录。

### 根本原因

运行日志只记录机器事实，不能替代研发过程、设计决策和学习沉淀。

### 解决方案

建立文档分工：

- README 做项目入口
- `project_context.md` 做完整上下文
- `dev_journal.md` 做时间线
- `project_status.md` 做当前状态
- `decisions.md` 做关键决策索引
- `learning_notes.md` 做技术学习记录
- `config_guide.md` 做配置说明

### 验证

文件结构已生成，脚本已写入。后续需要继续进行脚本级验证。

### 影响

项目后续开发可以保持上下文连续，也能迁移到其他项目。

## 2026-05-06 | 文档体系重新梳理

### 当时目标

根据新的文档分工要求，重新整理 `docs/` 中的 Markdown 文件，避免内容重复和职责混乱。

### 问题

已有文档中：

- README 和项目背景信息边界不清
- 缺少专门给 AI 恢复上下文的完整项目说明
- `dev_journal` 时间线不够完整
- `learning_notes` 还没有充分承担技术学习记录职责
- 哪些文件由 AI 自动维护、哪些需要用户手动指令，还没有明确说明

### 解决方案

本次更新：

- 重写 README
- 新增 `docs/project_context.md`
- 重写 `dev_journal.md`
- 重写 `project_status.md`
- 重写 `learning_notes.md`
- 更新 `decisions.md`
- 更新 `file_roles.md`
- 新增并完善 `docs/architecture.md`
- 新增并完善 `docs/config_guide.md`
- 新增并完善 `docs/case_study.md`

### 验证

已检查 `docs/` 文件存在性，并确认 README、架构、配置说明、案例素材和文件职责索引之间的分工已经补齐。

### 下一步

后续每次代码修改、调试和关键讨论都应同步更新 `dev_journal.md`，阶段变化时更新 `project_status.md`。

## 2026-05-06 | 文档职责进一步细化

### 当时目标

把 `docs/` 的职责切分得更明确，避免 README、上下文、状态、日志、配置说明和案例素材互相重复。

### 问题

- `architecture.md` 内容过短，不能完整描述运行链路和模块分工。
- `config_guide.md` 对手动配置文件的说明不够细。
- `case_study.md` 还没有形成面试和论文可直接复用的表达框架。
- README 还缺少这些文档的入口索引。

### 解决方案

本次进一步更新：

- 重写 `docs/architecture.md`，补充运行链路、模块职责、输出流和扩展点。
- 重写 `docs/config_guide.md`，补充所有人工可配置文件的字段说明、常见错误和安全规则。
- 重写 `docs/case_study.md`，补充项目背景、工程亮点、技术挑战、面试表达和论文表达素材。
- 更新 `README.md`，把新文档纳入入口索引。
- 更新 `docs/file_roles.md`，明确哪些文件适合 AI 实时维护，哪些更适合用户主导。

### 验证

文档结构现已覆盖：

- 对外入口
- 完整上下文
- 技术架构
- 开发日志
- 当前状态
- 技术学习
- 配置说明
- 文件职责
- 案例沉淀

### 影响

后续新增项目时，可以直接沿用这套文档分工，不需要重新发明记录结构。

## 2026-05-06 | 明确文档维护模式与手动触发指令

### 当时目标

把各个 Markdown 文件到底是“AI 主动维护”还是“需要用户手动触发”说清楚，并给出可直接复用的指令模板。

### 问题

虽然此前已经写过文件职责分工，但“具体怎么维护、谁来维护、什么时候更新、用户该怎么下指令”还不够明确。

### 解决方案

重写 `docs/file_roles.md`，明确三类维护模式：

- AI 主动维护
- 用户手动触发，AI 整理
- 脚本辅助维护

并为 `README.md`、`project_context.md`、`architecture.md`、`dev_journal.md`、`project_status.md`、`decisions.md`、`learning_notes.md`、`config_guide.md`、`case_study.md`、`AGENTS.md` 分别补充：

- 记录内容
- 维护方式
- 触发时机
- 是否需要用户手动触发
- 可直接使用的指令模板

### 验证

`docs/file_roles.md` 已包含逐文件维护规则和常用指令模板，可直接作为后续项目记录的操作说明。

### 影响

后续你不需要再反复解释“这个文件该不该更新、怎么更新”，可以直接按模板下指令。

## 2026-05-06 | 新增 timeline_v2：从单段群聊升级到项目级连续会议

### 当时目标

把当前项目升级成更贴近教育场景的学生团队对话生成器，同时保留旧版本以方便对照。

### 为什么要改

旧版 `legacy` 只能生成单段群聊，存在三个明显限制：

- 对话上下文只在一次群聊里，无法表达长期项目推进
- 结束方式偏机械，容易靠 token 或最大轮数停下
- 无法表达学生在会后查资料、上传文档、改 PPT、跑实验等操作痕迹

### 解决方案

本轮没有直接推翻旧实现，而是采用双轨方案：

- 保留 `src/persona_groupchat_dataset/` 和 `run_experiments.py`
- 新增 `src/persona_project_timeline_dataset/` 和 `run_timeline_experiments.py`
- 新增 `configs/scenarios_timeline.json`
- 新增 `configs/experiment_groups_timeline.json`

timeline_v2 的新增能力包括：

- 一个 `project_id` 包含多次 `session`
- 每次 session 都承接上一轮项目状态
- 引入出勤波动，例如 `passive`、`late`、`async_followup`、`absent`
- 引入内部 controller/closer 进行自然收束
- 输出项目状态历史和事件流

### 验证

- `python run_experiments.py --dry-run` 通过
- `python run_timeline_experiments.py --dry-run` 通过

### 影响

仓库从单线数据生成器变成双轨结构：

- `legacy` 负责保留基线
- `timeline_v2` 负责当前主研发方向

## 2026-05-06 | timeline_v2 首轮真实运行后的问题暴露

### 当时目标

验证 timeline_v2 在真实模型调用下是否能产出自然学生对话。

### 首轮观察到的问题

- 某些 session 基本只有一名成员在说话
- 保存下来的消息里混入了 `TaskHost` 提示内容
- 事件抽取几乎只命中了 prompt 里的 `deadline` 文本，没抓到真实学生操作
- 项目状态推进偏弱，很多 session 结束后仍停在 `not_started`

### 根本原因

- `TaskHost` 作为发起者被直接混进了保存消息，污染了对话文本和事件抽取输入
- 多角色自由对话下，模型很容易让少数角色垄断发言
- 事件抽取依赖消息文本，如果消息源被 prompt 污染，结果自然失真

### 解决方案

- 保存阶段排除 `TaskHost` 消息
- 事件抽取只基于真实成员消息
- 如果讨论过短或说话人太少，追加 repair prompt 引导继续展开
- repair 逻辑最多补两轮，避免无限修补

### 验证

后续真实运行输出显示：

- `TaskHost` 已不再写入最终保存消息
- 多成员参与情况相比首轮有改善
- 开始出现更可用的项目状态承接

### 遗留问题

- 少数 session 仍可能由一两个人主导
- 事件抽取覆盖率仍然不高

## 2026-05-06 | timeline_v2 运行兼容修复与自然性补强

### 当时目标

减少 timeline_v2 的运行失败，并进一步控制输出自然性。

### 遇到的问题

- controller 额外调用下，AutoGen cache 触发磁盘兼容问题
- 有时模型会写出一条消息里包含多个角色名的伪对话格式
- controller 即使识别到有进展，也可能把 `progress_level` 留在 `not_started`

### 根本原因

- AutoGen 默认 cache 行为在当前运行环境里不稳定
- 多智能体 prompt 不够明确时，模型会“帮别人补台词”
- 项目状态完全依赖 controller 结果时，容易过于保守

### 解决方案

- 在 timeline 运行线中将 `llm_config["cache_seed"] = None`
- 在 persona prompt 中明确要求“一条消息只代表一个人”
- 在消息序列化阶段清理同名开头，并截断明显的跨角色台词污染
- 收尾前提高最低参与门槛，要求更多不同成员真正发言
- 对 `state_after_session` 增加轻量后处理，根据决策数和分工数自动提升进度阶段

### 验证

- dry-run 仍可通过
- 需要继续跑一轮短程真实运行确认自然性改善是否稳定

### 影响

timeline_v2 当前已经不只是“能跑”，而是在开始进入质量打磨阶段。

## 2026-05-06 | 文档同步到双轨架构

### 当时目标

确保 `docs/` 记录和当前代码现实一致，不再停留在旧版单段群聊阶段。

### 本次更新内容

- 更新 `project_context.md`，明确项目边界和双轨结构
- 更新 `project_status.md`，把重心切换到 timeline_v2 自然性打磨
- 更新 `architecture.md`，补充两条运行链路和项目级输出
- 更新 `config_guide.md`，补充 timeline 相关配置与命令
- 更新 `decisions.md`，记录双轨保留策略与隐藏式收尾决策
- 更新 `learning_notes.md`，补充连续会议、隐藏控制和事件层模拟原理

### 影响

后续 AI 或开发者重新进入项目时，可以直接从文档恢复到 timeline_v2 的真实状态，不会再误以为仓库只有单段群聊版本。

## 2026-05-06 | 修复 timeline_v2 中途终止时项目级结果丢失的问题

### 当时目标

验证 timeline_v2 在真实运行中即使没有跑完整个项目，也能保存已经完成的 session。

### 发现的问题

真实运行超时后，`run.log` 已经显示 session 完成，但 `state.json` 里仍然没有对应 project 内容。

### 根本原因

此前 timeline_v2 只在整个 `project` 结束后，才把结果写回 `dataset["projects"]` 和 `projects.jsonl`。这意味着一旦中断发生在 project 内部，前面已完成的 session 仍会丢失。

### 解决方案

- 新增 `project_checkpoints.jsonl`
- 每完成一个 session，就写入当前 project 快照
- 同步把 in-progress 项目写回 `state.json`
- 保留原有 `projects.jsonl`，继续只记录完整 project 的最终结果

### 验证

在 `2026-05-06` 的一次 300 秒真实运行中：

- 进程在第 3 个 session 中途被终止
- `state.json` 已保留前 2 个 session 的完整内容
- `project_checkpoints.jsonl` 已写入 project 进行中的增量快照

### 影响

timeline_v2 现在满足“项目中途异常终止，也能保留前面已生成内容”的核心要求。

## 2026-05-06 | 验证消息清洗与当前残留问题

### 当时目标

检查模型输出里的角色名前缀和伪多人发言，在最终保存结果中是否被清洗。

### 验证结果

- 控制台原始输出里仍能看到 `Mia:`、`Leo:`、`Max:` 这类模型前缀
- 保存到 `state.json` / `project_checkpoints.jsonl` 的消息文本已清洗掉这类前缀
- 第一轮 session 的最终落盘文本恢复成单人自然发言格式

### 当前残留问题

- 某些 session 仍可能只有 2-3 条有效消息
- 有些 session 虽然能保留，但讨论深度仍偏浅
- 事件抽取仍然偏少，很多自然对话没有触发结构化事件

### 下一步

继续优化：

- repair 逻辑
- 事件触发规则
- session 深度和成员参与度

## 2026-05-06 | 切换为简易 API 双模型配置模板

### 当时目标

用户准备从 OpenRouter 切换到简易 API，并希望按“主对话模型 + 控制器模型”的方式配置。

### 问题

原来的 `configs/oai_config_list.json` 是单一 `config_list` 数组，所有 agent、controller 和 closer 都共用同一个模型。这样在 `timeline_v2` 中不够灵活：

- 主对话需要更自然、更快的模型
- controller/closer 更需要稳定 JSON 和指令遵守
- 全部调用使用同一模型会增加成本和调参难度

### 解决方案

- 将 `configs/oai_config_list.json` 改为双模型对象结构
- `dialogue` 默认使用 `gemini-2.5-flash`
- `controller` 默认使用 `gpt-4.1-mini`
- API 地址改为 `https://jeniya.cn/v1`
- API key 保留 `YOUR_JENIYA_API_KEY` 占位符，由用户本地填写
- `timeline_v2` 新增 `ModelConfigBundle`，分别传入主对话模型和控制器模型
- `legacy` 兼容新对象格式，默认读取 `dialogue`

### 验证

- `compileall` 通过
- `run_timeline_experiments.py --dry-run` 通过
- `run_experiments.py --dry-run` 通过

### 影响

后续可以用更快的模型生成学生对话，同时用更稳的模型做内部控制，降低长流程运行慢和反复 repair 的概率。

## 2026-05-06 | 简易 API 双模型完整运行验证

### 当时目标

用户已填入新的简易 API key，需要验证 API 是否能真实调用，并尽量完整跑完一次 `timeline_v2` 长时间线对话生成。

### 验证步骤

- 先分别调用 `dialogue` 和 `controller` 两套模型做最小请求测试。
- 再运行 `timeline_positive_4`，生成一个完整 project。
- 运行命令使用 `run_timeline_experiments.py --config-list-file configs/oai_config_list.json --only-groups timeline_positive_4`。

### 验证结果

- `dialogue=gemini-2.5-flash` 可通过 `https://jeniya.cn/v1/chat/completions` 正常返回。
- `controller=gpt-4.1-mini` 可通过同一 OpenAI-compatible 接口正常返回。
- 完整运行成功，输出目录为 `outputs/persona_project_timeline_dataset_20260506_192154/`。
- 生成状态为 `completed`。
- 项目生成了 5 个 session。
- 每个 session 都有 4 名成员参与。
- 每个 session 的消息数分别为 12、12、13、13、12。
- 最终保存的 `messages` 中没有发现 `TaskHost`、`[[SESSION_END]]` 或明显的角色名前缀污染。
- 生成了 4 个结构化事件。

### 发现的问题

- 单个 5-session project 运行约 13 分钟，仍然偏慢。主要原因是 AutoGen GroupChat 会产生大量 API 调用，而不是 API 不可用。
- AutoGen 日志持续提示 `Model ... is not found. The cost will be 0`，这是 AutoGen 成本统计不认识简易 API 模型名导致的警告，不影响生成。
- 项目最终结局为 `stalled`，但状态历史中已有 12 条决策和 7 条分工，说明当前 `project_outcome` 判断偏保守。
- 5 个 session 的 `session_outcome` 都是 `progress_made_and_pause`，结局类型还不够多样。
- 事件抽取只有 4 条，且主要集中在 `edit_slides` 和 `upload_document`；像“找模板”“搭骨架”等真实操作没有被充分识别。

### 下一步

- 增加简易 API 模型价格字段或禁用 AutoGen 成本警告，减少日志噪音。
- 调整项目终局判断，让高截止压力、多决策、多分工的项目可以进入 `forced_submission` 或 `completed`。
- 扩展事件抽取规则，覆盖“找模板”“搭骨架”“做演示”“预留模块”等更贴近学生项目的动作。
- 如需提高批量效率，可增加更短的测试配置，例如固定 2 个 session 的 smoke test group。

## 2026-05-06 | 新增 timeline_v2 直观对话转写文件

### 当时目标

让 timeline_v2 的输出不只适合程序读取，也适合人类快速浏览。用户希望新增一个更直观的结果文件，按时间记录每一次对话，只保留说话人、发言内容和学生行为操作。

### 问题

此前完整结果主要保存在 `final_dataset.json`、`state.json`、`projects.jsonl` 和 `project_checkpoints.jsonl` 中。这些文件结构完整，但嵌套较深，不适合直接阅读整条项目对话时间线。

### 根本原因

结构化 JSON 适合下游评估项目和程序处理，但不适合人工快速判断生成质量。当前项目正在打磨自然学生团队对话，因此需要一个人工可读的转写视图。

### 解决方案

新增 `conversation_timeline.txt`：

- 每次 timeline_v2 运行自动在输出目录下创建该文件。
- 每完成一个完整 project，就把该 project 的所有 session 追加进去。
- 每个 session 按顺序输出 `说话人：发言内容`。
- 如果某条消息触发了学生行为事件，则在对应轮次下方追加 `【操作】` 行。

### 验证

- 对已有完整运行目录 `outputs/persona_project_timeline_dataset_20260506_192154/` 做了回填，已生成 `conversation_timeline.txt`。
- 预览确认文件按 5 个 session 顺序展示对话。
- 文件中未发现 `TaskHost`、`session_prompt` 或 `[[SESSION_END]]` 污染。

### 遗留问题

当前 `conversation_timeline.txt` 是完整 project 结束后写入。如果未来希望“即使 project 中途终止，也能看到已完成 session 的直观转写”，需要把该文件升级为 session 级增量写入。

## 2026-05-06 | timeline_v2 第一阶段质量升级

### 当时目标

把前一轮“功能升级路线图”中的低风险高收益部分先落地：让生成结果更容易诊断、更能中断保留、更能覆盖学生操作事件，并减少终局判断偏保守的问题。

### 问题

- `conversation_timeline.txt` 仍是完整 project 结束后才写入，中途终止时无法直接阅读已完成 session。
- 事件抽取只覆盖少量关键词，最近完整运行只有 4 个事件。
- `project_outcome` 容易偏向 `stalled`，即使项目已有多条决策和分工。
- 缺少独立质量报告，人工只能反复打开 JSON 或转写文件排查问题。
- 场景库只有 3 个场景，后续批量生成容易风格单一。

### 解决方案

本次更新：

- 将 `conversation_timeline.txt` 升级为 session 级增量写入。
- 新增 `quality_report.md` 和 `quality_report.json`，检测参与度失衡、伪多人发言、重复、事件过少和终局矛盾。
- 扩展事件关键词，覆盖找模板、搭骨架、做演示、改稿、分工、查案例、整理引用、测试 demo、提交等学生项目动作。
- 在事件对象中增加 artifact 元数据，并在 project record 中汇总 `artifacts`。
- 优化 `finalize_project_outcome`，综合进度、决策数、分工数、deadline pressure 和提交/放弃语言信号判断项目结局。
- 新增 `generation_settings` 配置，把最少消息数、参与人数、repair 次数、closer 开关、质量诊断开关、超时时间和增量转写开关外置。
- 新增 `timeline_smoke_test` 分组、`--smoke-test` 和 `--estimate-cost` 命令入口。
- `timeline_smoke_test` 默认不混入全量运行，只在显式 smoke test 或指定 group 时运行。
- 将 timeline 场景库扩展到 9 个教育场景。

### 验证

- `compileall src/persona_project_timeline_dataset` 通过。
- `run_timeline_experiments.py --dry-run` 通过，加载 11 个 persona、9 个 scenario、6 个 group。
- `run_timeline_experiments.py --estimate-cost --smoke-test` 通过，能输出 1 个 project、2 个 session 的运行规模估算。
- 用已有完整数据测试质量诊断函数，能生成 1 个 project、5 个 session、4 个事件和 2 条质量警告的诊断结果。

### 遗留问题

- `enable_event_controller` 目前只是配置预留，尚未接入 LLM 二阶段事件抽取。
- `--estimate-cost` 当前是运行规模估算，不是精确 token 或价格估算。
- 断点续跑 `--resume-run-dir` 尚未实现。
- 需要再跑一次真实 `--smoke-test` 来观察新增质量报告和增量转写在真实生成中的效果。

## 2026-05-06 | 新增 persona 组合实验配置

### 当时目标

基于 `persona.json` 中已有的 11 类学生 persona，设计多样化学生组合，并让 `timeline_v2` 能批量生成不同类型的学生团队对话。

### 问题

此前 `configs/experiment_groups_timeline.json` 已经有一些正向、混合和高冲突分组，但这些分组主要服务 timeline_v2 功能验证，不是专门围绕 persona 组合实验系统设计的。

### 解决方案

新增独立配置文件：

```text
configs/experiment_groups_persona_composition.json
```

该文件不覆盖原有 timeline 配置，而是新增 12 个 persona 组合 group：

- `composition_positive_balanced_4`
- `composition_positive_balanced_5`
- `composition_creative_vs_critical`
- `composition_execution_heavy`
- `composition_maintenance_heavy`
- `composition_free_rider_managed`
- `composition_free_rider_unmanaged`
- `composition_dominator_buffered`
- `composition_dominator_unbuffered`
- `composition_blocker_conflict`
- `composition_lone_wolf_conflict`
- `composition_high_dysfunction`

这些组合覆盖稳定正向、高功能正向、创意批判拉扯、执行导向、维护导向、搭便车、支配者、阻碍者、独狼和高失调等团队形态。

### 验证

已完成非 API 验证：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition.json --dry-run
```

结果：

- 成功加载 11 个 persona
- 成功加载 9 个 scenario
- 成功加载 12 个 persona composition group
- 所有 `member_role_ids` 和 `scenario_id` 引用有效

同时完成运行规模估算：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition.json --estimate-cost
```

结果：

- 预计生成 12 个 project
- 预计生成 36-57 个 session
- 粗略模型调用至少 108 次，实际会更高，因为 AutoGen 需要进行 speaker selection 和多轮对话调用

### 下一步

先真实运行 3 个代表性组合：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition.json --only-groups composition_positive_balanced_4,composition_free_rider_managed,composition_high_dysfunction
```

确认输出质量、成本和运行时长可接受后，再考虑完整运行全部 12 组。

## 2026-05-06 自发发言机制设计与实现

### 当前目标

在不牺牲对话质量的前提下，减少 AutoGen `speaker_selection_method="auto"` 带来的额外选人调用，并让学生团队对话更像真实小组讨论，能够出现自发发言、短句插话、被点名后回应、沉默收束和抢话式推进。

### 问题原因

AutoGen 的 `auto` speaker selection 会在每轮对话外额外调用模型判断下一个说话人。对于 timeline_v2 的长期多 session 生成，这会显著拉长运行时间。同时，`auto` 更像外部主持人选人，不完全符合“每个学生根据情境自发说话”的模拟目标。

### 解决方案

- 新增 `src/persona_project_timeline_dataset/turn_taking.py`，实现本地 `urgency_queue` 发言策略。
- 通过 `urgency_score` 综合 persona、出勤状态、是否被点名、是否长期未发言、deadline 压力、冲突/问题/分工信号等因素选择下一个发言者。
- 当所有成员发言紧迫度较低，且对话已有足够轮数时，允许返回 `None` 让 session 自然停止。
- 用连续短 turn 的方式模拟抢话和插话，不做真实并发语音重叠。
- 新增 `configs/experiment_groups_persona_composition_urgency.json`，继承 persona composition 基线配置，只覆盖发言选择策略和 turn-taking 参数。
- 扩展 session 输出和质量报告，记录 `speaker_selection_policy`、`interruption_like_turns`、`silence_stop_used` 和 `speaker_selection_trace`。

### 技术依据

- AutoGen 官方支持自定义 `speaker_selection_method` callable。
- University of Electro-Communications 2026 年关于 interruptions / silence 的研究提供了“发言竞价、沉默、打断”的设计参考。
- Generative Agents 和 SOTOPIA 的思路支持用角色、状态和社会情境驱动 agent 行为，而不是固定轮流发言。

### 验证计划

- 先运行 `python -m compileall src`。
- 再运行 urgency 配置的 `--dry-run` 和 `--estimate-cost`。
- 使用构造消息测试 `urgency_queue` 是否能选择未发言者、被点名者和冲突调和者。
- 最后再用 API 跑 1 个小组做 smoke test，对比 `auto` 和 `urgency_queue` 的运行时间、发言均衡和自然插话效果。

### 验证结果

已完成静态验证：

```powershell
python -m compileall src
```

结果：通过。

已完成配置验证：

```powershell
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition_urgency.json --dry-run
python run_timeline_experiments.py --experiment-file configs/experiment_groups_persona_composition_urgency.json --estimate-cost
```

结果：

- 成功加载 12 个 persona composition group
- 预计 12 个 project，36-57 个 session
- speaker policy 显示为 `urgency_queue`
- 估算提示已更新为：`urgency_queue` 会避免每轮额外 LLM speaker-selection 调用

已完成非 API selector 行为验证：

- 开场场景选择 `Ivy`
- 被点名场景选择 `Max`
- 冲突场景选择 `Mia`
- 自然收束场景返回 `None`
- `speaker_selection_trace` 能正确记录 `selected`、`interruption_like` 和 `natural_stop`

已完成 3 个代表组 API 验证：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition_urgency.json --only-groups composition_positive_balanced_4,composition_free_rider_managed,composition_high_dysfunction
```

输出目录：

- `outputs/persona_composition_urgency_timeline_dataset_20260506_230420`

与之前 `auto` 模式 3 组结果对比：

- `auto` 输出目录：`outputs/persona_composition_timeline_dataset_20260506_214134`
- `auto`：12 个 session，145 条消息，HTTP POST 285 次，用时约 34.81 分钟
- `urgency_queue`：12 个 session，148 条消息，HTTP POST 156 次，用时约 20.95 分钟
- 调用次数下降约 45.3%
- 运行时间下降约 39.8%
- `urgency_queue` 输出中 12 个 session 均记录了 `speaker_selection_policy="urgency_queue"`
- `interruption_like_turns` 总数为 68，说明新策略确实产生了大量插话/抢话式 turn 诊断

### 观察到的问题

- 高失调组中 `Derek` 发言占比偏高，但这符合 `dominator` persona 的预期，也被质量报告提示为 dominance 风险。
- `silence_stop_used` 这次为 0，说明大部分 session 仍是跑到自然轮数或 controller 收尾，而不是由低紧迫度直接停止。后续可以继续调低 `min_turns_before_silence` 或提高 `silence_threshold` 做对照实验。
- 模型偶尔仍会在内容中误称上一位发言者，例如把 Ivy 的观点说成 Mia 的观点。这属于模型生成内容问题，不是 speaker selection 本身的问题，后续可通过 prompt 或质量诊断继续处理。

## 2026-05-07 项目级完整收束模式

### 问题

前一版 persona composition 输出虽然能生成多次 session，但整体更像“达到预设会议次数后结束”。用户阅读 `conversation_timeline.txt` 时会感觉项目事件线还没有完全收束，尤其是最后一场仍像普通中途讨论。

### 修改

- `GenerationSettings` 新增 `min_project_sessions_before_terminal`，避免项目过早接受终局信号。
- `GenerationSettings` 新增 `force_project_closure_on_final_session`，最后一次 session 必须给出项目级结局。
- `configs/experiment_groups_persona_composition_urgency.json` 将默认 session 数提高到 `5-8`，并把 `max_round` 提高到 `14`。
- controller 在最后一次 session 会收到 `force_project_closure=true`，必须从 `completed/stalled/abandoned/forced_submission` 中选择项目级结局。
- closing message 会根据 `project_end_signal` 写出最终口径，例如“先按这个版本提交”，而不是继续说“下次再推进”。
- 修正终局后处理：`forced_submission` 不再被 `finalize_project_outcome()` 覆盖成 `completed`。

### 单组实验

运行命令：

```powershell
python run_timeline_experiments.py --config-list-file configs/oai_config_list.json --experiment-file configs/experiment_groups_persona_composition_urgency.json --only-groups composition_positive_balanced_4
```

输出目录：

- `outputs/persona_composition_urgency_timeline_dataset_20260506_234830`

结果：

- 生成 1 个 project
- 计划 8 次 session，实际生成 8 次 session
- 每次 session 消息数为 `[14, 14, 10, 14, 14, 15, 8, 15]`
- `speaker_selection_policy` 均为 `urgency_queue`
- `interruption_like_turns` 总数为 43
- `silence_stop_used` 出现 2 次
- 最后一场出现明确提交口径：“时间紧迫，咱们就先按这个版本提交吧”

### 仍需注意

- 该次实验是在修正 `forced_submission` 覆盖问题之前运行的，所以文件中的项目最终结局显示为 `completed`，但最后 session 的 `project_end_signal` 是 `forced_submission`。代码已修正，后续新运行会保留 `forced_submission`。
- `session_outcome` 仍全部是 `progress_made_and_pause`，说明 session 级结局类型还不够多样，后续可继续优化 controller。
## 2026-05-07 persona 组合 urgency 批量生成与统一汇总

### 当前目标

针对同一功能模块 `timeline_v2`、同一 API 配置、同一 `urgency_queue` 自发发言机制，把 12 组不同 persona 组合的对话生成结果统一放入一个 collection 目录，避免不同批次输出分散在多个 timestamp 文件夹中，导致后续复查困难。

### 修改内容

- 新增并完善 `scripts/collect_timeline_results.py`，用于把多个 timeline_v2 运行目录汇总到一个 collection。
- collection 支持扫描 `collection_dir/runs/`，因此后续同类批量实验可以直接把输出放进同一个总目录。
- collection 会生成统一入口 `README.md`、总索引 `group_overview.md/json`、差异报告 `persona_difference_report.md`、合并数据 `final_dataset_combined.json`、合并直观转写 `conversation_timeline_combined.txt`。
- 每个分组会被拆分到 `groups/<group_id>/`，其中包含该分组的 `conversation_timeline.txt`、`summary.md` 和 `project.json`。
- 修复了汇总脚本中中文模板字符串的乱码问题，保证新生成的 collection 总览文件可读。

### 运行结果

统一汇总目录：

```text
outputs/persona_composition_urgency_collection_20260507/
```

已完成 12 / 12 个 persona composition 分组：

- `composition_positive_balanced_4`
- `composition_positive_balanced_5`
- `composition_creative_vs_critical`
- `composition_execution_heavy`
- `composition_maintenance_heavy`
- `composition_free_rider_managed`
- `composition_free_rider_unmanaged`
- `composition_dominator_buffered`
- `composition_dominator_unbuffered`
- `composition_blocker_conflict`
- `composition_lone_wolf_conflict`
- `composition_high_dysfunction`

最终汇总状态：

- missing groups: `none`
- partial groups: `none`
- 所有分组均已生成完整 planned/generated session。

### 初步差异观察

- 正向组和维护/执行型组整体更容易持续推进，多个分组结局为 `completed`。
- 支配者、阻碍者、独狼、搭便车等混合失调组仍可能完成或被迫提交，但更容易出现强势推进、临时僵持、分工拉扯或事件推进不均。
- `composition_high_dysfunction` 新版结果为 5 个 session，其中出现 2 次 `temporary_stalemate`，比早期 3-session 版本更能体现高失调组的拖延和僵持。
- 当前负面组并不一定都会 `abandoned`，这可以保留为真实样本：现实学生团队即使关系失调，也可能在 deadline 压力下被迫提交。

### 后续复查重点

- 人工阅读 `persona_difference_report.md` 和各组 `conversation_timeline.txt`，确认角色差异是否足够明显。
- 如果希望高失调组更容易不了了之，可以后续单独提高冲突倾向、降低 `force_project_closure_on_final_session` 的提交倾向，生成新的对照 collection。
- 当前 collection 可作为“同一模型、同一机制、不同 persona 组合”的第一版系统样本集。

## 2026-05-08 真实单组 timeline_v2 生成验证

- Goal: 选取一个学生组做一次真实 `timeline_v2` 生成，验证新的“纯对话转写 + 独立行为流 + 保留 JSON 接口”输出是否已经实际落地。
- Problem: 之前主要完成了代码修改、静态检查和 dry-run，还缺少一次真实 API 运行来确认输出文件是否按新约定生成。
- Root Cause: timeline 输出结构刚完成调整，如果不做真实运行，只能证明代码路径可执行，不能证明最终文件形态、时间戳写入和行为拆分在真实样本中都正常。
- Solution: 使用 `E:\CondaConfig\envs\autogen_env\python.exe` 运行 `run_timeline_experiments.py --config-list-file configs/oai_config_list.json --only-groups timeline_positive_4 --max-projects 1`，生成 1 个真实 project，并复核输出目录中的文本和 JSON 产物。
- Validation: 真实输出目录为 `outputs/persona_project_timeline_dataset_20260508_185119/`；已确认存在 `conversation_timeline.txt`、`behavior_timeline.txt`、`behavior_events.jsonl`、`final_dataset.json`、`quality_report.json/md`；`conversation_timeline.txt` 已显示带分钟级时间戳的纯对话转写；`behavior_events.jsonl` 已包含 `timestamp`、`source_basis`、`visibility` 等字段；`final_dataset.json` 已用 Python 成功解析；`quality_report.json` 显示本次生成 `1` 个 project、`5` 个 session、`24` 个事件，项目结局为 `completed`。
- Impact: 这次运行证明 timeline_v2 的新输出结构已经在真实生成链路中生效，后续评估或人工阅读可以直接使用分离后的转写与行为流；同时也暴露了当前样本层面的质量问题，主要是 `session_outcome` 多样性不足，以及第 4 次对话存在近似重复发言。
- Next: 继续优化 session 收尾与多样性控制；检查第 4 次对话的重复发言成因；再选 2 到 3 个差异更大的 persona/timeline 分组做小批量真实生成，验证新结构在不同团队风格下是否同样稳定。
