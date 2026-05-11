# 生成质量诊断报告

本报告只用于调试对话生成质量，不是学生表现评估标签。

- 数据集：persona_project_timeline_benchmark_v2
- 运行状态：completed
- 项目数：1
- session 数：2
- 事件数：0
- 警告数：2

## 主要警告

- 所有 session_outcome 完全相同，结局类型多样性不足。
- 事件数量偏低，可能漏掉了学生操作。

## 项目明细

### timeline_smoke_test__project_01

- 项目结局：completed
- session 数：2
- 事件数：0
- artifact 数：0
- session_outcome 分布：{'progress_made_and_pause': 2}

- 第 1 次：messages=12, speakers={'Mia': 4, 'Leo': 5, 'Ivy': 2, 'Max': 1}, dominance=0.417, events=0, policy=auto, interruptions=[], silence_stop=False
- 第 2 次：messages=12, speakers={'Mia': 3, 'Leo': 5, 'Ivy': 2, 'Max': 2}, dominance=0.417, events=0, policy=auto, interruptions=[], silence_stop=False
