import { useCallback, useEffect, useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../../context/AuthContext';
import {
  createIntervention,
  getInterventions,
  getReports,
  getStudents,
  updateInterventionStatus,
} from '../../shared/api/assessment';
import { API_BASE } from '../../shared/api/client';

const ACTION_TYPE_LABELS = {
  watchlist: '重点关注',
  one_on_one_plan: '1v1 计划',
  milestone_intervention_task: '里程碑干预',
};

const TIER_LABELS = {
  Beginning: '起步',
  Developing: '发展中',
  Proficient: '熟练',
  Exemplary: '卓越',
};

export default function DecisionSupport() {
  const { token } = useAuth();
  const [students, setStudents] = useState([]);
  const [reports, setReports] = useState([]);
  const [error, setError] = useState('');
  const [actionFeedback, setActionFeedback] = useState('');
  const [interventions, setInterventions] = useState([]);
  const [intLoading, setIntLoading] = useState(false);
  const [intError, setIntError] = useState('');
  const [intStudent, setIntStudent] = useState('');
  const [intAction, setIntAction] = useState('');
  const [intStatus, setIntStatus] = useState('');

  const reloadInterventions = useCallback(async () => {
    if (!token) return;
    const params = {};
    if (intStudent) params.student_id = intStudent;
    if (intAction) params.action_type = intAction;
    if (intStatus) params.status = intStatus;
    const list = await getInterventions(token, params);
    setInterventions(Array.isArray(list) ? list : []);
  }, [token, intStudent, intAction, intStatus]);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, r] = await Promise.all([getStudents(token), getReports(token)]);
        setStudents(s);
        setReports(r);
      } catch (e) {
        setError(e.message || '加载决策数据失败');
      }
    };
    load();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setIntLoading(true);
      setIntError('');
      try {
        await reloadInterventions();
      } catch (e) {
        if (!cancelled) setIntError(e.message || '加载干预记录失败');
      } finally {
        if (!cancelled) setIntLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, reloadInterventions]);

  const riskStudents = useMemo(
    () => students.filter((s) => s.intervention_alert || s.latest_composite_score < 62.5),
    [students]
  );
  const averageScore = useMemo(() => {
    if (!students.length) return 0;
    return Math.round(students.reduce((acc, cur) => acc + cur.latest_composite_score, 0) / students.length);
  }, [students]);

  const tierBuckets = useMemo(() => {
    const map = { Beginning: 0, Developing: 0, Proficient: 0, Exemplary: 0 };
    const normalizeTier = (tier) => {
      if (!tier) return 'Developing';
      if (tier === 'Standard') return 'Proficient';
      if (tier === 'Advanced') return 'Exemplary';
      return ['Beginning', 'Developing', 'Proficient', 'Exemplary'].includes(tier) ? tier : 'Developing';
    };
    students.forEach((s) => {
      const key = normalizeTier(s.latest_tier);
      map[key] += 1;
    });
    return Object.entries(map).map(([metric, count]) => ({
      metric,
      metricLabel: TIER_LABELS[metric] || metric,
      count,
    }));
  }, [students]);

  const scoreBandData = useMemo(() => {
    const buckets = [
      { band: '<60', count: 0, explanation: '高风险，需要优先干预' },
      { band: '60-69', count: 0, explanation: '临界区，需持续跟踪' },
      { band: '70-84', count: 0, explanation: '稳健区，建议定向提升' },
      { band: '>=85', count: 0, explanation: '优势区，可承担示范角色' },
    ];
    students.forEach((s) => {
      const score = Number(s.latest_composite_score || 0);
      if (score < 60) buckets[0].count += 1;
      else if (score < 70) buckets[1].count += 1;
      else if (score < 85) buckets[2].count += 1;
      else buckets[3].count += 1;
    });
    return buckets;
  }, [students]);

  const teachingInsights = useMemo(() => {
    if (!students.length) return [];
    const riskRate = Math.round((riskStudents.length / students.length) * 100);
    const highScoreCount = scoreBandData.find((x) => x.band === '>=85')?.count || 0;
    const lowScoreCount = scoreBandData.find((x) => x.band === '<60')?.count || 0;
    const developingCount = tierBuckets.find((x) => x.metric === 'Developing')?.count || 0;

    const insights = [];
    if (riskRate >= 30) {
      insights.push(`当前风险学生占比 ${riskRate}%，建议本周优先安排 1 对 1 反馈与小组复盘。`);
    } else {
      insights.push(`当前风险学生占比 ${riskRate}%，整体可控，建议采用分层跟进策略保持稳定。`);
    }
    if (developingCount > students.length * 0.4) {
      insights.push(`“发展中”阶段学生较多（${developingCount} 人），建议增加过程性示范与阶段检查点。`);
    }
    if (lowScoreCount > 0) {
      insights.push(`低于 60 分学生有 ${lowScoreCount} 人，建议聚焦沟通与协作证据的补强。`);
    }
    if (highScoreCount > 0) {
      insights.push(`85 分以上学生有 ${highScoreCount} 人，可作为同伴互助中的“示范组长”。`);
    }
    return insights;
  }, [students, riskStudents.length, scoreBandData, tierBuckets]);

  const topConcernStudents = useMemo(() => {
    return [...students]
      .sort((a, b) => a.latest_composite_score - b.latest_composite_score)
      .slice(0, 5)
      .map((s) => ({
        ...s,
        reason: s.intervention_alert
          ? '触发 intervention_alert'
          : `综合分偏低（${Math.round(s.latest_composite_score)}）`,
      }));
  }, [students]);

  const handleTeacherAction = async (actionType, actionLabel, studentId, milestone) => {
    try {
      const res = await createIntervention(token, {
        student_id: studentId,
        action_type: actionType,
        milestone,
        note: `${actionLabel}（由决策支持中心触发）`,
      });
      const stamp = new Date(res.created_at || Date.now()).toLocaleTimeString('zh-CN', { hour12: false });
      setActionFeedback(`[${stamp}] 已为 ${studentId} 创建：${actionLabel}（ID: ${res.id}）`);
      try {
        await reloadInterventions();
      } catch (_) {
        /* 列表刷新失败不影响创建成功提示 */
      }
    } catch (e) {
      setActionFeedback(`操作失败：${e.message || '创建干预记录失败'}`);
    }
  };

  const handleMarkInterventionDone = async (id) => {
    try {
      setIntError('');
      await updateInterventionStatus(token, id, 'done');
      await reloadInterventions();
    } catch (e) {
      setIntError(e.message || '更新状态失败');
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🎯 决策支持中心</div>
        <div className="page-subtitle">AI辅助教师进行项目监控与干预决策</div>
      </div>

      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-icon red">🚨</div>
          <div className="stat-content">
            <div className="stat-value">{riskStudents.length}</div>
            <div className="stat-label">风险学生数量</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{reports.length}</div>
            <div className="stat-label">报告批次</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">📊</div>
          <div className="stat-content">
            <div className="stat-value">{averageScore}</div>
            <div className="stat-label">平均学生评分</div>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">🚨 风险学生告警</div>
          </div>
          {riskStudents.map((s) => (
              <div className="alert-item high" key={s.student_id}>
                <div className="alert-icon">🔴</div>
                <div className="alert-content">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="alert-title">{s.student_id} 需要关注</div>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.latest_milestone}</span>
                  </div>
                  <div className="alert-desc">最新综合分：{Math.round(s.latest_composite_score)} ｜ 最新等级：{s.latest_tier}</div>
                  <div className="alert-suggestion">💡 建议：优先安排一次 1 对 1 指导并追踪下一里程碑变化。</div>
                </div>
              </div>
          ))}
        </div>

        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <div className="card-title">⚠️ 需关注学生</div>
            </div>
            {riskStudents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">✅</div>
                <p>当前没有高风险学生</p>
              </div>
            ) : (
              riskStudents.map(s => (
                <div className="member-item" key={s.student_id} style={{ borderLeft: '3px solid var(--danger)', paddingLeft: 16, marginBottom: 8 }}>
                  <span className="member-avatar">👨‍🎓</span>
                  <div className="member-info">
                    <div className="member-name">{s.student_id}</div>
                    <div className="member-detail">里程碑：{s.latest_milestone}</div>
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--danger)' }}>
                    {Math.round(s.latest_composite_score)}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">📊 团队对比分析</div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={tierBuckets}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="metricLabel" style={{ fontSize: 11 }} />
                <YAxis style={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => [value, '人数']} />
                <Bar dataKey="count" fill="#4F46E5" name="人数" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">📚 教师解读报告</div>
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            {teachingInsights.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无可解读数据</div>
            ) : (
              teachingInsights.map((text, idx) => (
                <div
                  key={idx}
                  style={{
                    fontSize: 13,
                    color: 'var(--text-secondary)',
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                    lineHeight: 1.7,
                  }}
                >
                  {idx + 1}. {text}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">🧭 优先关注学生（Top 5）</div>
          </div>
          {topConcernStudents.map((s) => (
            <div
              className="member-item"
              key={s.student_id}
              style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', marginBottom: 8 }}
            >
              <span className="member-avatar">👨‍🎓</span>
              <div className="member-info">
                <div className="member-name">{s.student_id}</div>
                <div className="member-detail">{s.reason}</div>
              </div>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--danger)' }}>
                {Math.round(s.latest_composite_score)}
              </div>
            </div>
          ))}
          <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
            {topConcernStudents.slice(0, 3).map((s) => (
              <div key={`${s.student_id}-actions`} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => handleTeacherAction('watchlist', '加入重点关注名单', s.student_id, s.latest_milestone)}
                >
                  关注 {s.student_id}
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => handleTeacherAction('one_on_one_plan', '创建1v1反馈计划', s.student_id, s.latest_milestone)}
                >
                  1v1计划
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => handleTeacherAction('milestone_intervention_task', '创建里程碑干预任务', s.student_id, s.latest_milestone)}
                >
                  干预任务
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">📊 分数段分布与教学含义</div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={scoreBandData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="band" style={{ fontSize: 11 }} />
              <YAxis style={{ fontSize: 11 }} />
              <Tooltip formatter={(value) => [value, '人数']} />
              <Bar dataKey="count" fill="#0EA5E9" name="人数" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
            {scoreBandData.map((item) => (
              <div key={item.band} style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {item.band}：{item.explanation}
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">🧠 教学动作建议</div>
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: '#FEF2F2', border: '1px solid #FECACA' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#B91C1C', marginBottom: 4 }}>短期（本周）</div>
              <div style={{ fontSize: 13, color: '#7F1D1D', lineHeight: 1.7 }}>
                针对低分段学生开展 1v1 快速面谈，明确下一里程碑的证据提交要求（讨论、文档、协作三类至少覆盖两类）。
              </div>
            </div>
            <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: '#FFFBEB', border: '1px solid #FDE68A' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#92400E', marginBottom: 4 }}>中期（下个里程碑）</div>
              <div style={{ fontSize: 13, color: '#78350F', lineHeight: 1.7 }}>
                对“发展中”学生设置分层任务：补强沟通与协作证据；对高分学生安排同伴指导职责，提升组内扩散效应。
              </div>
            </div>
            <div style={{ padding: 12, borderRadius: 'var(--radius-sm)', background: '#ECFDF5', border: '1px solid #A7F3D0' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#065F46', marginBottom: 4 }}>长期（课程周期）</div>
              <div style={{ fontSize: 13, color: '#064E3B', lineHeight: 1.7 }}>
                建议在每个里程碑后固定输出“风险原因 + 干预动作 + 复评结果”三联单，形成可追踪的教学改进闭环。
              </div>
            </div>
          </div>
          {actionFeedback && (
            <div
              style={{
                marginTop: 12,
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--primary-50)',
                border: '1px solid var(--primary-100)',
                color: 'var(--primary-dark)',
                fontSize: 12,
              }}
            >
              {actionFeedback}
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header" style={{ flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
          <div className="card-title">📋 干预记录</div>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => reloadInterventions()}>
            刷新
          </button>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 14, alignItems: 'center' }}>
          <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8, alignItems: 'center' }}>
            学生
            <select
              className="input"
              style={{ minWidth: 140 }}
              value={intStudent}
              onChange={(e) => setIntStudent(e.target.value)}
            >
              <option value="">全部</option>
              {students.map((s) => (
                <option key={s.student_id} value={s.student_id}>
                  {s.student_id}
                </option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8, alignItems: 'center' }}>
            动作类型
            <select
              className="input"
              style={{ minWidth: 140 }}
              value={intAction}
              onChange={(e) => setIntAction(e.target.value)}
            >
              <option value="">全部</option>
              <option value="watchlist">重点关注</option>
              <option value="one_on_one_plan">1v1 计划</option>
              <option value="milestone_intervention_task">里程碑干预</option>
            </select>
          </label>
          <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8, alignItems: 'center' }}>
            状态
            <select
              className="input"
              style={{ minWidth: 100 }}
              value={intStatus}
              onChange={(e) => setIntStatus(e.target.value)}
            >
              <option value="">全部</option>
              <option value="open">进行中</option>
              <option value="done">已完成</option>
            </select>
          </label>
          {intLoading && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>加载中…</span>}
        </div>
        {intError && (
          <div style={{ fontSize: 13, color: 'var(--danger)', marginBottom: 10 }}>{intError}</div>
        )}
        {interventions.length === 0 && !intLoading ? (
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无记录，可通过上方按钮创建干预。</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '8px 6px' }}>ID</th>
                  <th style={{ padding: '8px 6px' }}>学生</th>
                  <th style={{ padding: '8px 6px' }}>动作</th>
                  <th style={{ padding: '8px 6px' }}>里程碑</th>
                  <th style={{ padding: '8px 6px' }}>状态</th>
                  <th style={{ padding: '8px 6px' }}>创建时间</th>
                  <th style={{ padding: '8px 6px' }}>备注</th>
                  <th style={{ padding: '8px 6px' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {interventions.map((row) => {
                  const notePreview =
                    row.note && row.note.length > 48 ? `${row.note.slice(0, 48)}…` : row.note || '—';
                  const created =
                    row.created_at &&
                    new Date(row.created_at).toLocaleString('zh-CN', { hour12: false });
                  const actionLabel = ACTION_TYPE_LABELS[row.action_type] || row.action_type;
                  const statusLabel = row.status === 'done' ? '已完成' : row.status === 'open' ? '进行中' : row.status;
                  return (
                    <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '8px 6px', color: 'var(--text-muted)' }}>{row.id}</td>
                      <td style={{ padding: '8px 6px' }}>{row.student_id}</td>
                      <td style={{ padding: '8px 6px' }}>{actionLabel}</td>
                      <td style={{ padding: '8px 6px' }}>{row.milestone || '—'}</td>
                      <td style={{ padding: '8px 6px' }}>{statusLabel}</td>
                      <td style={{ padding: '8px 6px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                        {created || '—'}
                      </td>
                      <td style={{ padding: '8px 6px', color: 'var(--text-secondary)', maxWidth: 220 }} title={row.note || ''}>
                        {notePreview}
                      </td>
                      <td style={{ padding: '8px 6px' }}>
                        {row.status === 'open' ? (
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            onClick={() => handleMarkInterventionDone(row.id)}
                          >
                            标记完成
                          </button>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">🤖 AI综合建议</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ padding: 16, background: '#FEF2F2', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--danger)', marginBottom: 8 }}>🔴 紧急关注</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              当前应重点关注综合分低于 62.5 或触发 intervention_alert 的学生。
              对于连续两个里程碑下降者，建议自动进入教师重点跟踪名单。
            </p>
          </div>
          <div style={{ padding: 16, background: '#FFFBEB', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--warning)', marginBottom: 8 }}>🟡 进度关注</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              建议在评估运行完成后自动生成“里程碑变化对比”，并结合过程证据定位原因。
            </p>
          </div>
          <div style={{ padding: 16, background: '#ECFDF5', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--secondary)', marginBottom: 8 }}>🟢 积极发现</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              系统已支持基于真实评估数据的风险识别，后续可结合项目模块做组内/组间诊断。
            </p>
          </div>
          <div style={{ padding: 16, background: 'var(--primary-50)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>💡 教学建议</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              你可以将本页面联动“发起评估任务”按钮，让教师直接触发下一个里程碑评估闭环。
            </p>
          </div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 20 }}>
        <div className="card-header">
          <div className="card-title">🖼 测评可视化报告</div>
        </div>
        {reports.length === 0 ? (
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无报告批次，请先执行评估并导入报告。</div>
        ) : (
          reports.slice(0, 1).map((run) => (
            <div key={run.run_id}>
              <div style={{ fontSize: 13, marginBottom: 10, color: 'var(--text-secondary)' }}>run_id: {run.run_id}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
                {run.artifacts
                  .filter((a) => a.type === 'chart_png')
                  .slice(0, 4)
                  .map((a) => (
                    <div key={a.name} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 10 }}>
                      <div style={{ fontSize: 12, marginBottom: 6 }}>{a.name}</div>
                      <img src={`${API_BASE}${a.url}`} alt={a.name} style={{ width: '100%', borderRadius: 6 }} />
                    </div>
                  ))}
              </div>
            </div>
          ))
        )}
      </div>
      {error && <div className="card" style={{ color: 'var(--danger)' }}>{error}</div>}
    </div>
  );
}
