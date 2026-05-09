import { useState } from 'react';
import { students } from '../../data/mockData';

const currentStudent = students[0];

const initialFiles = [
  {
    id: 'f1',
    name: '需求分析报告_v3.0.docx',
    type: 'document',
    category: '需求文档',
    size: '2.4 MB',
    uploadDate: '2026-03-14',
    uploader: 's1',
    description: '基于用户调研和文献综述整理的需求分析报告最终版',
    status: 'approved',
  },
  {
    id: 'f2',
    name: '文献综述_AI教育应用.pdf',
    type: 'document',
    category: '研究资料',
    size: '1.8 MB',
    uploadDate: '2026-03-09',
    uploader: 's1',
    description: '近5年AI在教育领域应用的文献综述报告',
    status: 'approved',
  },
  {
    id: 'f3',
    name: '第三次讨论_会议纪要.pdf',
    type: 'meeting',
    category: '会议纪要',
    size: '520 KB',
    uploadDate: '2026-03-19',
    uploader: 's1',
    description: '系统架构方案讨论会议纪要（AI生成）',
    status: 'approved',
  },
  {
    id: 'f4',
    name: '推荐算法调研笔记.md',
    type: 'document',
    category: '研究资料',
    size: '340 KB',
    uploadDate: '2026-03-22',
    uploader: 's1',
    description: '主流推荐算法对比分析笔记',
    status: 'pending',
  },
];

const fileCategories = ['全部', '需求文档', '研究资料', '会议纪要', '设计文档', '代码文件', '其他'];

export default function FileUpload() {
  const [files, setFiles] = useState(initialFiles);
  const [filter, setFilter] = useState('全部');
  const [showUpload, setShowUpload] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    name: '',
    category: '需求文档',
    description: '',
    file: null,
  });
  const [dragActive, setDragActive] = useState(false);

  const filteredFiles = filter === '全部' ? files : files.filter(f => f.category === filter);

  const getFileIcon = (type, name) => {
    if (name.endsWith('.pdf')) return '📕';
    if (name.endsWith('.docx') || name.endsWith('.doc')) return '📘';
    if (name.endsWith('.md')) return '📝';
    if (name.endsWith('.pptx') || name.endsWith('.ppt')) return '📙';
    if (name.endsWith('.xlsx') || name.endsWith('.xls')) return '📗';
    if (name.endsWith('.zip') || name.endsWith('.rar')) return '📦';
    if (name.endsWith('.png') || name.endsWith('.jpg')) return '🖼️';
    if (type === 'meeting') return '📋';
    return '📄';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved': return <span className="badge completed">已确认</span>;
      case 'pending': return <span className="badge active">待审核</span>;
      case 'rejected': return <span className="badge high">需修改</span>;
      default: return null;
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setUploadForm(prev => ({ ...prev, name: file.name, file }));
      setShowUpload(true);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadForm(prev => ({ ...prev, name: file.name, file }));
    }
  };

  const handleUpload = () => {
    if (!uploadForm.name) return;
    const newFile = {
      id: `f${files.length + 1}`,
      name: uploadForm.name,
      type: uploadForm.category === '会议纪要' ? 'meeting' : 'document',
      category: uploadForm.category,
      size: uploadForm.file ? `${(uploadForm.file.size / 1024 / 1024).toFixed(1)} MB` : '未知',
      uploadDate: new Date().toISOString().split('T')[0],
      uploader: currentStudent.id,
      description: uploadForm.description,
      status: 'pending',
    };
    setFiles([newFile, ...files]);
    setShowUpload(false);
    setUploadForm({ name: '', category: '需求文档', description: '', file: null });
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="page-title">📁 文件管理</div>
            <div className="page-subtitle">上传和管理项目相关文档、会议纪要等工作内容</div>
          </div>
          <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
            ⬆️ 上传文件
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="stats-grid" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <div className="stat-icon primary">📄</div>
          <div className="stat-content">
            <div className="stat-value">{files.length}</div>
            <div className="stat-label">总文件数</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-content">
            <div className="stat-value">{files.filter(f => f.status === 'approved').length}</div>
            <div className="stat-label">已确认</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏳</div>
          <div className="stat-content">
            <div className="stat-value">{files.filter(f => f.status === 'pending').length}</div>
            <div className="stat-label">待审核</div>
          </div>
        </div>
      </div>

      {/* 上传弹窗 */}
      {showUpload && (
        <div className="card" style={{ marginBottom: 20, border: '2px solid var(--primary-light)', background: 'linear-gradient(135deg, var(--card), var(--primary-50))' }}>
          <div className="card-header">
            <div className="card-title">⬆️ 上传新文件</div>
            <button className="btn btn-sm btn-outline" onClick={() => setShowUpload(false)}>✕ 关闭</button>
          </div>

          {/* 拖拽上传区 */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border)'}`,
              borderRadius: 'var(--radius)',
              padding: '32px 20px',
              textAlign: 'center',
              background: dragActive ? 'var(--primary-50)' : 'white',
              marginBottom: 16,
              transition: 'all 0.2s ease',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('fileInput').click()}
          >
            <div style={{ fontSize: 40, marginBottom: 8 }}>
              {uploadForm.file ? '✅' : '📂'}
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
              {uploadForm.file ? uploadForm.name : '拖拽文件到此处，或点击选择文件'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              支持 PDF、Word、Markdown、PPT、图片等格式
            </div>
            <input
              id="fileInput"
              type="file"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.md,.txt,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.zip"
            />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">文件分类</label>
              <select
                className="form-select"
                value={uploadForm.category}
                onChange={e => setUploadForm({ ...uploadForm, category: e.target.value })}
              >
                {fileCategories.filter(c => c !== '全部').map(c => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">文件名称</label>
              <input
                className="form-input"
                value={uploadForm.name}
                onChange={e => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="输入文件名称"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">文件描述（可选）</label>
            <textarea
              className="form-textarea"
              style={{ minHeight: 70 }}
              value={uploadForm.description}
              onChange={e => setUploadForm({ ...uploadForm, description: e.target.value })}
              placeholder="简要描述文件内容和用途..."
            />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={handleUpload}>
              ✅ 确认上传
            </button>
            <button className="btn btn-outline" onClick={() => setShowUpload(false)}>取消</button>
          </div>
        </div>
      )}

      {/* 分类筛选 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {fileCategories.map(cat => (
          <button
            key={cat}
            className={`btn btn-sm ${filter === cat ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilter(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* 文件列表 */}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>文件名</th>
              <th>分类</th>
              <th>大小</th>
              <th>上传日期</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredFiles.map(file => (
              <tr key={file.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 22 }}>{getFileIcon(file.type, file.name)}</span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{file.name}</div>
                      {file.description && (
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{file.description}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td><span className="tag">{file.category}</span></td>
                <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{file.size}</td>
                <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{file.uploadDate}</td>
                <td>{getStatusBadge(file.status)}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-sm btn-secondary">📥 下载</button>
                    <button className="btn btn-sm btn-outline">🔄 更新</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredFiles.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📂</div>
            <p>该分类下暂无文件</p>
          </div>
        )}
      </div>
    </div>
  );
}
