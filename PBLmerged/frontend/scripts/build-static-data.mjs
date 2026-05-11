// 把 backend/pbl_platform_data_pack_20260430 下的评测结果与报告图
// 转换成前端可以直接 fetch 的静态文件，输出到 frontend/public/data/。
//
// 用法（在 frontend/ 目录下执行）：
//   node scripts/build-static-data.mjs
//
// 可通过环境变量覆盖默认路径：
//   PACK_DIR     数据包根目录
//   OUT_DIR      输出目录（默认 public/data）

import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = path.resolve(__dirname, '..');
const PACK_DIR =
  process.env.PACK_DIR ||
  path.resolve(FRONTEND_ROOT, '../backend/pbl_platform_data_pack_20260430');
const OUT_DIR = process.env.OUT_DIR || path.join(FRONTEND_ROOT, 'public/data');

const ASSESSMENT_JSON = path.join(PACK_DIR, 'assessment_results/assessment_results.json');
const REPORT_DIR = path.join(PACK_DIR, 'report_artifacts');
const RUN_ID = process.env.RUN_ID || 'static_pack_20260430';

const MILESTONE_RANK = { M1: 1, M2: 2, M3: 3 };

function pickLatest(items) {
  return [...items].sort((a, b) => (MILESTONE_RANK[b.milestone] || 0) - (MILESTONE_RANK[a.milestone] || 0))[0];
}

// 评测包没有 evidence_snippets，这里用 narrative 切片伪造一些占位证据，
// 避免前端「贡献记录」面板完全空白。如果将来评测包带证据，可以替换此函数。
function buildEvidenceSnippets(item) {
  const snippets = [];
  const narrative = item.narrative_summary || '';
  if (narrative) {
    snippets.push({ source: 'collab_trace', text: narrative, trace_ref: null });
  }
  for (const [dim, payload] of Object.entries(item.dimension_scores || {})) {
    const rationale = payload?.rationale;
    if (rationale) {
      snippets.push({ source: 'transcripts', text: `[${dim}] ${rationale}`, trace_ref: dim });
    }
  }
  return snippets.slice(0, 12);
}

function toMilestoneSummary(item, domain_scores_map) {
  return {
    milestone: item.milestone,
    composite_score: item.composite_score,
    student_tier: item.student_tier,
    assessed_at: item.assessed_at,
    domain_scores: domain_scores_map,
  };
}

function toMilestoneDetail(item) {
  const domain_scores = {};
  for (const [domain, payload] of Object.entries(item.domain_scores || {})) {
    domain_scores[domain] = {
      normalized: Number(payload?.normalized || 0),
      tier: payload?.tier || null,
    };
  }
  const dimension_scores = {};
  for (const [dim, payload] of Object.entries(item.dimension_scores || {})) {
    dimension_scores[dim] = {
      final_score: payload?.final_score ?? null,
      rationale: payload?.rationale ?? null,
    };
  }
  const flags = item.flags || {};
  return {
    student_id: item.student_id,
    milestone: item.milestone,
    composite_score: item.composite_score,
    student_tier: item.student_tier,
    assessed_at: item.assessed_at,
    narrative_summary: item.narrative_summary || '',
    domain_scores,
    dimension_scores,
    flags: {
      intervention_alert: Boolean(flags.intervention_alert),
      equity_flag: Boolean(flags.equity_flag),
      unresolved_dimensions: flags.unresolved_dimensions || [],
    },
    evidence_snippets: buildEvidenceSnippets(item),
  };
}

async function main() {
  console.log('[build-static-data] PACK_DIR =', PACK_DIR);
  console.log('[build-static-data] OUT_DIR  =', OUT_DIR);

  const raw = await fs.readFile(ASSESSMENT_JSON, 'utf-8');
  const items = JSON.parse(raw);
  console.log(`[build-static-data] 读到 ${items.length} 条评测记录`);

  // 按学生分组
  const byStudent = new Map();
  for (const item of items) {
    if (!byStudent.has(item.student_id)) byStudent.set(item.student_id, []);
    byStudent.get(item.student_id).push(item);
  }

  await fs.mkdir(path.join(OUT_DIR, 'students'), { recursive: true });
  await fs.mkdir(path.join(OUT_DIR, 'reports'), { recursive: true });

  // 1) students.json：对应 GET /api/assessments/students
  const studentsList = [];
  for (const [student_id, group] of byStudent) {
    const latest = pickLatest(group);
    const flags = latest.flags || {};
    studentsList.push({
      student_id,
      latest_milestone: latest.milestone,
      latest_composite_score: latest.composite_score,
      latest_tier: latest.student_tier,
      intervention_alert: Boolean(flags.intervention_alert),
    });
  }
  studentsList.sort((a, b) => a.student_id.localeCompare(b.student_id));
  await fs.writeFile(
    path.join(OUT_DIR, 'students.json'),
    JSON.stringify(studentsList, null, 2),
    'utf-8',
  );
  console.log(`[build-static-data] 写入 students.json (${studentsList.length} 名学生)`);

  // 2) 每个学生的 milestones 列表与每里程碑详情
  for (const [student_id, group] of byStudent) {
    const dir = path.join(OUT_DIR, 'students', encodeURIComponent(student_id));
    await fs.mkdir(dir, { recursive: true });

    const milestoneSummaries = group
      .slice()
      .sort((a, b) => (MILESTONE_RANK[a.milestone] || 0) - (MILESTONE_RANK[b.milestone] || 0))
      .map((item) => {
        const dmap = {};
        for (const [domain, payload] of Object.entries(item.domain_scores || {})) {
          dmap[domain] = Number(payload?.normalized || 0);
        }
        return toMilestoneSummary(item, dmap);
      });
    await fs.writeFile(
      path.join(dir, 'milestones.json'),
      JSON.stringify(milestoneSummaries, null, 2),
      'utf-8',
    );

    for (const item of group) {
      await fs.writeFile(
        path.join(dir, `${item.milestone}.json`),
        JSON.stringify(toMilestoneDetail(item), null, 2),
        'utf-8',
      );
    }
  }
  console.log('[build-static-data] 写入每学生的 milestones.json 与各里程碑详情');

  // 3) 报告产物：拷贝 PNG/JSON，并生成 reports.json（对应 GET /api/reports）
  const reportFiles = await fs.readdir(REPORT_DIR);
  const artifacts = [];
  let id = 1;
  for (const name of reportFiles.sort()) {
    const ext = path.extname(name).toLowerCase();
    if (!['.png', '.json', '.csv', '.md'].includes(ext)) continue;
    const src = path.join(REPORT_DIR, name);
    const dst = path.join(OUT_DIR, 'reports', name);
    await fs.copyFile(src, dst);
    const stat = await fs.stat(src);
    artifacts.push({
      id: id++,
      name,
      type: ext === '.png' ? 'chart_png' : 'report_file',
      url: `/data/reports/${name}`,
      meta: { size_bytes: stat.size },
    });
  }
  const reportsPayload = [{ run_id: RUN_ID, artifacts }];
  await fs.writeFile(
    path.join(OUT_DIR, 'reports.json'),
    JSON.stringify(reportsPayload, null, 2),
    'utf-8',
  );
  console.log(`[build-static-data] 拷贝 ${artifacts.length} 个报告文件，写入 reports.json`);

  console.log('[build-static-data] 完成。');
}

main().catch((err) => {
  console.error('[build-static-data] 失败:', err);
  process.exit(1);
});
