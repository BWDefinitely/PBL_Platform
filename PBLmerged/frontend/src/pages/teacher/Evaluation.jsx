import { useEffect, useMemo, useState } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useAuth } from '../../context/AuthContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { getStudentMilestoneDetail, getStudentMilestones, getStudents } from '../../shared/api/assessment';

const DIMENSION_LABELS = {
  CT: '批判性思维',
  CR: '创新性推理',
  CM: '协作建构',
  CL: '沟通领导',
};
const DIMENSION_ORDER = ['CT', 'CR', 'CM', 'CL'];
const EVIDENCE_SOURCE_META = {
  doc_diffs: { icon: '📄', label: '文档贡献' },
  transcripts: { icon: '💬', label: '讨论参与' },
  collab_trace: { icon: '💡', label: '协作证据' },
};
const TIER_LABELS = {
  Beginning: '起步',
  Developing: '发展中',
  Proficient: '熟练',
  Exemplary: '卓越',
};

function formatDimension(code) {
  return `${DIMENSION_LABELS[code] || code} (${code})`;
}

function normalizeTier(tier) {
  if (!tier) return 'Developing';
  if (tier === 'Standard') return 'Proficient';
  if (tier === 'Advanced') return 'Exemplary';
  return ['Beginning', 'Developing', 'Proficient', 'Exemplary'].includes(tier) ? tier : 'Developing';
}

function normalizeEvidenceText(text) {
  if (!text) return '';
  return String(text)
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export default function Evaluation() {
  const { token } = useAuth();
  const [students, setStudents] = useState([]);
  const [viewMode, setViewMode] = useState('single');
  const [tierFilter, setTierFilter] = useState('all');
  const [scoreBandFilter, setScoreBandFilter] = useState('all');
  const [selectedStudent, setSelectedStudent] = useState('');
  const [detail, setDetail] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const getScoreColor = (score) => {
    if (score >= 80) return 'var(--secondary)';
    if (score >= 60) return 'var(--warning)';
    return 'var(--danger)';
  };

  useEffect(() => {
    const load = async () => {
      try {
        const items = await getStudents(token);
        setStudents(items);
        if (items.length) setSelectedStudent(items[0].student_id);
      } catch (e) {
        setError(e.message || '加载学生数据失败');
      }
    };
    load();
  }, [token]);

  useEffect(() => {
    const loadDetail = async () => {
      if (viewMode !== 'single' || !selectedStudent) return;
      setLoading(true);
      setError('');
      try {
        const picked = students.find((s) => s.student_id === selectedStudent);
        const milestone = picked?.latest_milestone || 'M3';
        const [data, ms] = await Promise.all([
          getStudentMilestoneDetail(token, selectedStudent, milestone),
          getStudentMilestones(token, selectedStudent),
        ]);
        setDetail(data);
        setMilestones(ms || []);
      } catch (e) {
        setError(e.message || '加载测评详情失败');
      } finally {
        setLoading(false);
      }
    };
    loadDetail();
  }, [selectedStudent, students, token, viewMode]);

  const radarData = useMemo(() => {
    if (!detail) return [];
    return DIMENSION_ORDER.map((d) => ({
      dimension: formatDimension(d),
      score: detail.domain_scores?.[d]?.normalized || 0,
      fullMark: 100,
    }));
  }, [detail]);

  const milestoneTrendData = useMemo(() => {
    const order = { M1: 1, M2: 2, M3: 3 };
    return [...milestones]
      .sort((a, b) => (order[a.milestone] || 0) - (order[b.milestone] || 0))
      .map((m) => ({
        milestone: m.milestone,
        composite: Math.round(m.composite_score || 0),
      }));
  }, [milestones]);

  const riskExplanation = useMemo(() => {
    if (!detail) return [];
    const reasons = [];
    const score = detail.composite_score || 0;
    const lowDomains = DIMENSION_ORDER
      .map((d) => ({ code: d, score: detail.domain_scores?.[d]?.normalized || 0 }))
      .filter((x) => x.score < 60)
      .sort((a, b) => a.score - b.score);
    if (score < 62.5) {
      reasons.push(`综合分低于风险阈值（当前 ${Math.round(score)}，阈值 62.5）`);
    }
    if (detail.flags?.intervention_alert) {
      reasons.push('评估引擎触发 intervention_alert');
    }
    if (lowDomains.length > 0) {
      reasons.push(`低分维度：${lowDomains.map((x) => `${formatDimension(x.code)} ${Math.round(x.score)}`).join('、')}`);
    }
    return reasons;
  }, [detail]);

  const evidenceBreakdown = useMemo(() => {
    const list = detail?.evidence_snippets || [];
    const map = list.reduce((acc, cur) => {
      const key = cur.source || 'unknown';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(map).map(([source, count]) => {
      const meta = EVIDENCE_SOURCE_META[source] || EVIDENCE_SOURCE_META.collab_trace;
      return `${meta.label} ${count} 条`;
    });
  }, [detail]);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const normalizedTier = normalizeTier(s.latest_tier);
      const score = Number(s.latest_composite_score || 0);
      const passTier = tierFilter === 'all' ? true : normalizedTier === tierFilter;
      const passScore = (() => {
        if (scoreBandFilter === 'all') return true;
        if (scoreBandFilter === 'lt60') return score < 60;
        if (scoreBandFilter === '60_70') return score >= 60 && score < 70;
        if (scoreBandFilter === '70_85') return score >= 70 && score < 85;
        if (scoreBandFilter === 'gte85') return score >= 85;
        return true;
      })();
      return passTier && passScore;
    });
  }, [students, tierFilter, scoreBandFilter]);

  const overallStats = useMemo(() => {
    if (!filteredStudents.length) {
      return { avg: 0, riskCount: 0, highest: null, lowest: null };
    }
    const sorted = [...filteredStudents].sort((a, b) => a.latest_composite_score - b.latest_composite_score);
    const avg = Math.round(filteredStudents.reduce((acc, cur) => acc + cur.latest_composite_score, 0) / filteredStudents.length);
    const riskCount = filteredStudents.filter((s) => s.intervention_alert || s.latest_composite_score < 62.5).length;
    return {
      avg,
      riskCount,
      lowest: sorted[0],
      highest: sorted[sorted.length - 1],
    };
  }, [filteredStudents]);

  useEffect(() => {
    if (!filteredStudents.length) {
      setSelectedStudent('');
      setDetail(null);
      return;
    }
    const stillExists = filteredStudents.some((s) => s.student_id === selectedStudent);
    if (!stillExists) {
      setSelectedStudent(filteredStudents[0].student_id);
    }
  }, [filteredStudents, selectedStudent]);

  const dimensionHighlights = useMemo(() => {
    if (!detail) return { strongest: [], weakest: [] };
    const scores = DIMENSION_ORDER.map((d) => ({
      code: d,
      label: formatDimension(d),
      score: detail.domain_scores?.[d]?.normalized || 0,
    }));
    return {
      strongest: [...scores].sort((a, b) => b.score - a.score).slice(0, 2),
      weakest: [...scores].sort((a, b) => a.score - b.score).slice(0, 2),
    };
  }, [detail]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📈 AI过程评估</div>
        <div className="page-subtitle">基于项目过程数据的结构化评估结果</div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">🔎 查看方式</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 2fr', gap: 12, alignItems: 'end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">视图</label>
            <select className="form-select" value={viewMode} onChange={(e) => setViewMode(e.target.value)}>
              <option value="single">单个学生</option>
              <option value="overall">全体学生总览</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">阶段筛选</label>
            <select className="form-select" value={tierFilter} onChange={(e) => setTierFilter(e.target.value)}>
              <option value="all">全部阶段</option>
              <option value="Beginning">{TIER_LABELS.Beginning}</option>
              <option value="Developing">{TIER_LABELS.Developing}</option>
              <option value="Proficient">{TIER_LABELS.Proficient}</option>
              <option value="Exemplary">{TIER_LABELS.Exemplary}</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">分数段筛选</label>
            <select className="form-select" value={scoreBandFilter} onChange={(e) => setScoreBandFilter(e.target.value)}>
              <option value="all">全部分数段</option>
              <option value="lt60">60 分以下</option>
              <option value="60_70">60-69 分</option>
              <option value="70_85">70-84 分</option>
              <option value="gte85">85 分及以上</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">学生筛选</label>
            <select
              className="form-select"
              value={selectedStudent}
              onChange={(e) => setSelectedStudent(e.target.value)}
              disabled={viewMode !== 'single' || filteredStudents.length === 0}
            >
              {filteredStudents.map((m) => (
                <option key={m.student_id} value={m.student_id}>
                  {m.student_id} ｜ {m.latest_milestone} ｜ {TIER_LABELS[normalizeTier(m.latest_tier)]} ｜ {Math.round(m.latest_composite_score)}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
          当前筛选命中 {filteredStudents.length} / {students.length} 名学生
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">{viewMode === 'single' ? '🏆 学生最新评分' : '🏫 班级总体评分'}</div>
          </div>
          <div className="score-display" style={{ color: getScoreColor(detail?.composite_score || 0), marginBottom: 20 }}>
            {viewMode === 'single'
              ? Math.round(detail?.composite_score || 0)
              : overallStats.avg}
            <span style={{ fontSize: 16, color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center' }}>
            {viewMode === 'single'
              ? `当前里程碑：${detail?.milestone || '-'} ｜ 等级：${detail?.student_tier || '-'}`
              : `筛选后学生数：${filteredStudents.length} ｜ 需关注：${overallStats.riskCount}`}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">{viewMode === 'single' ? '👤 当前学生信息' : '📌 总览摘要'}</div>
          </div>
          {viewMode === 'single' ? (
            (() => {
              const current = filteredStudents.find((m) => m.student_id === selectedStudent);
              if (!current) return <div className="empty-state">暂无学生数据</div>;
              return (
                <div className="member-item" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                  <span className="member-avatar">👨‍🎓</span>
                  <div className="member-info">
                    <div className="member-name">{current.student_id}</div>
                    <div className="member-detail">里程碑 {current.latest_milestone} ｜ {TIER_LABELS[normalizeTier(current.latest_tier)]}</div>
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: getScoreColor(current.latest_composite_score) }}>
                    {Math.round(current.latest_composite_score)}
                  </div>
                </div>
              );
            })()
          ) : (
            <div style={{ display: 'grid', gap: 10 }}>
              <div className="member-item" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                <span className="member-avatar">🥇</span>
                <div className="member-info">
                  <div className="member-name">最高分</div>
                  <div className="member-detail">{overallStats.highest?.student_id || '-'}</div>
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--secondary)' }}>
                  {Math.round(overallStats.highest?.latest_composite_score || 0)}
                </div>
              </div>
              <div className="member-item" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                <span className="member-avatar">🧭</span>
                <div className="member-info">
                  <div className="member-name">最低分</div>
                  <div className="member-detail">{overallStats.lowest?.student_id || '-'}</div>
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--danger)' }}>
                  {Math.round(overallStats.lowest?.latest_composite_score || 0)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'single' && detail && (
        <div className="fade-in">
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <div className="card-title">📉 里程碑趋势与风险解释</div>
            </div>
            <div className="grid-2">
              <div>
                {milestoneTrendData.length === 0 ? (
                  <div className="empty-state">暂无里程碑趋势数据</div>
                ) : (
                  <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={milestoneTrendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="milestone" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip formatter={(value) => [`${value}`, '综合分']} />
                      <Line type="monotone" dataKey="composite" stroke="#4F46E5" strokeWidth={3} dot={{ r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
              <div style={{ display: 'grid', gap: 10 }}>
                <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: '#FEF2F2' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#B91C1C', marginBottom: 4 }}>触发原因</div>
                  <div style={{ fontSize: 13, color: '#7F1D1D', lineHeight: 1.65 }}>
                    {riskExplanation.length ? riskExplanation.join('；') : '当前未命中明确风险触发条件。'}
                  </div>
                </div>
                <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: '#EFF6FF' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#1D4ED8', marginBottom: 4 }}>证据构成</div>
                  <div style={{ fontSize: 13, color: '#1E40AF' }}>
                    {evidenceBreakdown.length ? evidenceBreakdown.join('、') : '暂无证据记录'}
                  </div>
                </div>
                <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: '#ECFDF5' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#047857', marginBottom: 4 }}>建议动作</div>
                  <div style={{ fontSize: 13, color: '#065F46', lineHeight: 1.65 }}>
                    {riskExplanation.length
                      ? '建议本周安排 1v1 反馈，并在下一里程碑前跟踪最低维度的过程证据增量。'
                      : '维持当前节奏，建议在下一里程碑继续强化优势维度并补齐薄弱证据类型。'}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="grid-2" style={{ marginBottom: 20 }}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  👨‍🎓 {detail.student_id} - 能力雷达图
                </div>
              </div>
              <div className="radar-container">
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#E2E8F0" />
                    <PolarAngleAxis dataKey="dimension" style={{ fontSize: 12 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} style={{ fontSize: 10 }} />
                    <Radar name={detail.student_id} dataKey="score" stroke="#4F46E5" fill="#4F46E5" fillOpacity={0.25} strokeWidth={2} />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div className="card-title">📊 各维度得分</div>
              </div>
              {DIMENSION_ORDER.map((d) => (
                <div className="score-bar" key={d}>
                  <span className="score-bar-label" style={{ width: 150 }}>{formatDimension(d)}</span>
                  <div className="score-bar-track">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${detail.domain_scores?.[d]?.normalized || 0}%`,
                        backgroundColor: getScoreColor(detail.domain_scores?.[d]?.normalized || 0),
                      }}
                    />
                  </div>
                  <span className="score-bar-value" style={{ color: getScoreColor(detail.domain_scores?.[d]?.normalized || 0) }}>
                    {Math.round(detail.domain_scores?.[d]?.normalized || 0)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid-2" style={{ marginBottom: 20 }}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">📋 贡献记录</div>
              </div>
              <div style={{ display: 'grid', gap: 10 }}>
                {(detail.evidence_snippets || []).map((c, i) => {
                  const meta = EVIDENCE_SOURCE_META[c.source] || EVIDENCE_SOURCE_META.collab_trace;
                  const cleanText = normalizeEvidenceText(c.text);
                  return (
                    <div
                      key={`${c.source}-${i}`}
                      style={{
                        border: '1px solid var(--border)',
                        background: 'var(--bg)',
                        borderRadius: 'var(--radius-sm)',
                        padding: 10,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                        <span>{meta.icon}</span>
                        <strong style={{ color: 'var(--text)', fontSize: 13 }}>{meta.label}</strong>
                      </div>
                      <div
                        style={{
                          fontSize: 13,
                          color: 'var(--text-secondary)',
                          lineHeight: 1.65,
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {cleanText || '暂无文本内容'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div className="card-title">💡 AI分析</div>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                {detail.narrative_summary || '暂无 AI 叙事总结。'}
              </div>
              <div style={{ marginTop: 14, display: 'grid', gap: 8 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  intervention_alert: {detail.flags?.intervention_alert ? '是' : '否'} ｜ equity_flag: {detail.flags?.equity_flag ? '是' : '否'}
                </div>
                <div style={{ padding: 10, borderRadius: 'var(--radius-sm)', background: '#ECFDF5', border: '1px solid #A7F3D0' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#065F46', marginBottom: 4 }}>优势维度</div>
                  <div style={{ fontSize: 13, color: '#065F46' }}>
                    {dimensionHighlights.strongest.map((s) => `${s.label}（${Math.round(s.score)}）`).join('、') || '-'}
                  </div>
                </div>
                <div style={{ padding: 10, borderRadius: 'var(--radius-sm)', background: '#FFFBEB', border: '1px solid #FDE68A' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#92400E', marginBottom: 4 }}>优先改进</div>
                  <div style={{ fontSize: 13, color: '#92400E' }}>
                    {dimensionHighlights.weakest.map((s) => `${s.label}（${Math.round(s.score)}）`).join('、') || '-'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {viewMode === 'overall' && (
        <div className="card fade-in" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <div className="card-title">👥 全体学生总览</div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>学生</th>
                  <th>里程碑</th>
                  <th>等级</th>
                  <th>综合分</th>
                  <th>风险</th>
                </tr>
              </thead>
              <tbody>
                {[...filteredStudents]
                  .sort((a, b) => b.latest_composite_score - a.latest_composite_score)
                  .map((s) => (
                    <tr key={s.student_id}>
                      <td>{s.student_id}</td>
                      <td>{s.latest_milestone}</td>
                      <td>{TIER_LABELS[normalizeTier(s.latest_tier)]}</td>
                      <td style={{ fontWeight: 700, color: getScoreColor(s.latest_composite_score) }}>
                        {Math.round(s.latest_composite_score)}
                      </td>
                      <td>{s.intervention_alert || s.latest_composite_score < 62.5 ? '是' : '否'}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {loading && <div className="card">加载中...</div>}
      {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
    </div>
  );
}
