import { apiRequest } from './client';

export function loginApi(payload) {
  return apiRequest('/api/auth/login', { method: 'POST', body: payload });
}

export function registerApi(payload) {
  return apiRequest('/api/auth/register', { method: 'POST', body: payload });
}
