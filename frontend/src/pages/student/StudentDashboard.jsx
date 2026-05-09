import { projects, teams, tasks, students, discussions } from '../../data/mockData';

export default function StudentDashboard() {
  const currentStudent = students[0]; // 张三
  const project = projects[0];
  const team = teams.find(t => t.members.includes(currentStudent.id));
  const myTasks = tasks.filter(t => t.assignee === currentStudent.id);
  const teamTasks = tasks.filter(t => t.teamId === team?.id);
  const teamDiscussions = discussions.filter(d => d.teamId === team?.id);

  const completedCount = myTasks.filter(t => t.status === 'completed').length;
  const inProgressCount = myTasks.filter(t => t.status === 'in_progress').length;
  const teamCompletedCount = teamTasks.filter(t => t.status === 'completed').length;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🏠 项目概览</div>
        <div className="page-subtitle">欢迎回来，{currentStudent.name}！</div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon primary">📋</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.length}</div>
            <div className="stat-label">我的任务</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-content">
            <div className="stat-value">{completedCount}</div>
            <div className="stat-label">已完成</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">🔵</div>
          <div className="stat-content">
            <div className="stat-value">{inProgressCount}</div>
            <div className="stat-label">进行中</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">👥</div>
          <div className="stat-content">
            <div className="stat-value">{team?.members.length || 0}</div>
            <div className="stat-label">团队成员</div>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">📌 项目信息</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>{project.title}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{project.description}</p>
          </div>
          <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-muted)' }}>
            <span>📅 {project.startDate} ~ {project.endDate}</span>
            <span>👥 团队：{team?.name}</span>
          </div>

          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>项目阶段：</div>
            {project.phases.map((phase, i) => (
              <div className="phase-item" key={i}>
                <span className="phase-status-icon">
                  {phase.status === 'completed' ? '✅' : phase.status === 'active' ? '🔵' : '⚪'}
                </span>
                <span className="phase-name">{phase.name}</span>
                <span className={`badge ${phase.status}`}>
                  {phase.status === 'completed' ? '已完成' : phase.status === 'active' ? '进行中' : '未开始'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              <div className="card-title">👥 我的团队</div>
            </div>
            {team?.members.map(mId => {
              const member = students.find(s => s.id === mId);
              const memberTasks = tasks.filter(t => t.assignee === mId && t.teamId === team.id);
              const memberCompleted = memberTasks.filter(t => t.status === 'completed').length;
              return (
                <div className="member-item" key={mId}>
                  <span className="member-avatar">{member?.avatar}</span>
                  <div className="member-info">
                    <div className="member-name">
                      {member?.name}
                      {mId === team.leader && <span style={{ fontSize: 11, color: 'var(--primary)', marginLeft: 6 }}>👑 组长</span>}
                      {mId === currentStudent.id && <span style={{ fontSize: 11, color: 'var(--secondary)', marginLeft: 6 }}>（我）</span>}
                    </div>
                    <div className="member-detail">{member?.major}</div>
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {memberCompleted}/{memberTasks.length} 任务
                  </span>
                </div>
              );
            })}
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">💬 最近讨论</div>
            </div>
            {teamDiscussions.slice(-2).reverse().map(disc => (
              <div key={disc.id} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{disc.summary}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{disc.date}</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  {disc.keyPoints[0]}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">📅 团队任务进度</div>
        </div>
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
            <span>总体进度</span>
            <span style={{ fontWeight: 700 }}>{teamCompletedCount}/{teamTasks.length} 已完成</span>
          </div>
          <div className="progress-bar-container" style={{ height: 12 }}>
            <div
              className="progress-bar green"
              style={{ width: `${(teamCompletedCount / teamTasks.length) * 100}%` }}
            />
          </div>
        </div>
        <table style={{ marginTop: 16 }}>
          <thead>
            <tr>
              <th>任务</th>
              <th>负责人</th>
              <th>状态</th>
              <th>截止日期</th>
            </tr>
          </thead>
          <tbody>
            {teamTasks.map(t => {
              const assignee = students.find(s => s.id === t.assignee);
              return (
                <tr key={t.id}>
                  <td style={{ fontWeight: t.assignee === currentStudent.id ? 600 : 400 }}>
                    {t.title}
                    {t.assignee === currentStudent.id && <span style={{ color: 'var(--primary)', fontSize: 11, marginLeft: 6 }}>（我的）</span>}
                  </td>
                  <td>{assignee?.avatar} {assignee?.name}</td>
                  <td>
                    <span className={`badge ${t.status}`}>
                      {t.status === 'completed' ? '已完成' : t.status === 'in_progress' ? '进行中' : '未开始'}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t.dueDate}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
