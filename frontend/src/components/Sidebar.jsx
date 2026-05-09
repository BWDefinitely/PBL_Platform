import { useNavigate, useLocation } from 'react-router-dom';

const teacherNav = [
  { section: '核心功能', items: [
    { path: '/teacher/dashboard', icon: '📊', label: '项目总览' },
    { path: '/teacher/plan-generator', icon: '🤖', label: '教学方案生成' },
    { path: '/teacher/task-management', icon: '📋', label: '任务与进度管理' },
    { path: '/teacher/process-data', icon: '📝', label: '过程数据采集' },
    { path: '/teacher/evaluation', icon: '📈', label: 'AI过程评估' },
    { path: '/teacher/decision-support', icon: '🎯', label: '决策支持中心' },
  ]},
];

const studentNav = [
  { section: '我的空间', items: [
    { path: '/student/dashboard', icon: '🏠', label: '项目概览' },
    { path: '/student/tasks', icon: '✅', label: '我的任务' },
    { path: '/student/progress', icon: '📈', label: '任务进度' },
    { path: '/student/chat', icon: '💬', label: '团队讨论' },
    { path: '/student/files', icon: '📁', label: '文件管理' },
    { path: '/student/report', icon: '📊', label: '能力报告' },
    { path: '/student/profile', icon: '🪞', label: '我的画像' },
  ]},
];

export default function Sidebar({ role, userName = '', onLogout, isPreview = false, onSwitchRole }) {
  const navigate = useNavigate();
  const location = useLocation();
  const navItems = role === 'teacher' ? teacherNav : studentNav;
  const userInfo = role === 'teacher'
    ? { name: userName || '教师', avatar: '👨‍🏫', roleLabel: '教师端' }
    : { name: userName || '学生', avatar: '👨‍🎓', roleLabel: '学生端' };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🎓</div>
          PBL智教平台
        </div>
        <div className="sidebar-role">{userInfo.roleLabel}</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.section}>
            <div className="nav-section-title">{section.section}</div>
            {section.items.map((item) => (
              <div
                key={item.path}
                className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
              >
                <span className="nav-item-icon">{item.icon}</span>
                {item.label}
              </div>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">{userInfo.avatar}</div>
          <div>
            <div className="user-name">{userInfo.name}</div>
            <div className="user-role">{userInfo.roleLabel}</div>
          </div>
        </div>
        {isPreview && (
          <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <button
              className="btn btn-outline"
              onClick={() => onSwitchRole?.('teacher')}
              disabled={role === 'teacher'}
              style={{ width: '100%' }}
            >
              教师视角
            </button>
            <button
              className="btn btn-outline"
              onClick={() => onSwitchRole?.('student')}
              disabled={role === 'student'}
              style={{ width: '100%' }}
            >
              学生视角
            </button>
          </div>
        )}
        <button className="btn btn-outline" style={{ marginTop: 10, width: '100%' }} onClick={onLogout}>退出登录</button>
      </div>
    </div>
  );
}
