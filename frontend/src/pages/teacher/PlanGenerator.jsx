import { useState } from 'react';
import { teachingPlanTemplate } from '../../data/mockData';

export default function PlanGenerator() {
  const [form, setForm] = useState({
    subject: '教育技术学',
    grade: '研究生',
    duration: '12周',
    objective: '设计并原型开发一个基于AI的个性化学习推荐系统',
    teamSize: '4-5人',
    keywords: 'AI, 个性化学习, 推荐系统',
  });
  const [generating, setGenerating] = useState(false);
  const [plan, setPlan] = useState(null);
  const [editMode, setEditMode] = useState(false);

  const handleGenerate = () => {
    setGenerating(true);
    setPlan(null);
    setTimeout(() => {
      setGenerating(false);
      setPlan(teachingPlanTemplate);
    }, 2500);
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🤖 教学方案生成</div>
        <div className="page-subtitle">输入教学信息，AI自动生成结构化PBL教学方案</div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">📝 基础信息输入</div>
          </div>

          <div className="form-group">
            <label className="form-label">学科领域</label>
            <select className="form-select" value={form.subject} onChange={e => setForm({...form, subject: e.target.value})}>
              <option>教育技术学</option>
              <option>计算机科学</option>
              <option>人工智能</option>
              <option>软件工程</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">年级</label>
            <select className="form-select" value={form.grade} onChange={e => setForm({...form, grade: e.target.value})}>
              <option>研究生</option>
              <option>本科高年级</option>
              <option>本科低年级</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">项目周期</label>
            <select className="form-select" value={form.duration} onChange={e => setForm({...form, duration: e.target.value})}>
              <option>6周</option>
              <option>8周</option>
              <option>10周</option>
              <option>12周</option>
              <option>16周</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">教学目标</label>
            <textarea className="form-textarea" value={form.objective} onChange={e => setForm({...form, objective: e.target.value})} />
          </div>

          <div className="form-group">
            <label className="form-label">团队规模</label>
            <select className="form-select" value={form.teamSize} onChange={e => setForm({...form, teamSize: e.target.value})}>
              <option>2-3人</option>
              <option>4-5人</option>
              <option>6-8人</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">关键词/跨学科领域</label>
            <input className="form-input" value={form.keywords} onChange={e => setForm({...form, keywords: e.target.value})} />
          </div>

          <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleGenerate}>
            ✨ AI生成教学方案
          </button>
        </div>

        <div>
          {generating && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="generating">
                <div className="generating-dots">
                  <span /><span /><span />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>AI正在生成教学方案...</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                    正在分析教学目标、构建项目情境、设计评估标准
                  </div>
                </div>
              </div>
            </div>
          )}

          {plan && (
            <div className="fade-in">
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-title">🌍 项目背景（真实情境）</div>
                  <button className="btn btn-sm btn-secondary" onClick={() => setEditMode(!editMode)}>
                    {editMode ? '💾 保存' : '✏️ 编辑'}
                  </button>
                </div>
                {editMode ? (
                  <textarea className="form-textarea" defaultValue={plan.projectBackground.trim()} style={{ minHeight: 120 }} />
                ) : (
                  <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                    {plan.projectBackground.trim()}
                  </p>
                )}
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-title">🎯 学习目标（能力导向）</div>
                </div>
                {plan.learningObjectives.map((obj, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 10, alignItems: 'center' }}>
                    <span className="tag">{obj.type}</span>
                    <span style={{ fontSize: 14 }}>{obj.content}</span>
                  </div>
                ))}
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-title">📋 项目任务拆解与时间规划</div>
                </div>
                {plan.taskBreakdown.map((phase, i) => (
                  <div className="plan-step" key={i}>
                    <div className="plan-step-number">{i + 1}</div>
                    <div className="plan-step-content">
                      <div className="plan-step-title">{phase.phase}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
                        ⏱ {phase.duration}
                      </div>
                      <ul className="plan-step-tasks">
                        {phase.tasks.map((task, j) => (
                          <li key={j}>{task}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <div className="card-title">🔗 跨学科融合点</div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {['人工智能', '学习科学', '用户体验设计', '数据分析', '教育心理学'].map((item, i) => (
                    <span className="tag" key={i}>{item}</span>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-title">📏 评估标准（Rubric）</div>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>评估维度</th>
                      <th>权重</th>
                      <th>描述</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { name: '研究能力', weight: '20%', desc: '文献综述、需求调研的深度与广度' },
                      { name: '设计能力', weight: '25%', desc: '方案设计的创新性、合理性与可行性' },
                      { name: '技术实现', weight: '20%', desc: '原型开发的技术水平与完成度' },
                      { name: '团队协作', weight: '20%', desc: '任务分工、沟通协调、冲突解决' },
                      { name: '展示表达', weight: '15%', desc: '成果展示的逻辑性、表达力与说服力' },
                    ].map((r, i) => (
                      <tr key={i}>
                        <td><strong>{r.name}</strong></td>
                        <td><span className="badge active">{r.weight}</span></td>
                        <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{r.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                <button className="btn btn-success">✅ 采用此方案</button>
                <button className="btn btn-outline" onClick={handleGenerate}>🔄 重新生成</button>
                <button className="btn btn-secondary">📥 导出方案</button>
              </div>
            </div>
          )}

          {!generating && !plan && (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">🤖</div>
                <p style={{ fontWeight: 600, marginBottom: 8 }}>AI方案生成器</p>
                <p style={{ fontSize: 14 }}>填写左侧表单后点击"AI生成教学方案"<br/>系统将自动为您生成结构化PBL教学方案</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
