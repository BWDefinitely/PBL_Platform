import { useEffect, useState } from 'react';
import { priorityHealth, prioritize } from '../../shared/api/priority';
import './PriorityAI.css';

const EMOTIONS = [
  { value: 'happy', emoji: '😄' },
  { value: 'neutral', emoji: '😐' },
  { value: 'sad', emoji: '😔' },
  { value: 'stressed', emoji: '😰' },
];

const ENVIRONMENTS = [
  { value: 'home', label: '🏠 家里' },
  { value: 'office', label: '🏢 办公室' },
  { value: 'cafe', label: '☕ 咖啡厅' },
  { value: 'travel', label: '🚄 旅途中' },
];

export default function PriorityAI() {
  const [userState, setUserState] = useState({
    energy: 7,
    emotion: 'neutral',
    available_time: 120,
    environment: 'home',
  });
  const [tasks, setTasks] = useState([
    { id: '1', name: '', deadline: '', urgency: 'medium', importance: 5, estimated_time: 30 },
  ]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    priorityHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: 'error' }));
  }, []);

  const addTask = () => {
    setTasks([
      ...tasks,
      { id: String(Date.now()), name: '', deadline: '', urgency: 'medium', importance: 5, estimated_time: 30 },
    ]);
  };
  const removeTask = (index) => {
    if (tasks.length > 1) setTasks(tasks.filter((_, i) => i !== index));
  };
  const updateTask = (index, field, value) => {
    const next = [...tasks];
    next[index] = { ...next[index], [field]: value };
    setTasks(next);
  };

  const handlePrioritize = async () => {
    const validTasks = tasks.filter((t) => t.name.trim() !== '');
    if (validTasks.length === 0) {
      setError('请至少添加一个任务');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await prioritize({ user_state: userState, tasks: validTasks });
      setResult(data);
    } catch (err) {
      setError(err?.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="priority-ai">
      <header className="pa-header">
        <h1>🎯 PriorityAI</h1>
        <p>智能优先级排序系统 | Multi-Agent 驱动</p>
        <div className="pa-status-badge">
          <span className={`pa-status-dot ${health?.status === 'healthy' ? 'green' : 'red'}`} />
          {health?.status === 'healthy' ? '系统正常' : '系统异常'}
        </div>
      </header>

      <main className="pa-main">
        <div className="pa-input-panel">
          <section className="pa-card">
            <h2>📊 当前状态</h2>
            <div className="pa-form-group">
              <label>精力水平: {userState.energy}/10</label>
              <input
                type="range"
                min="1"
                max="10"
                value={userState.energy}
                onChange={(e) => setUserState({ ...userState, energy: parseInt(e.target.value, 10) })}
              />
              <div className="pa-energy-visual">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className={`pa-energy-bar ${i < userState.energy ? 'active' : ''}`} />
                ))}
              </div>
            </div>

            <div className="pa-form-group">
              <label>情绪状态</label>
              <div className="pa-emoji-selector">
                {EMOTIONS.map((e) => (
                  <button
                    key={e.value}
                    type="button"
                    className={`pa-emoji-btn ${userState.emotion === e.value ? 'selected' : ''}`}
                    onClick={() => setUserState({ ...userState, emotion: e.value })}
                  >
                    {e.emoji}
                  </button>
                ))}
              </div>
            </div>

            <div className="pa-form-group">
              <label>可用时间: {userState.available_time} 分钟</label>
              <input
                type="range"
                min="15"
                max="480"
                step="15"
                value={userState.available_time}
                onChange={(e) => setUserState({ ...userState, available_time: parseInt(e.target.value, 10) })}
              />
            </div>

            <div className="pa-form-group">
              <label>当前环境</label>
              <div className="pa-env-selector">
                {ENVIRONMENTS.map((env) => (
                  <button
                    key={env.value}
                    type="button"
                    className={`pa-env-btn ${userState.environment === env.value ? 'selected' : ''}`}
                    onClick={() => setUserState({ ...userState, environment: env.value })}
                  >
                    {env.label}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="pa-card">
            <div className="pa-card-header">
              <h2>📝 任务列表</h2>
              <button type="button" className="pa-btn-add" onClick={addTask}>+ 添加任务</button>
            </div>
            {tasks.map((task, index) => (
              <div key={task.id} className="pa-task-input">
                <input
                  type="text"
                  placeholder="任务名称..."
                  value={task.name}
                  onChange={(e) => updateTask(index, 'name', e.target.value)}
                />
                <input
                  type="datetime-local"
                  value={task.deadline}
                  onChange={(e) => updateTask(index, 'deadline', e.target.value)}
                />
                <div className="pa-task-meta">
                  <select
                    value={task.urgency}
                    onChange={(e) => updateTask(index, 'urgency', e.target.value)}
                  >
                    <option value="low">不紧急</option>
                    <option value="medium">一般</option>
                    <option value="high">紧急</option>
                  </select>
                  <div className="pa-importance">
                    <span>重要: {task.importance}</span>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={task.importance}
                      onChange={(e) => updateTask(index, 'importance', parseInt(e.target.value, 10))}
                    />
                  </div>
                  <input
                    type="number"
                    min="5"
                    max="240"
                    value={task.estimated_time}
                    onChange={(e) => updateTask(index, 'estimated_time', parseInt(e.target.value, 10))}
                  />
                  <span>分钟</span>
                </div>
                {tasks.length > 1 && (
                  <button type="button" className="pa-btn-remove" onClick={() => removeTask(index)}>×</button>
                )}
              </div>
            ))}
          </section>

          <button type="button" className="pa-btn-submit" onClick={handlePrioritize} disabled={loading}>
            {loading ? '🤖 分析中...' : '🎯 获取优先级排序'}
          </button>
          {error && <div className="pa-error">{error}</div>}
        </div>

        <div className="pa-result-panel">
          {result ? (
            <>
              <section className="pa-card">
                <h2>🧠 状态分析</h2>
                <div className="pa-status-summary">
                  <div className="pa-stat">
                    <span className="pa-stat-value">{result.status_analysis.effective_energy}</span>
                    <span className="pa-stat-label">有效精力</span>
                  </div>
                  <div className="pa-stat">
                    <span className="pa-stat-value">{result.status_analysis.productivity_estimate}%</span>
                    <span className="pa-stat-label">生产力</span>
                  </div>
                </div>
                <p className="pa-advice">{result.status_analysis.advice}</p>
                {result.status_analysis.warnings?.length > 0 && (
                  <div className="pa-warnings">
                    {result.status_analysis.warnings.map((w, i) => (
                      <span key={i} className="pa-warning-tag">{w}</span>
                    ))}
                  </div>
                )}
              </section>

              <section className="pa-card">
                <h2>🏆 优先级排序</h2>
                <div className="pa-ranking-list">
                  {result.ranking.map((item, index) => (
                    <div key={item.task_id} className={`pa-rank-item pa-rank-${index + 1}`}>
                      <div className="pa-rank-number">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                      </div>
                      <div className="pa-rank-content">
                        <h3>{item.task_name}</h3>
                        <div className="pa-rank-meta">
                          <span className="pa-quadrant">{item.eisenhower_quadrant}</span>
                          <span>{item.estimated_time}分钟</span>
                          <span className="pa-score">得分: {item.priority_score}</span>
                        </div>
                        <p className="pa-rank-advice">{item.execution_advice}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="pa-card">
                <h2>💡 整体建议</h2>
                <pre className="pa-recommendation">{result.summary.recommendation}</pre>
                <h3>执行计划</h3>
                <div className="pa-execution-plan">
                  {result.summary.execution_plan && Object.entries(result.summary.execution_plan)
                    .filter(([key]) => key.startsWith('phase'))
                    .map(([phase, data]) => (
                      data.tasks?.length > 0 && (
                        <div key={phase} className="pa-phase">
                          <h4>{data.name} ({data.time}分钟)</h4>
                          <ul>
                            {data.tasks.map((t, i) => <li key={i}>{t}</li>)}
                          </ul>
                        </div>
                      )
                    ))}
                </div>
              </section>

              <section className="pa-card">
                <h2>⚙️ Agent 执行日志</h2>
                <div className="pa-agent-log">
                  {result.execution_log.map((log, i) => (
                    <div key={i} className={`pa-log-item ${log.status}`}>
                      <span className="pa-log-step">{log.step}.</span>
                      <span className="pa-log-agent">{log.agent}</span>
                      <span className={`pa-log-status ${log.status}`}>{log.status}</span>
                    </div>
                  ))}
                </div>
                <p className="pa-process-time">处理耗时: {result.summary.processing_time_ms}ms</p>
              </section>
            </>
          ) : (
            <div className="pa-empty">
              <div className="pa-empty-icon">🎯</div>
              <h2>等待分析</h2>
              <p>填写你的状态和任务<br/>点击「获取优先级排序」</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
