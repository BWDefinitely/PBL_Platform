import { apiRequest } from './client';

// 静态模式：从 public/data/ 直接读取打包进前端的评测数据，无需后端服务。
// 在 .env 中设置 VITE_USE_STATIC=true 即可启用。
const USE_STATIC = import.meta.env.VITE_USE_STATIC === 'true';

// 静态文件相对站点根目录，开发与生产构建（Vite）都会把 public/ 暴露在根路径。
const STATIC_BASE = `${import.meta.env.BASE_URL || '/'}data`.replace(/\/+$/, '');

async function fetchStatic(relativePath) {
  const url = `${STATIC_BASE}${relativePath}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`静态数据加载失败：${url}（${res.status}）`);
  }
  return res.json();
}

export function getStudents(token) {
  if (USE_STATIC) return fetchStatic('/students.json');
  return apiRequest('/api/assessments/students', { token });
}

export function getStudentMilestones(token, studentCode) {
  if (USE_STATIC) {
    return fetchStatic(`/students/${encodeURIComponent(studentCode)}/milestones.json`);
  }
  return apiRequest(
    `/api/assessments/students/${encodeURIComponent(studentCode)}/milestones`,
    { token },
  );
}

export function getStudentMilestoneDetail(token, studentCode, milestone) {
  if (USE_STATIC) {
    return fetchStatic(
      `/students/${encodeURIComponent(studentCode)}/${encodeURIComponent(milestone)}.json`,
    );
  }
  return apiRequest(
    `/api/assessments/students/${encodeURIComponent(studentCode)}/milestones/${encodeURIComponent(milestone)}`,
    { token },
  );
}

export function getReports(token) {
  if (USE_STATIC) return fetchStatic('/reports.json');
  return apiRequest('/api/reports', { token });
}

// 干预记录在静态数据包里没有，静态模式下返回空数组，UI 会回落到「暂无」状态。
export function createIntervention(token, payload) {
  if (USE_STATIC) {
    return Promise.resolve({ id: Date.now(), ...payload, status: payload.status || 'pending' });
  }
  return apiRequest('/api/interventions', { method: 'POST', token, body: payload });
}

export function getInterventions(token, params = {}) {
  if (USE_STATIC) return Promise.resolve([]);
  const q = new URLSearchParams();
  if (params.student_id) q.set('student_id', params.student_id);
  if (params.action_type) q.set('action_type', params.action_type);
  if (params.status) q.set('status', params.status);
  if (params.limit != null) q.set('limit', String(params.limit));
  const qs = q.toString();
  return apiRequest(`/api/interventions${qs ? `?${qs}` : ''}`, { token });
}

export function updateInterventionStatus(token, id, status) {
  if (USE_STATIC) return Promise.resolve({ id, status });
  return apiRequest(`/api/interventions/${id}`, { method: 'PATCH', token, body: { status } });
}
