#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

RUN_ID="${1:-v9_full64_$(date +%Y%m%d_%H%M%S)}"
DATASET_DIR="${2:-/Users/meiling/Desktop/red bird/synthetic_data_outputs/data/synthetic_v9_llm_profile_perfect_full64}"
ASSESSMENT_JSON="${3:-/Users/meiling/Desktop/red bird/pbl_assessment/test_full64/report_v9_full64/assessment_results_dedup.json}"
EVIDENCE_DIR="${4:-/Users/meiling/Desktop/red bird/pbl_assessment/data/full8x8_v9_enriched/negotiatedkt_raw}"
REPORT_DIR="${5:-/Users/meiling/Desktop/red bird/pbl_assessment/test_full64/report_v9_full64}"

echo "[1/3] Import process CSVs..."
python3 -m src.jobs.import_process_data --dataset-dir "$DATASET_DIR"

echo "[2/3] Import assessment results..."
python3 -m src.jobs.import_assessment_results \
  --run-id "$RUN_ID" \
  --assessment-json "$ASSESSMENT_JSON" \
  --evidence-dir "$EVIDENCE_DIR" \
  --report-dir "$REPORT_DIR"

echo "[3/3] Done."
echo "run_id=$RUN_ID"
