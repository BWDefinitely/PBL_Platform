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

function formatDimension(code) {
  return `${DIMENSION_LABELS[code] || code} (${code})`;
}

function normalizeEvidenceText(text) {
  if (!text) return '';
  return String(text)
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export default function StudentReport() {
  const { token } = useAuth();
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [me, setMe] = useState(null);
  const [detail, setDetail] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const studentList = await getStudents(token);
        setStudents(studentList);
        const first = studentList[0];
        if (!first) return;
        setSelectedStudentId(first.student_id);
        setMe(first);
      } catch (e) {
        setError(e.message || '加载能力报告失败');
      }
    };
    load();
  }, [token]);

  useEffect(() => {
    const loadDetail = async () => {
      if (!selectedStudentId || students.length === 0) return;
      const target = students.find((s) => s.student_id === selectedStudentId) || students[0];
      if (!target) return;
      try {
        setMe(target);
        const [d, ms] = await Promise.all([
          getStudentMilestoneDetail(token, target.student_id, target.latest_milestone),
          getStudentMilestones(token, target.student_id),
        ]);
        setDetail(d);
        setMilestones(ms || []);
      } catch (e) {
        setError(e.message || '加载能力报告失败');
      }
    };
    loadDetail();
  }, [token, selectedStudentId, students]);

  const radarData = useMemo(() => {
    if (!detail) return [];
    return DIMENSION_ORDER.map((d) => ({
      dimension: formatDimension(d),
      score: detail.domain_scores?.[d]?.normalized || 0,
      fullMark: 100,
    }));
  }, [detail]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'var(--secondary)';
    if (score >= 60) return 'var(--warning)';
    return 'var(--danger)';
  };

  const milestoneTrendData = useMemo(() => {
    const order = { M1: 1, M2: 2, M3: 3 };
    return [...milestones]
      .sort((a, b) => (order[a.milestone] || 0) - (order[b.milestone] || 0))
      .map((m) => ({
        milestone: m.milestone,
        composite: Math.round(m.composite_score || 0),
      }));
  }, [milestones]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📊 能力报告</div>
        <div className="page-subtitle">个性化能力分析与反馈</div>
      </div>
      {students.length > 1 && (
        <div className="card" style={{ marginBottom: 16, padding: 12 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>选择学生</div>
          <select
            className="input"
            value={selectedStudentId}
            onChange={(e) => setSelectedStudentId(e.target.value)}
          >
            {students.map((s) => (
              <option key={s.student_id} value={s.student_id}>
                {s.student_id}（{s.latest_milestone} / {Math.round(s.latest_composite_score)}）
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-icon green">⏱</div>
          <div className="stat-content">
            <div className="stat-value">{Math.round(detail?.composite_score || 0)}</div>
            <div className="stat-label">综合评分</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">📈</div>
          <div className="stat-content">
            <div className="stat-value">{detail?.milestone || '-'}</div>
            <div className="stat-label">最新里程碑</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">📊</div>
          <div className="stat-content">
            <div className="stat-value">{detail?.student_tier || '-'}</div>
            <div className="stat-label">学生等级</div>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">🎯 能力雷达图</div>
          </div>
          <div className="radar-container">
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="dimension" style={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} style={{ fontSize: 10 }} />
                  <Radar name={me?.student_id || '我的得分'} dataKey="score" stroke="#4F46E5" fill="#4F46E5" fillOpacity={0.25} strokeWidth={2} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">📊 各维度详细得分</div>
          </div>
          {DIMENSION_ORDER.map((d) => {
            const score = detail?.domain_scores?.[d]?.normalized || 0;
            return (
              <div className="score-bar" key={d}>
                <span className="score-bar-label">{formatDimension(d)}</span>
                <div className="score-bar-track">
                  <div
                    className="score-bar-fill"
                    style={{
                      width: `${score}%`,
                      backgroundColor: getScoreColor(score),
                    }}
                  />
                </div>
                <span className="score-bar-value" style={{ color: getScoreColor(score) }}>{score}</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">📉 里程碑成长趋势</div>
        </div>
        {milestoneTrendData.length === 0 ? (
          <div className="empty-state">暂无里程碑趋势数据</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
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

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">💡 有价值贡献记录</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          {(detail?.evidence_snippets || []).map((c, i) => {
            const sourceMeta = EVIDENCE_SOURCE_META[c.source] || EVIDENCE_SOURCE_META.collab_trace;
            const cleanText = normalizeEvidenceText(c.text);
            return (
              <div
                key={i}
                style={{
                  padding: 14,
                  background: 'var(--bg)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  minHeight: 150,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 18 }}>{sourceMeta.icon}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--primary)' }}>{sourceMeta.label}</span>
                  {c.trace_ref && (
                    <span
                      style={{
                        fontSize: 11,
                        color: 'var(--text-muted)',
                        background: 'white',
                        border: '1px solid var(--border)',
                        borderRadius: 999,
                        padding: '2px 8px',
                      }}
                    >
                      {c.trace_ref}
                    </span>
                  )}
                </div>
                <p
                  style={{
                    fontSize: 13,
                    color: 'var(--text-secondary)',
                    lineHeight: 1.7,
                    margin: 0,
                    wordBreak: 'break-word',
                    display: '-webkit-box',
                    WebkitLineClamp: 5,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {cleanText || '暂无可展示文本'}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid-2">
        <div className="card" style={{ borderLeft: '4px solid var(--secondary)' }}>
          <div className="card-header">
            <div className="card-title">✅ 你的优势</div>
          </div>
          {DIMENSION_ORDER
            .map((d) => ({ d, score: detail?.domain_scores?.[d]?.normalized || 0 }))
            .sort((a, b) => b.score - a.score)
            .slice(0, 2)
            .map((s, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--secondary)', fontSize: 16 }}>💪</span>
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{formatDimension(s.d)}表现较好（{Math.round(s.score)}）</span>
            </div>
          ))}
        </div>

        <div className="card" style={{ borderLeft: '4px solid var(--warning)' }}>
          <div className="card-header">
            <div className="card-title">📈 改进建议</div>
          </div>
          {DIMENSION_ORDER
            .map((d) => ({ d, score: detail?.domain_scores?.[d]?.normalized || 0 }))
            .sort((a, b) => a.score - b.score)
            .slice(0, 2)
            .map((w, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--warning)', fontSize: 16 }}>⚠️</span>
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{formatDimension(w.d)}需要提升（{Math.round(w.score)}）</span>
            </div>
          ))}
          <div style={{ marginTop: 16, padding: 12, background: 'var(--primary-50)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>💡 个性化建议</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, paddingLeft: 16 }}>
              1. 重点提升当前最低维度，并在下一里程碑中提供更可验证的过程证据。
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, paddingLeft: 16 }}>
              2. 在团队讨论中主动反馈与分工协作，可明显改善协作建构（CM）与沟通领导（CL）表现。
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, paddingLeft: 16 }}>
              3. 关注教师反馈并在文档迭代中体现修正轨迹，提升批判性思维（CT）与创新性推理（CR）说服力。
            </div>
          </div>
        </div>
      </div>
      {error && <div className="card" style={{ color: 'var(--danger)', marginTop: 12 }}>{error}</div>}
    </div>
  );
}
