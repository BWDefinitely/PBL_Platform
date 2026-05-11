# PBL Platform 数据导入说明（给同事）

这个数据包对应：
- 过程数据：`synthetic_v9_llm_profile_perfect_full64`
- 评估结果：`test2x8 raw_results_v4_cl4_fix/assessment_results.json`
- 报告图表：`report_v4/*.png`

## 1. 克隆代码仓库

```bash
git clone git@github.com:ssrzero123/pbl--platform.git
cd pbl--platform
```

## 2. 放置数据包

把本数据包目录 `pbl_platform_data_pack_20260430` 放到项目根目录下，结构应如下：

```text
pbl--platform/
  assessment-api/
  pbl-platform/
  share_package/
    pbl_platform_data_pack_20260430/
      process_dataset/
      assessment_results/
      report_artifacts/
      import_data.sh
      DATA_SETUP.md
```

## 3. 一键导入（推荐）

在项目根目录执行：

```bash
bash share_package/pbl_platform_data_pack_20260430/import_data.sh \
  "$(pwd)/share_package/pbl_platform_data_pack_20260430" \
  "team_init_20260430"
```

执行完成后会自动：
- 创建并激活 `assessment-api/.venv`
- 安装后端依赖
- 运行 `alembic upgrade head`
- 导入过程数据 CSV
- 导入评估 JSON 与报告图表

## 4. 启动服务

### 后端

```bash
cd assessment-api
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8100
```

### 前端

```bash
cd pbl-platform
npm install
cp .env.example .env
npm run dev
```

## 5. 手工导入命令（可选）

如果不想用一键脚本，也可以手动执行：

```bash
cd assessment-api
source .venv/bin/activate
alembic upgrade head

python3 -m src.jobs.import_process_data \
  --dataset-dir "../share_package/pbl_platform_data_pack_20260430/process_dataset"

python3 -m src.jobs.import_assessment_results \
  --run-id "team_init_20260430" \
  --assessment-json "../share_package/pbl_platform_data_pack_20260430/assessment_results/assessment_results.json" \
  --report-dir "../share_package/pbl_platform_data_pack_20260430/report_artifacts"
```

## 6. 数据内容清单

- `process_dataset/messages.csv`
- `process_dataset/content.csv`
- `process_dataset/presentations.csv`
- `process_dataset/events.csv`
- `assessment_results/assessment_results.json`
- `assessment_results/assessment_results_m3_all.json`
- `assessment_results/assessment_results.csv`
- `report_artifacts/*.png`
- `report_artifacts/error_metrics_summary.json`

## 7. 常见问题

- **Q: 报错找不到 Python 或 pip？**
  - A: 请安装 Python 3.10+，并确保 `python3` 可用。
- **Q: 前端看不到报告图？**
  - A: 确认后端已启动在 `8100`，并且导入时带了 `--report-dir`。
- **Q: 想重复导入？**
  - A: 可以重复执行导入命令，导入逻辑支持幂等更新。
