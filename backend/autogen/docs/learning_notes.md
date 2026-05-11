# 技术学习记录（Learning Notes）

## 2026-05-08 | Why split transcript and behavior

When a transcript mixes dialogue lines with system-generated behavior markers, the result is easy to debug but less realistic as a meeting record. A better pattern is:

- transcript layer: who said what, with time
- behavior layer: who did what, when, and why the event exists
- structured JSON layer: stable machine interface

## 2026-05-08 | Validation terminology used in this repo

These terms are all about validation, but they happen at different layers and have different costs.

### Static check

Static check means: **check code or file structure first, without depending on a full real run.**

In this repo, typical static checks answer questions like:

- Can Python still parse the files?
- Did an edit introduce syntax or indentation errors?
- Do imports and basic file structure still make sense?

One concrete example is:

```powershell
E:\CondaConfig\envs\autogen_env\python.exe -m compileall src
```

`compileall` does not prove the feature is correct. It only proves the code is still readable by Python. So static checks are cheap and useful, but shallow.

### Function-level spot check

Function-level spot check means: **inspect or exercise a few critical functions directly instead of running the whole system end to end.**

This is useful when:

- the full run is slow
- the full run costs API money
- you changed only one logic layer and want quick feedback

For this timeline work, examples of function-level spot checks are:

- checking whether behavior filtering removes plan-only actions
- checking whether behavior summaries still say real completed actions
- checking whether `present_defense` is inferred too aggressively

The key idea is local verification of the most risk-prone logic.

### Dry-run

`dry-run` means: **walk through the execution flow without doing the expensive or fully real action.**

In this repo, `--dry-run` usually means:

- load configs
- resolve groups / projects / session plans
- validate the run setup
- show what would run
- but do not perform the full real generation workload

This is best understood as a rehearsal. It catches config mistakes and scale mistakes early, before you spend time or tokens.

### compileall

`compileall` is a built-in Python module that batch-compiles `.py` files. In practice, it is often used as a lightweight static check.

What it can tell you:

- "Python can still parse these files."

What it cannot tell you:

- whether the business logic is correct
- whether outputs look natural
- whether the behavior layer matches the product requirement

So it protects against broken code, not against wrong logic.

### Smoke test

`smoke test` means: **run the smallest real end-to-end case just to confirm the system basically works.**

You can think of the strength ladder like this:

- static check: inspect the code shape
- function-level spot check: inspect a few critical logic units
- dry-run: rehearse the workflow
- smoke test: run one small real case

### How these terms mapped to this task

For the recent `timeline_v2` behavior-layer changes, the terms roughly mapped to:

- static check: `python -m compileall ...`
- function-level spot check: review behavior filtering, summary formatting, and between-session inference logic
- dry-run: `run_timeline_experiments.py --dry-run`
- smoke test / real validation: run one real group and inspect `conversation_timeline.txt`, `behavior_timeline.txt`, `behavior_events.jsonl`, and `final_dataset.json`

This split is useful because it lets humans read the dialogue like a transcript while keeping behavior provenance explicit through fields such as `source_basis` and `visibility`.

The timestamp simulation is intentionally minute-level rather than second-level. It is detailed enough to make multi-session project timelines feel continuous, but not so detailed that it pretends to be a true calendar reconstruction.

这个文件面向计算机专业新手，记录项目中遇到的技术问题、考察过的方案、最终选择和相关原理。它比 `decisions.md` 更详细，比 `dev_journal.md` 更偏知识沉淀。

## 1. AutoGen 0.2 与 GroupChat

### 需要解决的问题

项目需要让多个角色围绕同一个任务自主对话，因此需要一个 multi-agent 框架。

### 考察过的方案

- 直接调用 OpenAI / OpenRouter API，自己写多角色轮转逻辑
- 使用 AutoGen 经典 `GroupChat`
- 使用更新版本 AutoGen 的新架构

### 最终选择

使用 AutoGen 0.2 的经典 `GroupChat`。

### 原理说明

AutoGen 中常见对象：

- `AssistantAgent`
  表示一个由 LLM 驱动的智能体。

- `UserProxyAgent`
  表示用户或任务发起者，在本项目中用于发起任务。

- `GroupChat`
  保存参与者、历史消息和最大轮数等群聊状态。

- `GroupChatManager`
  负责选择下一个发言者，并推动群聊继续。

### 为什么固定版本

`autogen-agentchat~=0.2` 可能安装到 0.7.x，因为 Python 依赖版本规则中 `~=` 并不等于“只安装 0.2.x”。为了避免 API 漂移，项目使用：

```text
autogen-agentchat>=0.2,<0.3
```

## 2. OpenRouter 与 OpenAI-compatible 接口

### 需要解决的问题

用户当前只有 OpenRouter API，需要让 AutoGen 通过 OpenRouter 调用模型。

### 使用方法

OpenRouter 提供 OpenAI-compatible API，因此可以通过 OpenAI SDK 的 `base_url` 接入：

```json
{
  "model": "qwen/qwen-2.5-7b-instruct",
  "api_key": "YOUR_API_KEY",
  "base_url": "https://openrouter.ai/api/v1"
}
```

### 踩坑记录

`openai/gpt-4o-mini` 返回过 403：

```text
The request is prohibited due to a violation of provider Terms Of Service.
```

排查后发现 key 和余额正常，问题集中在模型路由或 provider 策略，而不是项目代码。

### 学到的原则

换模型前先做最小化请求测试。不要直接把长任务跑起来，否则失败成本高。

## 3. 增量保存（Incremental Persistence）

### 需要解决的问题

LLM 长任务经常会因为 API 报错、网络、用户中断或对话漂移而失败。如果只在最后保存，前面生成的内容会丢失。

### 最终方案

每次运行创建一个独立目录：

```text
outputs/<run_id>/
```

并写出：

- `state.json`
- `dialogues.jsonl`
- `metadata.json`
- `run.log`
- `final_dataset.json`

### 原理说明

`dialogues.jsonl` 是 JSON Lines 格式，每一行是一条完整 JSON。它适合流式追加，因为不需要等全部数据生成完才能形成一个合法文件。

`state.json` 是当前整体状态快照，适合中断后查看进度。

## 4. 对话终止控制

### 需要解决的问题

多个 LLM agent 对话时，可能一直重复、附和或跑题，无法自然结束。

### 考察过的控制方式

- 只靠 prompt 要求总结
- 设置最大轮数 `max_round`
- 加结束标记 `[GROUP_COMPLETE]`
- 增加总结代理或裁判代理

### 当前方案

当前已实现：

- `max_round`
- `allow_repeat_speaker=false`
- `[GROUP_COMPLETE]` 结束标记
- `termination_reason` 输出字段

### 当前局限

prompt 约束不是强规则。模型可能不输出结束标记，因此仍可能出现 `stopped_without_token`。

### 后续可改进

增加总结代理或裁判代理，在后几轮强制检查任务是否完成，并输出结构化总结。

## 5. 为什么 timeline_v2 要从“单段群聊”升级为“连续会议”

### 需要解决的问题

真实学生项目通常不是一次会就结束，而是：

- 第一次定方向
- 后面几次补资料、分工、返工、改汇报
- 有时中间还会因为人没到齐、实验失败、老师反馈而改变讨论重点

如果只生成一段群聊，就很难模拟这种连续推进。

### 当前方案

timeline_v2 引入：

- `project_id`
- 多个 `session`
- `project_state_history`
- `carryover_summary`

### 原理说明

每次 session 不是重新给一遍完整任务，而是承接上一轮的项目状态。这种做法比“每轮都重新开题”更接近真实项目协作。

### 学到的原则

想模拟长期协作，关键不是把 prompt 写得更长，而是让系统记住“上次发生了什么、还有什么没做完”。

## 6. 隐藏式结束控制（hidden ending control）

### 需要解决的问题

如果完全自由对话，LLM 可能一直空转；但如果直接在最终对话里保留 `[GROUP_COMPLETE]` 这类 token，数据看起来会很机械。

### 当前方案

timeline_v2 使用：

- 内部结束信号 `[[SESSION_END]]`
- controller 分析 session
- closer 在需要时补一条自然收尾
- 保存前清除内部 token

### 原理说明

这相当于把“控制逻辑”和“最终可读文本”分层：

- 控制层知道什么时候该停
- 数据层只保留自然对话内容

### 学到的原则

很多时候不要把控制信号直接暴露给最终数据。内部控制可以很工程化，但最终语料应该尽量自然。

## 7. 文本化多模态事件模拟

### 需要解决的问题

当前项目希望模拟学生除了说话之外还“做了什么”，但暂时不需要真的接图像模型或文件理解模型。

### 当前方案

先做 `event layer simulation`：

- 当学生提到查资料、上传文档、改 PPT、跑实验等行为时
- 系统生成一个结构化事件对象
- 同时把 `event_id` 挂到相关消息上

### 原理说明

这样可以得到两种信息：

- 对话文本里谁说了什么
- 项目过程中谁做了什么操作

虽然这些事件还是文本模拟，但已经比纯对话更接近真实协作数据。

### 学到的原则

多模态不一定非要一步到位做成“真图像 + 真文件”。很多时候先把事件层抽出来，就能为后续研究打下结构基础。

## 8. 项目记录体系

### 需要解决的问题

项目不只是要能运行，还要能长期复盘、学习和迁移到其他项目。

### 考察过的方案

- 只写 README
- 只依赖运行日志
- 只依赖 `AGENTS.md`
- 使用 `AGENTS.md` + Markdown 文档 + 脚本

### 最终选择

使用三层体系：

- `AGENTS.md`
  约束 AI 工作行为。

- `docs/`
  记录项目上下文、状态、日志、决策和学习内容。

- `scripts/`
  提供初始化、补录、事件记录和运行上下文采集命令。

### 维护原则

- 代码修改后更新 `dev_journal.md`
- 长期设计变化更新 `decisions.md`
- 新技术理解更新 `learning_notes.md`
- 当前阶段变化更新 `project_status.md`
- 配置变化更新 `config_guide.md`

## 9. 为什么文档要按职责拆分

### 需要解决的问题

当项目持续时间变长后，如果所有内容都写在一个文件里，会出现两个问题：

- 人很难快速找到当前状态、历史原因或配置说明。
- AI 在上下文不足时容易把旧信息、当前状态和长期计划混在一起，产生错误假设。

### 当前拆分方式

- `README.md`
  面向第一次接触项目的人，负责快速入门。

- `project_context.md`
  面向上下文恢复，负责完整说明项目背景、目标和现状。

- `architecture.md`
  面向工程理解，负责说明运行链路、模块职责和数据流。

- `dev_journal.md`
  面向过程复盘，负责按时间记录问题、排查、根因和解决方案。

- `project_status.md`
  面向恢复开发，负责记录当前阶段、下一步和风险。

- `decisions.md`
  面向长期维护，负责记录关键决策及理由。

- `learning_notes.md`
  面向学习，负责解释技术原理和方案比较。

- `config_guide.md`
  面向人工操作，负责说明可配置文件怎么改。

### 学到的原则

好的项目文档不是越多越好，而是每个文件都有单一职责（single responsibility）。这样后续维护成本更低，也更适合 AI 读取。

## 10. Python 新手需要注意的项目概念

### CLI

CLI 是 command-line interface，表示命令行接口。本项目的 CLI 入口是：

```text
run_experiments.py
```

### dataclass

`dataclass` 是 Python 用来简化数据结构定义的工具。它适合表示配置对象，例如 Persona、Group、Experiment。

### Path

`pathlib.Path` 是 Python 处理路径的现代方式，比字符串路径更清晰。

### JSON

JSON 是常见的数据交换格式。本项目用 JSON 存配置和输出结果。

### JSONL

JSONL 是每行一个 JSON 对象的文件格式，适合持续追加数据。
