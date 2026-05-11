import { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../../shared/api/client';

// 测试专属：调用 backend/autogen 生成多智能体对话数据，并浏览本地输出。
export default function AIDataGenerator() {
  const [mode, setMode] = useState('timeline');
  const [smokeTest, setSmokeTest] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [estimateCost, setEstimateCost] = useState(false);
  const [onlyGroups, setOnlyGroups] = useState('');
  const [configFile, setConfigFile] = useState('configs/oai_config_list.json');

  const [jobs, setJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [log, setLog] = useState('');
  const [error, setError] = useState('');

  const [path, setPath] = useState('');
  const [browseData, setBrowseData] = useState(null);
  const [filePreview, setFilePreview] = useState({ path: '', content: '' });
  const pollRef = useRef(null);

  async function api(p, opts = {}) {
    const res = await fetch(`${API_BASE}${p}`, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    const ct = res.headers.get('content-type') || '';
    const data = ct.includes('application/json') ? await res.json() : await res.text();
    if (!res.ok) throw new Error(typeof data === 'string' ? data : data?.detail || `HTTP ${res.status}`);
    return data;
  }

  async function loadBrowse(p = path) {
    try {
      const data = await api(`/api/autogen/browse?path=${encodeURIComponent(p)}`);
      setBrowseData(data);
      setPath(data.path || '');
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  async function loadJobs() {
    try {
      const data = await api('/api/autogen/jobs');
      setJobs(data);
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    loadBrowse('');
    loadJobs();
  }, []);

  async function pollJob(id) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const j = await api(`/api/autogen/jobs/${id}`);
        setCurrentJob(j);
        const text = await api(`/api/autogen/jobs/${id}/log?tail=400`);
        setLog(typeof text === 'string' ? text : JSON.stringify(text));
        if (j.status !== 'running') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          loadJobs();
          // Refresh the browser at the current path so partial outputs become
          // visible immediately, whether the job succeeded, failed, or was cancelled.
          loadBrowse(path);
        }
      } catch (e) {
        // ignore
      }
    }, 1500);
  }

  useEffect(() => () => pollRef.current && clearInterval(pollRef.current), []);

  async function runJob() {
    setError('');
    setLog('');
    try {
      const data = await api('/api/autogen/run', {
        method: 'POST',
        body: {
          mode,
          smoke_test: smokeTest,
          dry_run: dryRun,
          estimate_cost: estimateCost,
          only_groups: onlyGroups || null,
          config_list_file: configFile,
        },
      });
      setCurrentJob({ id: data.job_id, status: 'running', cmd: data.cmd });
      pollJob(data.job_id);
      loadJobs();
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  async function cancelJob(id) {
    if (!id) return;
    if (!window.confirm('取消该运行任务？已写入的部分输出会保留在 runs/ 下，可稍后手动删除。')) return;
    try {
      await api(`/api/autogen/jobs/${id}/cancel`, { method: 'POST' });
      // poller will pick up the new status
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  async function deleteJob(id) {
    if (!id) return;
    if (!window.confirm('删除该任务记录及其所有保存的文件？此操作不可恢复。')) return;
    try {
      await api(`/api/autogen/jobs/${id}`, { method: 'DELETE' });
      if (currentJob?.id === id) {
        setCurrentJob(null);
        setLog('');
      }
      await loadJobs();
      await loadBrowse('');
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  async function openEntry(entry) {
    if (entry.type === 'dir') {
      loadBrowse(entry.path);
    } else {
      try {
        const text = await api(`/api/autogen/file?path=${encodeURIComponent(entry.path)}`);
        setFilePreview({ path: entry.path, content: typeof text === 'string' ? text : JSON.stringify(text, null, 2) });
      } catch (e) {
        setError(String(e.message || e));
      }
    }
  }

  async function revealInExplorer(p) {
    try {
      await api(`/api/autogen/reveal?path=${encodeURIComponent(p)}`, { method: 'POST' });
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  function downloadFile(p) {
    window.open(`${API_BASE}/api/autogen/download?path=${encodeURIComponent(p)}`, '_blank');
  }

  const crumbs = (path || '').split('/').filter(Boolean);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>🧪 AI 生成数据（测试专属）</h1>
        <div style={{ color: '#666', marginTop: 6 }}>
          调用 <code>backend/autogen</code> 多智能体群聊数据生成器。每次运行保存到 <code>autogen/runs/&lt;job_id&gt;/</code>，其下分为 <code>logs/</code>（运行日志）与 <code>data/</code>（生成数据）两个子目录。任务可中途取消，已生成的部分会保留在硬盘上，需要时通过列表里的「删除」按钮手动清除。
        </div>
      </div>

      {error && (
        <div style={{ background: '#fee', border: '1px solid #f99', padding: 10, borderRadius: 6, marginBottom: 12 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card" style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>运行参数</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', rowGap: 10, columnGap: 10, alignItems: 'center' }}>
            <label>模式</label>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="timeline">timeline_v2 (推荐)</option>
              <option value="legacy">legacy</option>
            </select>

            <label>配置文件</label>
            <input value={configFile} onChange={(e) => setConfigFile(e.target.value)} />

            <label>仅运行分组</label>
            <input value={onlyGroups} onChange={(e) => setOnlyGroups(e.target.value)} placeholder="例: timeline_positive_4 (可选)" />

            <label>选项</label>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <label><input type="checkbox" checked={smokeTest} onChange={(e) => setSmokeTest(e.target.checked)} /> smoke-test</label>
              <label><input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} /> dry-run</label>
              <label><input type="checkbox" checked={estimateCost} onChange={(e) => setEstimateCost(e.target.checked)} /> estimate-cost</label>
            </div>
          </div>

          <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={runJob} disabled={currentJob?.status === 'running'}>
              {currentJob?.status === 'running' ? '运行中…' : '🚀 启动生成'}
            </button>
            {currentJob?.status === 'running' && (
              <button className="btn btn-outline" style={{ borderColor: '#c00', color: '#c00' }} onClick={() => cancelJob(currentJob.id)}>
                ⛔ 取消当前任务
              </button>
            )}
            <button className="btn btn-outline" onClick={loadJobs}>刷新任务列表</button>
          </div>

          <div style={{ marginTop: 16 }}>
            <h4 style={{ margin: '0 0 6px' }}>历史任务</h4>
            <div style={{ maxHeight: 160, overflow: 'auto', border: '1px solid #eee', borderRadius: 6 }}>
              {jobs.length === 0 && <div style={{ padding: 10, color: '#888' }}>暂无任务</div>}
              {jobs.map((j) => (
                <div
                  key={j.id}
                  onClick={() => { setCurrentJob(j); pollJob(j.id); }}
                  style={{ padding: 8, borderBottom: '1px solid #f3f3f3', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}
                >
                  <span style={{ fontFamily: 'monospace' }}>{j.id}</span>
                  <span style={{ color: j.status === 'success' ? 'green' : j.status === 'failed' ? 'crimson' : j.status === 'cancelled' ? '#999' : '#0a6' }}>{j.status}</span>
                  <span style={{ color: '#888', fontSize: 12 }}>{j.started_at?.slice(11, 19)}</span>
                  <span style={{ display: 'flex', gap: 4 }}>
                    {j.status === 'running' ? (
                      <button className="btn btn-outline" style={{ padding: '2px 6px', fontSize: 11, color: '#c00', borderColor: '#c00' }} onClick={(ev) => { ev.stopPropagation(); cancelJob(j.id); }}>取消</button>
                    ) : (
                      <button className="btn btn-outline" style={{ padding: '2px 6px', fontSize: 11 }} onClick={(ev) => { ev.stopPropagation(); deleteJob(j.id); }}>删除</button>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card" style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>运行日志 {currentJob && <small style={{ color: '#888' }}>({currentJob.id})</small>}</h3>
          <pre style={{ background: '#0e1116', color: '#d6deeb', padding: 12, borderRadius: 6, maxHeight: 320, overflow: 'auto', fontSize: 12, whiteSpace: 'pre-wrap' }}>
            {log || '（暂无输出）'}
          </pre>
        </div>
      </div>

      <div className="card" style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 16, marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h3 style={{ margin: 0 }}>📁 已保存运行结果</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="btn btn-outline" onClick={() => loadBrowse('')}>runs 根目录</button>
            {currentJob?.id && (
              <>
                <button className="btn btn-outline" onClick={() => loadBrowse(`${currentJob.id}/data`)}>📊 当前任务 data/</button>
                <button className="btn btn-outline" onClick={() => loadBrowse(`${currentJob.id}/logs`)}>📜 当前任务 logs/</button>
              </>
            )}
            <button className="btn btn-outline" onClick={() => loadBrowse(path)}>刷新</button>
            <button className="btn btn-outline" onClick={() => revealInExplorer(path)}>🪟 在资源管理器中打开</button>
          </div>
        </div>

        <div style={{ marginBottom: 10, fontFamily: 'monospace', fontSize: 13 }}>
          <span style={{ cursor: 'pointer', color: '#06f' }} onClick={() => loadBrowse('')}>runs/</span>
          {crumbs.map((c, i) => (
            <span key={i}>
              <span style={{ cursor: 'pointer', color: '#06f' }} onClick={() => loadBrowse(crumbs.slice(0, i + 1).join('/'))}>{c}</span>
              {i < crumbs.length - 1 ? '/' : ''}
            </span>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 12 }}>
          <div style={{ border: '1px solid #eee', borderRadius: 6, maxHeight: 420, overflow: 'auto' }}>
            {browseData?.parent !== null && browseData?.parent !== undefined && (
              <div onClick={() => loadBrowse(browseData.parent)} style={{ padding: 8, cursor: 'pointer', borderBottom: '1px solid #f3f3f3' }}>📂 ..</div>
            )}
            {browseData?.entries?.map((e) => (
              <div
                key={e.path}
                onClick={() => openEntry(e)}
                style={{ padding: 8, cursor: 'pointer', borderBottom: '1px solid #f3f3f3', display: 'flex', justifyContent: 'space-between', gap: 8 }}
              >
                <span>{e.type === 'dir' ? '📁' : '📄'} {e.name}</span>
                <span style={{ display: 'flex', gap: 6 }}>
                  {e.type === 'file' && (
                    <>
                      <button className="btn btn-outline" style={{ padding: '2px 6px', fontSize: 11 }} onClick={(ev) => { ev.stopPropagation(); downloadFile(e.path); }}>下载</button>
                      <button className="btn btn-outline" style={{ padding: '2px 6px', fontSize: 11 }} onClick={(ev) => { ev.stopPropagation(); revealInExplorer(e.path); }}>定位</button>
                    </>
                  )}
                  <span style={{ color: '#888', fontSize: 12, minWidth: 60, textAlign: 'right' }}>{e.size != null ? `${e.size}B` : ''}</span>
                </span>
              </div>
            ))}
            {!browseData?.entries?.length && <div style={{ padding: 10, color: '#888' }}>空目录</div>}
          </div>

          <div>
            <div style={{ color: '#666', marginBottom: 6, fontSize: 12 }}>{filePreview.path || '点击文件可在此预览'}</div>
            <pre style={{ background: '#fafafa', border: '1px solid #eee', borderRadius: 6, padding: 10, maxHeight: 420, overflow: 'auto', fontSize: 12, whiteSpace: 'pre-wrap' }}>
              {filePreview.content || '（无预览）'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
