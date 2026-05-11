# 项目记录模板（Project Recording Template）

这个目录是一个可复用模板源（reusable template source），用于给新项目或已有项目建立统一的记录体系。

## 提供内容（What It Provides）

- 一个项目级 `AGENTS.md` 模板，用于约束记录行为
- 一套标准 `docs/` 模板
- 一个全局 Codex 记录规则模板 `global_codex_AGENTS.md.template`
- 一个可直接粘贴到 Codex settings 的规则模板 `codex_settings_prompt.template.md`
- 最新文档分工说明 `docs/file_roles.md.template`
- 完整项目上下文模板 `docs/project_context.md.template`

## 推荐用法（Recommended Use）

### 方式 A：直接复制模板目录内容

```powershell
Copy-Item -Recurse "旧项目路径\autogen\project_recording_template\*" "新项目路径\"
```

复制后，把 `.template` 文件重命名为正式文件。例如：

- `AGENTS.md.template` -> `AGENTS.md`
- `docs/project_context.md.template` -> `docs/project_context.md`
- `docs/file_roles.md.template` -> `docs/file_roles.md`
- `docs/architecture.md.template` -> `docs/architecture.md`

### 方式 B：用当前项目的初始化脚本

```powershell
python "旧项目路径\autogen\scripts\init_project_recording.py" --project-root "新项目路径" --project-name "my_project" --mode new --template-root "旧项目路径\autogen\project_recording_template"
```

已有项目补录历史时，可以再使用：

```powershell
python "旧项目路径\autogen\scripts\backfill_project_history.py" --project-root "新项目路径" --phase "Current Baseline" --goal "Describe the baseline." --summary "Describe what has already been done."
```

注意：当前 `project_recording_template/` 主要保存可复制模板；辅助脚本位于当前项目的 `scripts/` 目录。

## 新项目建议开场指令（Codex Prompt）

新开 Codex 对话时，可以直接发送：

```text
请先读取 AGENTS.md 和 docs/file_roles.md，按项目记录规范工作。
这是一个新项目，请检查 docs 记录骨架是否完整。
后续每次代码修改、功能调试、配置调整、运行验证，都要同步更新相关 docs。
```

## 全局与项目级规则分工

- `codex_settings_prompt.template.md`：放进 Codex settings，只写跨项目通用规则。
- `global_codex_AGENTS.md.template`：作为你的全局 `AGENTS.md` 参考模板。
- `AGENTS.md.template`：作为每个具体项目的项目级规则模板。

## 模板占位符（Placeholders）

模板文件中使用这些占位符：

- `__PROJECT_NAME__`
- `__PROJECT_SLUG__`
- `__DATE__`
