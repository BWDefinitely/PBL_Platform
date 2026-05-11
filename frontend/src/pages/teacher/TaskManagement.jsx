import { useState } from 'react';
import { tasks, teams, students, projects } from '../../data/mockData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import PriorityAI from '../shared/PriorityAI';

export default function TaskManagement() {
  const [activeTeam, setActiveTeam] = useState('team1');
  const [view, setView] = useState('board');

  const teamTasks = tasks.filter(t => t.teamId === activeTeam);
  const pending = teamTasks.filter(t => t.status === 'pending');
  const inProgress = teamTasks.filter(t => t.status === 'in_progress');
  const completed = teamTasks.filter(t => t.status === 'completed');
  const team = teams.find(t => t.id === activeTeam);

  const getStudentName = (id) => students.find(s => s.id === id)?.name || '';
  const getStudentAvatar = (id) => students.find(s => s.id === id)?.avatar || '';

  const timelineData = [
    { week: '第1周', planned: 2, actual: 2 },
    { week: '第2周', planned: 4, actual: 3 },
    { week: '第3周', planned: 6, actual: 5 },
    { week: '第4周', planned: 8, actual: 5 },
  ];

  const memberProgress = team?.members.map(mId => {
    const memberTasks = teamTasks.filter(t => t.assignee === mId);
    const done = memberTasks.filter(t => t.status === 'completed').length;
    return {
      name: getStudentName(mId),
      total: memberTasks.length,
      completed: done,
      rate: memberTasks.length ? Math.round(done / memberTasks.length * 100) : 0,
    };
  }) || [];

  const TaskCard = ({ task }) => (
    <div className="task-card">
      <div className="task-card-title">{task.title}</div>
      <div className="task-card-meta">
        <div className="task-assignee">
          <span>{getStudentAvatar(task.assignee)}</span>
          <span>{getStudentName(task.assignee)}</span>
        </div>
        <span className={`badge ${task.priority}`}>{task.priority === 'high' ? '高' : '中'}</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
        截止：{task.dueDate}
      </div>
    </div>
  );

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="page-title">📋 任务与进度管理</div>
            <div className="page-subtitle">管理项目任务分配与团队进度</div>
          </div>
          <button className="btn btn-primary">➕ 创建任务</button>
        </div>
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
        <div style={{ flex: 1 }} />
        <button className={`btn btn-sm ${view === 'board' ? 'btn-secondary' : 'btn-outline'}`} onClick={() => setView('board')}>
          📋 看板
        </button>
        <button className={`btn btn-sm ${view === 'timeline' ? 'btn-secondary' : 'btn-outline'}`} onClick={() => setView('timeline')}>
          📈 进度
        </button>
        <button className={`btn btn-sm ${view === 'priority' ? 'btn-secondary' : 'btn-outline'}`} onClick={() => setView('priority')}>
          🤖 PriorityAI
        </button>
      </div>

      {view === 'priority' ? (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <PriorityAI />
        </div>
      ) : view === 'board' ? (
        <div className="task-board">
          <div className="task-column">
            <div className="task-column-header">
              <div className="task-column-title">
                <span className="status-dot pending" /> 未开始
              </div>
              <span className="task-column-count">{pending.length}</span>
            </div>
            {pending.map(t => <TaskCard key={t.id} task={t} />)}
          </div>

          <div className="task-column">
            <div className="task-column-header">
              <div className="task-column-title">
                <span className="status-dot in_progress" /> 进行中
              </div>
              <span className="task-column-count">{inProgress.length}</span>
            </div>
            {inProgress.map(t => <TaskCard key={t.id} task={t} />)}
          </div>

          <div className="task-column">
            <div className="task-column-header">
              <div className="task-column-title">
                <span className="status-dot completed" /> 已完成
              </div>
              <span className="task-column-count">{completed.length}</span>
            </div>
            {completed.map(t => <TaskCard key={t.id} task={t} />)}
          </div>
        </div>
      ) : (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <div className="card-title">📈 计划 vs 实际进度</div>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="week" style={{ fontSize: 12 }} />
                <YAxis style={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="planned" stroke="#94A3B8" strokeDasharray="5 5" name="计划完成" strokeWidth={2} />
                <Line type="monotone" dataKey="actual" stroke="#4F46E5" name="实际完成" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">👤 成员完成情况</div>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={memberProgress} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis type="number" domain={[0, 100]} unit="%" style={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" width={50} style={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="rate" fill="#4F46E5" radius={[0, 6, 6, 0]} barSize={20} name="完成率" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <div className="card-header">
              <div className="card-title">📅 项目时间线</div>
            </div>
            <div className="timeline">
              {projects[0].phases.map((phase, i) => (
                <div className={`timeline-item ${phase.status}`} key={i}>
                  <div className="timeline-date">{phase.duration}</div>
                  <div className="timeline-title">{phase.name}</div>
                  <div className="timeline-desc">
                    {phase.status === 'completed' ? '✅ 已完成' : phase.status === 'active' ? '🔵 进行中' : '⏳ 等待中'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
