# 项目状态（Project Status）

## 2026-05-08 Latest Update

Completed:

- `timeline_v2` transcript output now uses message-level simulated timestamps.
- `conversation_timeline.txt` is now pure dialogue transcript without embedded behavior labels.
- New `behavior_timeline.txt` and `behavior_events.jsonl` are written alongside existing JSON outputs.
- Behavior events now carry `source_basis` and `visibility`.
- Project/session/message timeline fields were added: `project_anchor_time`, `session_start_time`, `session_end_time`, `message_timestamp`.

Current risk:

- The new between-session behavior synthesis is heuristic and intentionally conservative. It should be reviewed with small real runs before large batch generation.

Next:

- Run a real small `timeline_v2` generation and inspect whether the split transcript/behavior outputs look natural across multiple sessions.

这个文件只保留当前有效状态，方便几天后回来时快速接上开发。详细时间线看 `dev_journal.md`，完整背景看 `project_context.md`。

## 当前目标

当前主目标是继续把 `timeline_v2` 打磨成可稳定产出“自然学生团队对话”的版本，同时保留 `legacy` 版本作为基线对照。

更具体地说，当前优先级是：

- 提升多成员真实参与感
- 让 session 更自然地结束，而不是机械停下
- 让同一项目的多次会议之间承接更顺
- 让文本化事件流更像学生真实操作痕迹
- 保持文档和代码同步维护

## 当前阶段

当前处于：

`双轨架构已落地，timeline_v2 已经可用简易 API 完整运行，正在做生成质量和效率迭代。`

阶段特征：

- `legacy` 路线已恢复并保留
- `timeline_v2` 路线已可 dry-run、真实运行和完整 5-session project 生成
- 输出结构已升级到项目级时间线
- 当前主要不是“能不能跑”，而是“跑出来是否足够自然”

## 已完成

- 固定 AutoGen 0.2 运行线
- 已从 OpenRouter 单模型配置切换为简易 API 双模型配置模板
- 简易 API 双模型真实调用通过
- `timeline_positive_4` 完整 5-session 运行通过
- `timeline_v2` 已新增 `conversation_timeline.txt`，用于人工直观查看每次对话和学生操作
- `conversation_timeline.txt` 已升级为 session 级增量写入，异常中断时也能保留已完成 session 的直观转写
- 新增 `quality_report.md` 和 `quality_report.json`，用于生成质量诊断
- 新增 `timeline_smoke_test` 分组和 `--smoke-test` / `--estimate-cost` 运行入口
- 新增 `configs/experiment_groups_persona_composition.json`，用于 12 组 persona 组合对话生成实验
- 扩展 `scenarios_timeline.json`，当前已有 9 个教育场景
- 事件抽取规则已扩展，并在事件中加入 artifact 元数据
- 保留 `legacy` 单段群聊生成器
- 新增 `timeline_v2` 独立代码目录和入口
- 新增 `configs/scenarios_timeline.json`
- 新增 `configs/experiment_groups_timeline.json`
- 实现 `project_id -> session_id` 的项目级输出结构
- 实现项目状态承接 `project_state_history`
- 实现文本化操作事件 `events` + `event_refs`
- 实现成员出勤波动与会后补一句
- 实现隐藏式自然收束控制，不把结束 token 暴露到最终文本
- 实现 `project_checkpoints.jsonl` 与 session 级增量快照
- 修复 `TaskHost` 污染保存对话的问题
- 修复 timeline controller 调用下的 AutoGen cache 兼容问题
- 建立并持续维护项目记录体系

## 进行中

- 优化 `timeline_v2` 的多说话人参与度
- 优化一条消息里模拟多人发言的异常格式
- 优化 session 收尾自然性
- 继续用 `quality_report.md` 观察项目终局判断是否仍偏保守
- 继续优化事件触发覆盖率，尤其是“真实做了事但没显式说关键词”的情况
- 更新 `docs/`，使其准确反映双轨架构、timeline_v2 当前状态和新增直观输出文件

## 下一步准备完成

- 运行 `--smoke-test` 做一轮短程真实验证
- 选择 3 个代表性 persona 组合做小批量真实生成验证
- 增加简易 API 模型价格字段或降低 AutoGen 成本统计警告噪音
- 观察新增终局判断逻辑是否能把高压多进展项目判为 `forced_submission`
- 评估是否需要真正接入 LLM 事件 controller
- 设计完整断点续跑 `--resume-run-dir`
- 视结果决定是否进一步加强 closer/controller 的约束

## 当前关注的风险

- `timeline_v2` 比 `legacy` 更耗时、更耗 token
- `auto` speaker selection 每轮会额外选择说话人，是当前长时间运行的重要原因之一
- 新增的 `urgency_queue` 还需要通过 API smoke test 检查自然性和稳定性
- 模型偶尔会输出“一个 agent 替多人说话”的伪对话格式
- controller 返回 JSON 仍有解析失败风险，只是现在有 fallback
- 事件抽取仍是启发式规则，可能漏检
- 简易 API 模型虽然能完整运行，但一次 5-session project 仍可能需要十几分钟
- 当前 `--estimate-cost` 只是运行规模估算，不是精确 token/费用估算
- persona 组合完整运行规模较大，目前估算为 12 个 project、36-57 个 session，需要先小批量验证质量和成本

## 未来可增加的模块

- LLM 事件 controller
- 更精确的 token 和费用估算
- 项目级自动摘要报告
- 断点续跑能力
- 可切换的 session 自然性策略
- `urgency_queue` 参数对照实验，包括不同 `interrupt_threshold` 和 `silence_threshold`
- 数据质量筛查和去噪脚本

## 当前未解决问题

- 怎样定义“足够自然”的 session，并形成可重复检查标准
- 怎样让更多成员参与，同时又不让讨论显得被强推
- 怎样让状态推进更真实，不只是停在浅层 brainstorming
- 怎样让事件流既有覆盖率又不过度凭空生成
- 怎样评估 `urgency_queue` 相比 `auto` 是否真正降低调用成本并提升自然性

## 当前新增研发分支：自发发言机制

- 新增策略：`speaker_selection_method="urgency_queue"`
- 新增配置：`configs/experiment_groups_persona_composition_urgency.json`
- 作用范围：只作用于 `timeline_v2`，不影响 legacy
- 设计目标：减少 AutoGen `auto` 选人带来的额外模型调用，同时模拟学生自发发言、插话、抢话、沉默和自然停止
- 当前状态：代码已接入，并完成静态验证、配置验证、非 API 行为验证和 3 组代表性 API 验证
- 最新 API 输出：`outputs/persona_composition_urgency_timeline_dataset_20260506_230420`
- 对比结果：相同 3 组、12 个 session 下，HTTP POST 从 285 次降到 156 次，运行时间从约 34.81 分钟降到约 20.95 分钟
- 当前待优化点：`silence_stop_used` 尚未在真实运行中触发，高失调组支配者发言占比偏高，后续可继续做参数对照

## 项目级完整收束模式

- 已把 urgency 配置改成 `5-8` 次 session、单 session `max_round=14`
- 已加入 `min_project_sessions_before_terminal=5`
- 已加入 `force_project_closure_on_final_session=true`
- 最后一次 session 会强制生成项目级结局，不再停留在“下次继续”的中途状态
- 已修正 `forced_submission` 不被后处理覆盖为 `completed` 的问题
- 最新单组实验输出目录：`outputs/persona_composition_urgency_timeline_dataset_20260506_234830`
- 该单组实验最后一场已出现明确收尾口径，但后续仍可继续丰富 `session_outcome` 的多样性，让完整项目线更像真实过程而不是统一模板化收束
## 2026-05-07 最新状态：persona 组合 urgency 批量生成已完成

当前 `timeline_v2 + urgency_queue` 的 persona 组合批量实验已经完成 12 / 12 个分组生成，并已统一汇总到：

```text
outputs/persona_composition_urgency_collection_20260507/
```

该目录是本轮“同一功能模块、同一 API 模型配置、不同 persona 分组”的统一结果入口。优先查看：

- `README.md`：说明 collection 中每个文件的作用。
- `group_overview.md`：每个分组对应的结果文件、session 数、项目结局和解释。
- `persona_difference_report.md`：不同 persona 组合的差异复查报告。
- `conversation_timeline_combined.txt`：全部分组的直观对话合并转写。
- `groups/<group_id>/conversation_timeline.txt`：单个分组的直观对话。

当前无缺失分组、无未完成分组。后续主要工作不是继续盲目生成，而是人工复查各分组对话差异，并决定是否需要针对高失调组额外生成“更容易不了了之/放弃”的对照样本。

## 2026-05-08 最新状态：timeline_v2 真实单组生成已验证

已使用真实 API 完成 1 组 `timeline_v2` 生成验证：

```text
group: timeline_positive_4
output: outputs/persona_project_timeline_dataset_20260508_185119/
```

本次运行确认了新的双轨输出已经落地：

- `conversation_timeline.txt`：带时间戳的纯对话转写，不再混入行为标签。
- `behavior_timeline.txt`：独立行为事件时间线，便于人工阅读。
- `behavior_events.jsonl`：独立结构化行为流，包含 `source_basis` 与 `visibility`。
- `final_dataset.json`：结构化程序接口继续保留，并已用 Python 成功解析。

本次真实样本摘要：

- group: `timeline_positive_4`
- project: `timeline_positive_4__project_01`
- generated sessions: `5`
- project outcome: `completed`
- total events: `24`

当前观察到的质量提示：

- 所有 `session_outcome` 仍为 `progress_made_and_pause`，结局类型多样性不足。
- 第 4 次对话存在相邻重复或近似重复发言。

当前重点已从“能否生成”转为“生成结果是否足够自然、稳定、便于后续评估消费”。
