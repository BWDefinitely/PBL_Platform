#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "assessment-api" ]; then
  echo "[ERROR] 请在项目根目录执行本脚本（同级应有 assessment-api/ 和 pbl-platform/）"
  exit 1
fi

PACK_DIR="${1:-$(pwd)/share_package/pbl_platform_data_pack_20260430}"
RUN_ID="${2:-test2x8_v4_$(date +%Y%m%d_%H%M%S)}"

if [ ! -d "$PACK_DIR" ]; then
  echo "[ERROR] 数据包目录不存在: $PACK_DIR"
  echo "用法: bash import_data.sh /绝对路径/pbl_platform_data_pack_20260430 [run_id]"
  exit 1
fi

DATASET_DIR="$PACK_DIR/process_dataset"
ASSESSMENT_JSON="$PACK_DIR/assessment_results/assessment_results.json"
REPORT_DIR="$PACK_DIR/report_artifacts"

if [ ! -f "$DATASET_DIR/messages.csv" ] || [ ! -f "$ASSESSMENT_JSON" ]; then
  echo "[ERROR] 数据包不完整，缺少 process_dataset/messages.csv 或 assessment_results/assessment_results.json"
  exit 1
fi

cd assessment-api

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -r requirements.txt
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

alembic upgrade head

python3 -m src.jobs.import_process_data --dataset-dir "$DATASET_DIR"
python3 -m src.jobs.import_assessment_results \
  --run-id "$RUN_ID" \
  --assessment-json "$ASSESSMENT_JSON" \
  --report-dir "$REPORT_DIR"

echo "[OK] 数据导入完成，run_id=$RUN_ID"
echo "接下来可运行: uvicorn src.main:app --reload --host 0.0.0.0 --port 8100"
