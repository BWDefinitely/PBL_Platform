import { useEffect, useMemo, useState } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useAuth } from '../../context/AuthContext';
import { getStudentMilestoneDetail, getStudentMilestones, getStudents } from '../../shared/api/assessment';

const DIMENSION_LABELS = {
  CT: '批判性思维',
  CR: '创新性推理',
  CM: '协作建构',
  CL: '沟通领导',
};
const DIMENSION_ORDER = ['CT', 'CR', 'CM', 'CL'];
const TIER_LABELS = {
  Beginning: '起步',
  Developing: '发展中',
  Proficient: '熟练',
  Exemplary: '卓越',
};
const EVIDENCE_SOURCE_META = {
  doc_diffs: { icon: '📄', label: '文档贡献' },
  transcripts: { icon: '💬', label: '讨论参与' },
  collab_trace: { icon: '💡', label: '协作证据' },
};

function normalizeTier(tier) {
  if (!tier) return 'Developing';
  if (tier === 'Standard') return 'Proficient';
  if (tier === 'Advanced') return 'Exemplary';
  return ['Beginning', 'Developing', 'Proficient', 'Exemplary'].includes(tier) ? tier : 'Developing';
}

function normalizeText(text) {
  if (!text) return '';
  return String(text)
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--secondary)';
  if (score >= 60) return 'var(--warning)';
  return 'var(--danger)';
}

const PROFILE_BUTTONS = [
  { key: 'overview', icon: '🪞', title: '能力总览', desc: '当前里程碑综合分与能力雷达' },
  { key: 'dimensions', icon: '🧭', title: '维度详情', desc: '4 大领域 + 子维度逐项解读' },
  { key: 'growth', icon: '📈', title: '成长轨迹', desc: '历次里程碑综合分趋势' },
  { key: 'strength', icon: '💪', title: '优势与短板', desc: '最强 / 最弱维度与改进建议' },
  { key: 'narrative', icon: '🪄', title: 'AI 叙事画像', desc: '评估引擎对你的总体描述' },
  { key: 'evidence', icon: '🔍', title: '证据片段', desc: '画像背后的过程数据来源' },
  { key: 'flags', icon: '🚩', title: '风险与提醒', desc: '是否触发干预 / 公平性提示' },
];

export default function StudentProfile() {
  const { token } = useAuth();
  const [students, setStudents] = useState([]);
  const [me, setMe] = useState(null);
  const [detail, setDetail] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [openKey, setOpenKey] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const list = await getStudents(token);
        setStudents(list);
        const first = list[0];
        if (!first) return;
        setMe(first);
        const [d, ms] = await Promise.all([
          getStudentMilestoneDetail(token, first.student_id, first.latest_milestone),
          getStudentMilestones(token, first.student_id),
        ]);
        setDetail(d);
        setMilestones(ms || []);
      } catch (e) {
        setError(e.message || '加载用户画像失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const onSwitchStudent = async (studentId) => {
    const target = students.find((s) => s.student_id === studentId);
    if (!target) return;
    try {
      setLoading(true);
      setMe(target);
      const [d, ms] = await Promise.all([
        getStudentMilestoneDetail(token, target.student_id, target.latest_milestone),
        getStudentMilestones(token, target.student_id),
      ]);
      setDetail(d);
      setMilestones(ms || []);
    } catch (e) {
      setError(e.message || '加载用户画像失败');
    } finally {
      setLoading(false);
    }
  };

  const radarData = useMemo(() => {
    if (!detail) return [];
    return DIMENSION_ORDER.map((d) => ({
      dimension: `${DIMENSION_LABELS[d]} (${d})`,
      score: detail.domain_scores?.[d]?.normalized || 0,
      fullMark: 100,
    }));
  }, [detail]);

  const trendData = useMemo(() => {
    const order = { M1: 1, M2: 2, M3: 3 };
    return [...milestones]
      .sort((a, b) => (order[a.milestone] || 0) - (order[b.milestone] || 0))
      .map((m) => ({ milestone: m.milestone, composite: Math.round(m.composite_score || 0) }));
  }, [milestones]);

  const ranking = useMemo(() => {
    if (!detail) return { strongest: [], weakest: [] };
    const arr = DIMENSION_ORDER.map((d) => ({
      code: d,
      label: `${DIMENSION_LABELS[d]} (${d})`,
      score: detail.domain_scores?.[d]?.normalized || 0,
    }));
    return {
      strongest: [...arr].sort((a, b) => b.score - a.score).slice(0, 2),
      weakest: [...arr].sort((a, b) => a.score - b.score).slice(0, 2),
    };
  }, [detail]);

  const toggle = (key) => setOpenKey((cur) => (cur === key ? null : key));

  const renderDetail = (key) => {
    if (!detail) return <div className="empty-state">暂无数据</div>;

    if (key === 'overview') {
      return (
        <div className="grid-2">
          <div>
            <div className="score-display" style={{ color: getScoreColor(detail.composite_score || 0), marginBottom: 12 }}>
              {Math.round(detail.composite_score || 0)}
              <span style={{ fontSize: 16, color: 'var(--text-muted)' }}>/100</span>
            </div>
            <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-secondary)' }}>
              当前里程碑：{detail.milestone} ｜ 等级：{TIER_LABELS[normalizeTier(detail.student_tier)]}
            </div>
          </div>
          <div>
            <ResponsiveContainer width="100%" height={240}>
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
      );
    }

    if (key === 'dimensions') {
      const dimEntries = Object.entries(detail.dimension_scores || {});
      return (
        <div>
          {DIMENSION_ORDER.map((d) => (
            <div className="score-bar" key={d}>
              <span className="score-bar-label" style={{ width: 150 }}>{DIMENSION_LABELS[d]} ({d})</span>
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
          {dimEntries.length > 0 && (
            <div style={{ marginTop: 14, display: 'grid', gap: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>子维度细分</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                {dimEntries.map(([dim, payload]) => (
                  <div key={dim} style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--bg)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <strong style={{ fontSize: 13 }}>{dim}</strong>
                      <span style={{ fontSize: 13, fontWeight: 700, color: getScoreColor(Number(payload?.final_score) || 0) }}>
                        {payload?.final_score != null ? Math.round(Number(payload.final_score)) : '-'}
                      </span>
                    </div>
                    {payload?.rationale && (
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        {normalizeText(payload.rationale).slice(0, 80)}
                        {normalizeText(payload.rationale).length > 80 ? '…' : ''}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (key === 'growth') {
      if (trendData.length === 0) return <div className="empty-state">暂无里程碑趋势数据</div>;
      const first = trendData[0]?.composite || 0;
      const last = trendData[trendData.length - 1]?.composite || 0;
      const delta = last - first;
      return (
        <div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="milestone" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => [`${value}`, '综合分']} />
              <Line type="monotone" dataKey="composite" stroke="#4F46E5" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 10, fontSize: 13, color: 'var(--text-secondary)' }}>
            从 {trendData[0]?.milestone} ({first}) 到 {trendData[trendData.length - 1]?.milestone} ({last})，
            综合分变化 <strong style={{ color: delta >= 0 ? 'var(--secondary)' : 'var(--danger)' }}>{delta >= 0 ? '+' : ''}{delta}</strong>。
          </div>
        </div>
      );
    }

    if (key === 'strength') {
      return (
        <div className="grid-2">
          <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: '#ECFDF5', border: '1px solid #A7F3D0' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#065F46', marginBottom: 6 }}>✅ 你的优势</div>
            {ranking.strongest.map((s) => (
              <div key={s.code} style={{ fontSize: 13, color: '#065F46', marginBottom: 4 }}>
                💪 {s.label}（{Math.round(s.score)}）
              </div>
            ))}
          </div>
          <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: '#FFFBEB', border: '1px solid #FDE68A' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#92400E', marginBottom: 6 }}>📈 待提升</div>
            {ranking.weakest.map((w) => (
              <div key={w.code} style={{ fontSize: 13, color: '#92400E', marginBottom: 4 }}>
                ⚠️ {w.label}（{Math.round(w.score)}）
              </div>
            ))}
            <div style={{ marginTop: 8, fontSize: 12, color: '#92400E', lineHeight: 1.6 }}>
              建议：在下个里程碑围绕薄弱维度补充可验证的过程证据。
            </div>
          </div>
        </div>
      );
    }

    if (key === 'narrative') {
      return (
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          {detail.narrative_summary || '暂无 AI 叙事总结。'}
        </div>
      );
    }

    if (key === 'evidence') {
      const list = detail.evidence_snippets || [];
      if (list.length === 0) return <div className="empty-state">暂无证据片段</div>;
      return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
          {list.map((c, i) => {
            const meta = EVIDENCE_SOURCE_META[c.source] || EVIDENCE_SOURCE_META.collab_trace;
            const text = normalizeText(c.text);
            return (
              <div key={`${c.source}-${i}`} style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'var(--bg)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span>{meta.icon}</span>
                  <strong style={{ fontSize: 13 }}>{meta.label}</strong>
                  {c.trace_ref && (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'white', border: '1px solid var(--border)', borderRadius: 999, padding: '1px 8px' }}>
                      {c.trace_ref}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.65, display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {text || '暂无文本'}
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    if (key === 'flags') {
      const f = detail.flags || {};
      const items = [
        { label: '干预提醒 (intervention_alert)', value: f.intervention_alert, danger: true },
        { label: '公平性提示 (equity_flag)', value: f.equity_flag, danger: false },
      ];
      return (
        <div style={{ display: 'grid', gap: 10 }}>
          {items.map((it) => (
            <div
              key={it.label}
              style={{
                padding: 12,
                borderRadius: 'var(--radius-sm)',
                background: it.value ? (it.danger ? '#FEF2F2' : '#FFFBEB') : '#F0FDF4',
                border: `1px solid ${it.value ? (it.danger ? '#FECACA' : '#FDE68A') : '#BBF7D0'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{ fontSize: 13, color: 'var(--text)' }}>{it.label}</span>
              <strong style={{ fontSize: 13, color: it.value ? (it.danger ? '#B91C1C' : '#92400E') : '#047857' }}>
                {it.value ? '已触发' : '未触发'}
              </strong>
            </div>
          ))}
          {f.unresolved_dimensions && f.unresolved_dimensions.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              未达成共识维度：{f.unresolved_dimensions.join('、')}
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🪞 我的画像</div>
        <div className="page-subtitle">点击下方按钮，逐项查看你在本项目中的能力画像</div>
      </div>

      {students.length > 1 && (
        <div className="card" style={{ marginBottom: 16, padding: 12 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>选择学生</div>
          <select
            className="form-select"
            value={me?.student_id || ''}
            onChange={(e) => onSwitchStudent(e.target.value)}
          >
            {students.map((s) => (
              <option key={s.student_id} value={s.student_id}>
                {s.student_id}（{s.latest_milestone} / {Math.round(s.latest_composite_score)}）
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">👤 当前学生</div>
        </div>
        {me ? (
          <div className="member-item" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
            <span className="member-avatar">👨‍🎓</span>
            <div className="member-info">
              <div className="member-name">{me.student_id}</div>
              <div className="member-detail">
                里程碑 {me.latest_milestone} ｜ {TIER_LABELS[normalizeTier(me.latest_tier)]}
              </div>
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: getScoreColor(me.latest_composite_score) }}>
              {Math.round(me.latest_composite_score)}
            </div>
          </div>
        ) : (
          <div className="empty-state">暂无学生数据</div>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 12,
          marginBottom: 20,
        }}
      >
        {PROFILE_BUTTONS.map((btn) => {
          const active = openKey === btn.key;
          return (
            <button
              key={btn.key}
              type="button"
              onClick={() => toggle(btn.key)}
              className="card"
              style={{
                textAlign: 'left',
                cursor: 'pointer',
                border: active ? '2px solid var(--primary)' : '1px solid var(--border)',
                background: active ? 'var(--primary-50, #EEF2FF)' : 'white',
                padding: 14,
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <span style={{ fontSize: 22 }}>{btn.icon}</span>
                <strong style={{ fontSize: 15, color: 'var(--text)' }}>{btn.title}</strong>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{btn.desc}</div>
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--primary)', fontWeight: 600 }}>
                {active ? '收起 ▲' : '展开 ▼'}
              </div>
            </button>
          );
        })}
      </div>

      {openKey && (
        <div className="card fade-in" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <div className="card-title">
              {PROFILE_BUTTONS.find((b) => b.key === openKey)?.icon}{' '}
              {PROFILE_BUTTONS.find((b) => b.key === openKey)?.title}
            </div>
            <button className="btn btn-outline" onClick={() => setOpenKey(null)} style={{ padding: '4px 12px', fontSize: 12 }}>
              收起
            </button>
          </div>
          {renderDetail(openKey)}
        </div>
      )}

      {loading && <div className="card">加载中...</div>}
      {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
    </div>
  );
}
