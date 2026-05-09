import { useState } from 'react';
import { discussions, documents, collaborationData, students, teams } from '../../data/mockData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function ProcessData() {
  const [activeTab, setActiveTab] = useState('discussions');
  const [activeTeam, setActiveTeam] = useState('team1');

  const getStudentName = (id) => students.find(s => s.id === id)?.name || id;
  const teamDiscussions = discussions.filter(d => d.teamId === activeTeam);
  const teamDocs = documents.filter(d => d.teamId === activeTeam);
  const collab = collaborationData[activeTeam];

  const weeklyData = collab.weeklyActivity.map(w => {
    const result = { week: w.week };
    const team = teams.find(t => t.id === activeTeam);
    team.members.forEach(mId => {
      result[getStudentName(mId)] = w[mId];
    });
    return result;
  });

  const colors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444'];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📝 过程数据采集</div>
        <div className="page-subtitle">自动记录并分析项目过程中的关键行为数据</div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {teams.map(t => (
          <button
            key={t.id}
            className={`btn ${activeTeam === t.id ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTeam(t.id)}
          >
            {t.name}
          </button>
        ))}
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'discussions' ? 'active' : ''}`} onClick={() => setActiveTab('discussions')}>
          💬 讨论记录
        </button>
        <button className={`tab ${activeTab === 'documents' ? 'active' : ''}`} onClick={() => setActiveTab('documents')}>
          📄 文档版本
        </button>
        <button className={`tab ${activeTab === 'activity' ? 'active' : ''}`} onClick={() => setActiveTab('activity')}>
          📊 活跃度分析
        </button>
        <button className={`tab ${activeTab === 'collaboration' ? 'active' : ''}`} onClick={() => setActiveTab('collaboration')}>
          🤝 协作关系
        </button>
      </div>

      {activeTab === 'discussions' && (
        <div>
          {teamDiscussions.map(disc => (
            <div className="card" key={disc.id} style={{ marginBottom: 16 }}>
              <div className="card-header">
                <div className="card-title">
                  💬 {disc.summary}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  {disc.date} · {disc.duration}分钟
                </div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ fontSize: 13, color: 'var(--text-muted)', marginRight: 8 }}>参与者：</span>
                {disc.participants.map(p => (
                  <span key={p} className="tag" style={{ marginRight: 6 }}>
                    {students.find(s => s.id === p)?.avatar} {getStudentName(p)}
                  </span>
                ))}
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>📌 关键要点：</div>
                {disc.keyPoints.map((kp, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
                    <span style={{ color: 'var(--primary)', fontWeight: 700 }}>•</span>
                    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{kp}</span>
                  </div>
                ))}
              </div>
              <div>
                {disc.tags.map((tag, i) => (
                  <span className="tag" key={i}>{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'documents' && (
        <div>
          {teamDocs.map(doc => (
            <div className="card" key={doc.id} style={{ marginBottom: 16 }}>
              <div className="card-header">
                <div className="card-title">📄 {doc.title}</div>
                <span className="badge active">当前版本：{doc.currentVersion}</span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>版本历史：</div>
              {doc.versions.map((v, i) => (
                <div className="doc-version" key={i}>
                  <span className="doc-version-tag">{v.version}</span>
                  <span>{students.find(s => s.id === v.author)?.avatar} {getStudentName(v.author)}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{v.date}</span>
                  <span style={{ flex: 1, color: 'var(--text-secondary)' }}>{v.changes}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📊 成员每周活跃度（小时）</div>
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="week" style={{ fontSize: 12 }} />
              <YAxis style={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              {teams.find(t => t.id === activeTeam)?.members.map((mId, i) => (
                <Bar key={mId} dataKey={getStudentName(mId)} fill={colors[i]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {activeTab === 'collaboration' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">🤝 团队协作互动记录</div>
          </div>
          <table>
            <thead>
              <tr>
                <th>成员A</th>
                <th>成员B</th>
                <th>互动类型</th>
                <th>互动强度</th>
              </tr>
            </thead>
            <tbody>
              {collab.interactions.map((inter, i) => (
                <tr key={i}>
                  <td>
                    {students.find(s => s.id === inter.from)?.avatar} {getStudentName(inter.from)}
                  </td>
                  <td>
                    {students.find(s => s.id === inter.to)?.avatar} {getStudentName(inter.to)}
                  </td>
                  <td><span className="tag">{inter.type}</span></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="progress-bar-container" style={{ width: 100 }}>
                        <div
                          className={`progress-bar ${inter.weight >= 6 ? 'green' : inter.weight >= 3 ? 'blue' : 'red'}`}
                          style={{ width: `${inter.weight * 12.5}%` }}
                        />
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{inter.weight}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
