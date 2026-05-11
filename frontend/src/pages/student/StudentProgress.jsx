import { useState } from 'react';
import { tasks, students, teams, projects } from '../../data/mockData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import PriorityAI from '../shared/PriorityAI';

const currentStudent = students[0]; // 张三
const team = teams.find(t => t.members.includes(currentStudent.id));

export default function StudentProgress() {
  const [view, setView] = useState('board');
  const project = projects[0];
  const teamTasks = tasks.filter(t => t.teamId === team?.id);
  const myTasks = teamTasks.filter(t => t.assignee === currentStudent.id);

  const pending = teamTasks.filter(t => t.status === 'pending');
  const inProgress = teamTasks.filter(t => t.status === 'in_progress');
  const completed = teamTasks.filter(t => t.status === 'completed');

  const getStudentName = (id) => students.find(s => s.id === id)?.name || '';
  const getStudentAvatar = (id) => students.find(s => s.id === id)?.avatar || '';

  const taskStatusData = [
    { name: '已完成', value: completed.length, color: '#10B981' },
    { name: '进行中', value: inProgress.length, color: '#4F46E5' },
    { name: '未开始', value: pending.length, color: '#94A3B8' },
  ];

  const memberProgress = team?.members.map(mId => {
    const memberTasks = teamTasks.filter(t => t.assignee === mId);
    const done = memberTasks.filter(t => t.status === 'completed').length;
    return {
      name: getStudentName(mId),
      avatar: getStudentAvatar(mId),
      total: memberTasks.length,
      completed: done,
      inProgress: memberTasks.filter(t => t.status === 'in_progress').length,
      rate: memberTasks.length ? Math.round(done / memberTasks.length * 100) : 0,
      isMe: mId === currentStudent.id,
    };
  }) || [];

  const timelineData = [
    { week: '第1周', planned: 2, actual: 2 },
    { week: '第2周', planned: 4, actual: 3 },
    { week: '第3周', planned: 6, actual: 5 },
    { week: '第4周', planned: 8, actual: 5 },
  ];

  const TaskCard = ({ task }) => {
    const isMyTask = task.assignee === currentStudent.id;
    return (
      <div className="task-card" style={{ borderLeft: isMyTask ? '3px solid var(--primary)' : 'none' }}>
        <div className="task-card-title">
          {task.title}
          {isMyTask && <span style={{ fontSize: 10, color: 'var(--primary)', marginLeft: 6, fontWeight: 700 }}>我的</span>}
        </div>
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
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📈 任务进度</div>
        <div className="page-subtitle">查看团队整体进度与个人任务状态</div>
      </div>

      {/* 统计卡片 */}
      <div className="stats-grid" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-content">
            <div className="stat-value">{completed.length}/{teamTasks.length}</div>
            <div className="stat-label">团队任务完成</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">📋</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.filter(t => t.status === 'completed').length}/{myTasks.length}</div>
            <div className="stat-label">我的任务完成</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">🔵</div>
          <div className="stat-content">
            <div className="stat-value">{inProgress.length}</div>
            <div className="stat-label">进行中任务</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">📅</div>
          <div className="stat-content">
            <div className="stat-value">{project.phases.filter(p => p.status === 'completed').length}/{project.phases.length}</div>
            <div className="stat-label">项目阶段</div>
          </div>
        </div>
      </div>

      {/* 视图切换 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button className={`btn btn-sm ${view === 'board' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setView('board')}>
          📋 看板视图
        </button>
        <button className={`btn btn-sm ${view === 'chart' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setView('chart')}>
          📊 数据视图
        </button>
        <button className={`btn btn-sm ${view === 'timeline' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setView('timeline')}>
          📅 时间线
        </button>
        <button className={`btn btn-sm ${view === 'priority' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setView('priority')}>
          🤖 PriorityAI
        </button>
      </div>

      {view === 'priority' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <PriorityAI />
        </div>
      )}

      {/* 看板视图 */}
      {view === 'board' && (
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
      )}

      {/* 数据视图 */}
      {view === 'chart' && (
        <div>
          <div className="grid-2" style={{ marginBottom: 20 }}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">📊 任务状态分布</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <ResponsiveContainer width="50%" height={200}>
                  <PieChart>
                    <Pie data={taskStatusData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" paddingAngle={3}>
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
                <div className="card-title">📈 计划 vs 实际进度</div>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="week" style={{ fontSize: 12 }} />
                  <YAxis style={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="planned" stroke="#94A3B8" strokeDasharray="5 5" name="计划" strokeWidth={2} />
                  <Line type="monotone" dataKey="actual" stroke="#4F46E5" name="实际" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">👥 成员完成进度</div>
            </div>
            {memberProgress.map((m, i) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '12px 0',
                borderBottom: i < memberProgress.length - 1 ? '1px solid var(--border-light)' : 'none',
              }}>
                <span style={{ fontSize: 24 }}>{m.avatar}</span>
                <div style={{ width: 60 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    {m.name}
                    {m.isMe && <span style={{ color: 'var(--primary)', fontSize: 11, marginLeft: 4 }}>（我）</span>}
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                    <span>{m.completed} 已完成 · {m.inProgress} 进行中</span>
                    <span style={{ fontWeight: 700, color: 'var(--text)' }}>{m.rate}%</span>
                  </div>
                  <div className="progress-bar-container">
                    <div
                      className={`progress-bar ${m.rate >= 50 ? 'green' : m.rate >= 25 ? 'blue' : 'yellow'}`}
                      style={{ width: `${m.rate}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 时间线视图 */}
      {view === 'timeline' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <div className="card-title">📅 项目阶段</div>
            </div>
            <div className="timeline">
              {project.phases.map((phase, i) => (
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

          <div className="card">
            <div className="card-header">
              <div className="card-title">📋 任务时间线</div>
            </div>
            <div className="timeline">
              {teamTasks
                .sort((a, b) => new Date(a.startDate) - new Date(b.startDate))
                .map((task, i) => {
                  const isMyTask = task.assignee === currentStudent.id;
                  return (
                    <div className={`timeline-item ${task.status}`} key={i}>
                      <div className="timeline-date">
                        {task.startDate} ~ {task.dueDate}
                      </div>
                      <div className="timeline-title" style={{ color: isMyTask ? 'var(--primary)' : 'var(--text)' }}>
                        {task.title}
                        {isMyTask && <span style={{ fontSize: 10, marginLeft: 6 }}>⭐ 我的</span>}
                      </div>
                      <div className="timeline-desc">
                        {getStudentAvatar(task.assignee)} {getStudentName(task.assignee)} ·
                        <span className={`badge ${task.status}`} style={{ marginLeft: 6, fontSize: 11, padding: '2px 6px' }}>
                          {task.status === 'completed' ? '已完成' : task.status === 'in_progress' ? '进行中' : '未开始'}
                        </span>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
