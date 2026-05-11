import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    role: 'student',
    email: '',
    password: '',
    display_name: '',
    student_code: '',
    class_name: '',
    grade: '',
    organization: '',
    subject: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate(form.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
    } catch (err) {
      setError(err.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in" style={{ maxWidth: 560, margin: '36px auto' }}>
      <div className="card">
        <div className="card-header"><div className="card-title">注册账号</div></div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
          学生注册时「学号」须与已导入数据中的英文名一致（如 Alice、Bob），系统会把该账号与已有测评记录绑定。
          教师注册无需学号。若页面提示连不上后端，请确认 assessment-api 已在 8100 端口运行（开发模式下前端会通过 Vite 将 /api 代理到该端口）。
        </p>
        <form onSubmit={onSubmit}>
          <div style={{ marginBottom: 10 }}>
            <select className="input" style={{ width: '100%' }} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="student">学生</option>
              <option value="teacher">教师</option>
            </select>
          </div>
          <div style={{ marginBottom: 10 }}>
            <input className="input" style={{ width: '100%' }} placeholder="邮箱" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <input className="input" style={{ width: '100%' }} type="password" placeholder="密码（至少8位）" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <input className="input" style={{ width: '100%' }} placeholder="显示名" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          </div>

          {form.role === 'student' ? (
            <>
              <div style={{ marginBottom: 10 }}>
                <input className="input" style={{ width: '100%' }} placeholder="学号（student_code）" value={form.student_code} onChange={(e) => setForm({ ...form, student_code: e.target.value })} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <input className="input" style={{ width: '100%' }} placeholder="班级" value={form.class_name} onChange={(e) => setForm({ ...form, class_name: e.target.value })} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <input className="input" style={{ width: '100%' }} placeholder="年级" value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })} />
              </div>
            </>
          ) : (
            <>
              <div style={{ marginBottom: 10 }}>
                <input className="input" style={{ width: '100%' }} placeholder="机构" value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <input className="input" style={{ width: '100%' }} placeholder="学科" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
              </div>
            </>
          )}

          {error && <div style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</div>}
          <button className="btn btn-primary" disabled={loading} type="submit">{loading ? '注册中...' : '注册并登录'}</button>
        </form>
        <div style={{ marginTop: 12, fontSize: 13 }}>
          已有账号？<Link to="/login">去登录</Link>
        </div>
      </div>
    </div>
  );
}
