import { apiRequest } from './client';

export function priorityHealth() {
  return apiRequest('/api/priority/health');
}

export function prioritize(payload) {
  return apiRequest('/api/priority/prioritize', { method: 'POST', body: payload });
}

export function agentsStatus() {
  return apiRequest('/api/priority/agents/status');
}
