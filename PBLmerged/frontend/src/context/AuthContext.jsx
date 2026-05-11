import { createContext, useContext, useMemo, useState } from 'react';
import { loginApi, registerApi } from '../shared/api/auth';

const AuthContext = createContext(null);
const STORAGE_KEY = 'pbl_auth_state_v1';
const PREVIEW_ENABLED = import.meta.env.DEV && (import.meta.env.VITE_AUTH_PREVIEW ?? 'true') === 'true';
const PREVIEW_DEFAULT_ROLE = import.meta.env.VITE_PREVIEW_ROLE === 'student' ? 'student' : 'teacher';

function getPreviewAuthState() {
  return {
    token: '__preview__',
    refreshToken: null,
    role: PREVIEW_DEFAULT_ROLE,
    email: 'preview@local',
    isPreview: true,
  };
}

function loadStoredAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (!parsed) return null;
    return {
      ...parsed,
      isPreview: Boolean(parsed.isPreview),
    };
  } catch (_) {
    return null;
  }
}

export function AuthProvider({ children }) {
  const initial = loadStoredAuth();
  const [authState, setAuthState] = useState(
    initial || (PREVIEW_ENABLED ? getPreviewAuthState() : { token: null, refreshToken: null, role: null, email: null, isPreview: false })
  );

  const persist = (next) => {
    setAuthState(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  const login = async (payload) => {
    const res = await loginApi(payload);
    persist({
      token: res.access_token,
      refreshToken: res.refresh_token,
      role: res.role,
      email: payload.email,
      isPreview: false,
    });
    return res;
  };

  const register = async (payload) => {
    const res = await registerApi(payload);
    persist({
      token: res.access_token,
      refreshToken: res.refresh_token,
      role: res.role,
      email: payload.email,
      isPreview: false,
    });
    return res;
  };

  const switchPreviewRole = (nextRole) => {
    if (!authState.isPreview) return;
    if (!['teacher', 'student'].includes(nextRole)) return;
    persist({
      ...authState,
      role: nextRole,
    });
  };

  const logout = () => {
    if (PREVIEW_ENABLED) {
      persist(getPreviewAuthState());
      return;
    }
    const next = { token: null, refreshToken: null, role: null, email: null, isPreview: false };
    setAuthState(next);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(
    () => ({
      ...authState,
      isAuthenticated: Boolean(authState.token),
      isPreviewEnabled: PREVIEW_ENABLED,
      login,
      register,
      logout,
      switchPreviewRole,
    }),
    [authState]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
