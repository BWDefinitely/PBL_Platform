import { useState } from 'react';
import { tasks, students } from '../../data/mockData';

export default function StudentTasks() {
  const currentStudent = students[0]; // 张三
  const myTasks = tasks.filter(t => t.assignee === currentStudent.id);
  const [filter, setFilter] = useState('all');

  const filteredTasks = filter === 'all' ? myTasks : myTasks.filter(t => t.status === filter);

  const getStatusInfo = (status) => {
    switch (status) {
      case 'completed': return { label: '已完成', icon: '✅', color: 'var(--secondary)' };
      case 'in_progress': return { label: '进行中', icon: '🔵', color: 'var(--primary)' };
      default: return { label: '未开始', icon: '⚪', color: 'var(--text-muted)' };
    }
  };

  const getPriorityInfo = (priority) => {
    switch (priority) {
      case 'high': return { label: '高优先级', color: 'var(--danger)' };
      default: return { label: '中优先级', color: 'var(--warning)' };
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">✅ 我的任务</div>
        <div className="page-subtitle">管理和追踪你的项目任务</div>
      </div>

      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card" style={{ cursor: 'pointer', border: filter === 'all' ? '2px solid var(--primary)' : '' }} onClick={() => setFilter('all')}>
          <div className="stat-icon primary">📋</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.length}</div>
            <div className="stat-label">全部任务</div>
          </div>
        </div>
        <div className="stat-card" style={{ cursor: 'pointer', border: filter === 'in_progress' ? '2px solid var(--primary)' : '' }} onClick={() => setFilter('in_progress')}>
          <div className="stat-icon yellow">🔵</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.filter(t => t.status === 'in_progress').length}</div>
            <div className="stat-label">进行中</div>
          </div>
        </div>
        <div className="stat-card" style={{ cursor: 'pointer', border: filter === 'completed' ? '2px solid var(--secondary)' : '' }} onClick={() => setFilter('completed')}>
          <div className="stat-icon green">✅</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.filter(t => t.status === 'completed').length}</div>
            <div className="stat-label">已完成</div>
          </div>
        </div>
        <div className="stat-card" style={{ cursor: 'pointer', border: filter === 'pending' ? '2px solid var(--text-muted)' : '' }} onClick={() => setFilter('pending')}>
          <div className="stat-icon primary">⏳</div>
          <div className="stat-content">
            <div className="stat-value">{myTasks.filter(t => t.status === 'pending').length}</div>
            <div className="stat-label">未开始</div>
          </div>
        </div>
      </div>

      {filteredTasks.map(task => {
        const statusInfo = getStatusInfo(task.status);
        const priorityInfo = getPriorityInfo(task.priority);
        return (
          <div className="card" key={task.id} style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{ fontSize: 28, marginTop: 4 }}>{statusInfo.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>{task.title}</h3>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span className={`badge ${task.priority}`}>{priorityInfo.label}</span>
                    <span className={`badge ${task.status}`}>{statusInfo.label}</span>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
                  {task.description}
                </p>
                <div style={{ display: 'flex', gap: 20, fontSize: 12, color: 'var(--text-muted)' }}>
                  <span>📅 开始：{task.startDate}</span>
                  <span>⏰ 截止：{task.dueDate}</span>
                  {task.completedDate && <span>✅ 完成：{task.completedDate}</span>}
                </div>

                {task.status === 'in_progress' && (
                  <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                    <button className="btn btn-sm btn-success">✅ 标记完成</button>
                    <button className="btn btn-sm btn-secondary">📝 更新进度</button>
                  </div>
                )}

                {task.status === 'pending' && (
                  <div style={{ marginTop: 12 }}>
                    <button className="btn btn-sm btn-primary">▶️ 开始任务</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
