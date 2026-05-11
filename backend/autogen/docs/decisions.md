# 关键决策（Key Decisions）

## D-011 | Split timeline_v2 human output into pure transcript and separate behavior stream

- Date: 2026-05-08
- Background: The previous human-readable output mixed dialogue and behavior labels in the same transcript, which made it look more like system annotation than a realistic meeting record.
- Options considered:
  - Keep mixed transcript plus event markers
  - Remove behavior markers entirely and rely only on JSON
  - Split transcript and behavior into separate human-readable outputs while keeping structured JSON
- Decision: Keep `conversation_timeline.txt` as a pure timestamped transcript, add `behavior_timeline.txt` and `behavior_events.jsonl`, and preserve structured JSON as the stable program interface.
- Reasoning: This keeps the main reading experience close to meeting transcription while retaining an explicit activity layer for downstream evaluation and debugging.
- Impact: Future review, collection, and downstream tooling should treat transcript and behavior as separate surfaces. Event provenance is now part of the output contract through `source_basis` and `visibility`.

这个文件记录长期有效的技术和工程决策。详细排查过程写在 `dev_journal.md`，技术原理和方案比较写在 `learning_notes.md`。

## D-001 | 使用 AutoGen 0.2 的经典 GroupChat

- 日期：2026-04-27
- 背景：项目需要一个能直接支持多角色群聊的框架。
- 考察方案：
  - 使用 AutoGen 0.2 经典 `GroupChat`
  - 使用 AutoGen 0.4+ / 0.7+ 新架构
- 决策：使用 `autogen-agentchat>=0.2,<0.3`
- 理由：当前需求与经典 `GroupChat` API 更匹配，工程实现更直接。
- 影响：未来升级 AutoGen 需要显式迁移，不能直接改依赖版本。

## D-002 | 使用 OpenRouter 作为模型接口

- 日期：2026-04-27
- 背景：用户当前可用的是 OpenRouter API。
- 考察方案：
  - 使用 OpenAI 官方接口
  - 使用 OpenRouter OpenAI-compatible 接口
  - 使用本地模型服务
- 决策：使用 OpenRouter，并通过 `base_url=https://openrouter.ai/api/v1` 接入。
- 理由：符合当前可用资源，且 OpenRouter 与 OpenAI SDK 兼容。
- 影响：模型路由可能受 OpenRouter/provider 策略影响，切换模型前需要先做最小请求测试。

## D-003 | 将模型从 openai/gpt-4o-mini 切换到 qwen/qwen-2.5-7b-instruct

- 日期：2026-04-27
- 背景：`openai/gpt-4o-mini` 返回 403，无法用于当前账号和路由。
- 决策：改用 `qwen/qwen-2.5-7b-instruct`。
- 理由：同一 key 下该模型已通过最小化请求验证。
- 影响：生成质量和风格会受 Qwen 模型影响，后续如更换模型需要重新验证。

## D-004 | 输出采用增量保存

- 日期：2026-04-27
- 背景：长对话运行容易中断，最终一次性保存会丢失中间结果。
- 考察方案：
  - 全部运行结束后保存
  - 每完成一段对话后保存
- 决策：每完成一段对话后写入 `state.json` 和 `dialogues.jsonl`。
- 理由：降低中断损失，方便恢复和复盘。
- 影响：输出目录中文件更多，但可追溯性明显增强。

## D-005 | 先做领域无关框架，再通过 prompt 切换教育场景

- 日期：2026-04-28
- 背景：主项目是教育评估，但用户希望框架不被教育场景写死。
- 决策：先建立通用 multi-agent 对话生成框架，再通过场景 prompt 和配置切换到教育领域。
- 理由：这样项目可复用性更强，也方便后续跨场景比较。
- 影响：后续应新增场景库，而不是把教育任务硬编码在 runner 中。

## D-006 | 项目记录体系采用“AGENTS 规则 + 模板脚手架 + 脚本”

- 日期：2026-04-30
- 背景：用户希望未来所有项目都能实时记录进展和复盘材料。
- 考察方案：
  - 只依赖 `AGENTS.md`
  - 只复制 Markdown 模板
  - 同时使用 `AGENTS.md`、模板和脚本
- 决策：采用三者结合。
- 理由：`AGENTS.md` 约束 AI 行为，模板提供文件结构，脚本提供可执行入口。
- 影响：当前项目新增 `docs/`、`project_recording_template/` 和 `scripts/`。

## D-007 | 文档体系采用“入口、上下文、日志、状态、学习、配置、案例”分工

- 日期：2026-05-06
- 背景：项目后续会长期迭代，且用户希望文档同时服务于 AI 上下文恢复、个人学习、项目复盘、面试表达和论文素材沉淀。
- 考察方案：
  - 把所有内容集中写入 README
  - 用一个总日志文件记录所有内容
  - 按用途拆分为多个职责明确的 Markdown 文件
- 决策：按用途拆分文档职责。
- 理由：README 适合快速入口，不适合承载完整历史和技术学习；开发日志适合时间线，不适合当前状态快照；技术学习和长期决策也需要分开，避免后续维护混乱。
- 影响：当前明确使用 `README.md`、`project_context.md`、`architecture.md`、`dev_journal.md`、`project_status.md`、`decisions.md`、`learning_notes.md`、`config_guide.md`、`file_roles.md` 和 `case_study.md` 分别承担不同职责。

## D-008 | 保留 legacy 基线，并在独立目录中孵化 timeline_v2

- 日期：2026-05-06
- 背景：项目需要从“单段群聊”升级为“连续会议 + 项目状态 + 事件流”的自然学生团队对话生成器，但旧版本仍有对照价值。
- 考察方案：
  - 直接在原始 `persona_groupchat_dataset` 上重构
  - 完全替换旧版本
  - 保留旧版本，并在新目录中实现 timeline_v2
- 决策：保留 `src/persona_groupchat_dataset/` 和 `run_experiments.py`，新增 `src/persona_project_timeline_dataset/` 和 `run_timeline_experiments.py`。
- 理由：这样可以降低改造风险，方便新旧结果对比，也便于后续定位 timeline 改动是否引入退化。
- 影响：当前仓库形成双轨结构，文档、配置和输出都需要明确区分 `legacy` 与 `timeline_v2`。

## D-009 | timeline_v2 采用“隐藏式结束控制 + 项目状态承接”，不把控制 token 暴露到最终文本

- 日期：2026-05-06
- 背景：自然学生对话既需要能结束，又不能在最终数据里留下过于机械的显式控制痕迹。
- 考察方案：
  - 完全依赖最大轮数停止
  - 在最终文本中保留显式结束 token
  - 使用内部 controller / closer，并在保存前清除内部结束标记
- 决策：采用隐藏式结束控制。
- 理由：这样可以同时保留自然性和可控性。对话在生成时仍可借助内部结束信号，但最终数据文本保持自然。
- 影响：timeline_v2 需要额外的 controller 分析和 closing utterance 生成，运行成本高于 legacy，但输出更适合作为下游原始数据。

## D-010 | timeline_v2 采用双模型配置

- 日期：2026-05-06
- 背景：timeline_v2 的主对话生成和内部控制调用对模型能力的要求不同。主对话更关注中文自然性、速度和成本；controller/closer 更关注 JSON 稳定性和指令遵守。
- 考察方案：
  - 所有调用继续使用一个模型
  - 主对话和控制器分别使用不同模型
- 决策：`configs/oai_config_list.json` 支持 `dialogue` 和 `controller` 两套配置。当前模板使用简易 API，`dialogue` 为 `gemini-2.5-flash`，`controller` 为 `gpt-4.1-mini`。
- 理由：这能降低长流程成本和等待时间，同时让控制层更稳定。
- 影响：timeline_v2 会读取双模型配置；legacy 入口兼容该格式并读取 `dialogue`。
