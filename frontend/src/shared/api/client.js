// 开发环境走同源 `/api`，由 Vite 代理到后端，避免浏览器用 localhost 与 API 用 127.0.0.1（或相反）导致连接失败。
// 生产构建请在环境变量中设置 VITE_API_BASE_URL 为真实后端地址。
const API_BASE = import.meta.env.DEV
  ? ''
  : (import.meta.env.VITE_API_BASE_URL || '');

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function formatApiDetail(detail) {
  if (detail == null) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'object' && item?.msg ? item.msg : JSON.stringify(item)))
      .join('；');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return JSON.stringify(detail);
}

export async function apiRequest(path, { method = 'GET', token, body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new ApiError(
      `无法连接后端${API_BASE ? ` ${API_BASE}` : '（同源 /api，经 Vite 代理）'}（请确认 assessment-api 已在 8100 端口运行；生产环境请设置 VITE_API_BASE_URL）`,
      0,
      { cause: String(e) }
    );
  }

  let payload = null;
  try {
    payload = await res.json();
  } catch (_) {
    payload = null;
  }
  if (!res.ok) {
    const msg = formatApiDetail(payload?.detail) || `API error ${res.status}`;
    throw new ApiError(msg, res.status, payload);
  }
  return payload;
}

export { API_BASE };
