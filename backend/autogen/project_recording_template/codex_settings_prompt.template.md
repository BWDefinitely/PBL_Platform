# Codex Settings 全局规则模板

把下面这段直接放进 Codex settings 的全局指令中：

```text
- Every project must have a recording skeleton; if not, initialize it before substantial work.
- After each meaningful code/config/debug step, update the project docs that changed.
- Default doc split: README for entry, project_context for full background, project_status for current state, dev_journal for timeline, architecture for structure, config_guide for manual config, learning_notes for knowledge, decisions for long-lived choices, case_study only on request, file_roles for document maintenance rules.
- Do not write secrets, keys, or private paths into human-readable docs.
- Prefer adding teaching-oriented comments to non-obvious code.
```

建议：

- 这里只放跨项目通用规则。
- 不要把某个具体项目的目录名、脚本名、输出路径写进全局 settings。
- 项目专属规则继续写在项目级 `AGENTS.md` 里。
