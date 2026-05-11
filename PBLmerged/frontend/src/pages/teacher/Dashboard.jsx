import { projects, teams, tasks, students, alerts, evaluations } from '../../data/mockData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

export default function TeacherDashboard() {
  const project = projects[0];
  const totalTasks = tasks.filter(t => t.projectId === 'p1');
  const completedTasks = totalTasks.filter(t => t.status === 'completed');
  const inProgressTasks = totalTasks.filter(t => t.status === 'in_progress');
  const pendingTasks = totalTasks.filter(t => t.status === 'pending');
  const unresolvedAlerts = alerts.filter(a => !a.resolved);

  const taskStatusData = [
    { name: '已完成', value: completedTasks.length, color: '#10B981' },
    { name: '进行中', value: inProgressTasks.length, color: '#4F46E5' },
    { name: '未开始', value: pendingTasks.length, color: '#94A3B8' },
  ];

  const teamScores = [
    { name: 'AI教育创新组', score: evaluations.team1.overallScore },
    { name: '智慧课堂组', score: evaluations.team2.overallScore },
  ];

  const phaseProgress = project.phases.map((p, i) => ({
    phase: p.name,
    progress: p.status === 'completed' ? 100 : p.status === 'active' ? 60 : 0,
  }));

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📊 项目总览</div>
        <div className="page-subtitle">{project.title}</div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon primary">👥</div>
          <div className="stat-content">
            <div className="stat-value">{students.length}</div>
            <div className="stat-label">参与学生</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-content">
            <div className="stat-value">{completedTasks.length}/{totalTasks.length}</div>
            <div className="stat-label">任务完成率</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">📊</div>
          <div className="stat-content">
            <div className="stat-value">{teams.length}</div>
            <div className="stat-label">项目团队</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{unresolvedAlerts.length}</div>
            <div className="stat-label">待处理告警</div>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">📈 任务完成情况</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie data={taskStatusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={3}>
                  {taskStatusData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {taskStatusData.map(item => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <div style={{ width: 12, height: 12, borderRadius: 3, background: item.color }} />
                  <span style={{ fontSize: 14, flex: 1 }}>{item.name}</span>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">🏆 团队评分对比</div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={teamScores} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="name" width={110} style={{ fontSize: 13 }} />
              <Tooltip />
              <Bar dataKey="score" fill="#4F46E5" radius={[0, 6, 6, 0]} barSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">📅 项目阶段进度</div>
          </div>
          {project.phases.map((phase, i) => (
            <div className="phase-item" key={i}>
              <span className="phase-status-icon">
                {phase.status === 'completed' ? '✅' : phase.status === 'active' ? '🔵' : '⚪'}
              </span>
              <span className="phase-name">{phase.name}</span>
              <span className="phase-duration">{phase.duration}</span>
              <span className={`badge ${phase.status}`}>
                {phase.status === 'completed' ? '已完成' : phase.status === 'active' ? '进行中' : '未开始'}
              </span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">⚠️ 系统告警</div>
          </div>
          {unresolvedAlerts.slice(0, 3).map(alert => (
            <div className={`alert-item ${alert.severity}`} key={alert.id}>
              <div className="alert-icon">
                {alert.severity === 'high' ? '🔴' : alert.severity === 'medium' ? '🟡' : '🟢'}
              </div>
              <div className="alert-content">
                <div className="alert-title">{alert.title}</div>
                <div className="alert-desc">{alert.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
