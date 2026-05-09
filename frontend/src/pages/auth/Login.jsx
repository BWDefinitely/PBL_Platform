import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login(form);
      navigate(res.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
    } catch (err) {
      setError(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in" style={{ maxWidth: 460, margin: '48px auto' }}>
      <div className="card">
        <div className="card-header"><div className="card-title">登录平台</div></div>
        <form onSubmit={onSubmit}>
          <div style={{ marginBottom: 12 }}>
            <input className="input" style={{ width: '100%' }} placeholder="邮箱" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <input className="input" style={{ width: '100%' }} placeholder="密码" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          {error && <div style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</div>}
          <button className="btn btn-primary" disabled={loading} type="submit">{loading ? '登录中...' : '登录'}</button>
        </form>
        <div style={{ marginTop: 12, fontSize: 13 }}>
          没有账号？<Link to="/register">去注册</Link>
        </div>
      </div>
    </div>
  );
}
