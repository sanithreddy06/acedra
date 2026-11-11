import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import { api, setUnauthorizedHandler, tokens } from './api';
import type { Me, Role, TokenResponse } from '../types/api';

export type { Me, Role, University } from '../types/api';

interface AuthState {
  me: Me | null; ready: boolean;
  signIn: (email: string, password: string) => Promise<Me>;
  acceptTokens: (d: TokenResponse) => void;
  signOut: () => Promise<void>;
  hasModule: (m: string) => boolean;
}
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setUnauthorizedHandler(() => setMe(null));
    if (!tokens.access) { setReady(true); return; }
    api.get<Me>('/auth/me').then(setMe).catch(() => tokens.clear()).finally(() => setReady(true));
  }, []);

  const acceptTokens = useCallback((d: TokenResponse) => {
    tokens.set(d.access_token, d.refresh_token);
    setMe(d.user);
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const d = await api.post<TokenResponse>('/auth/login', { email, password });
    acceptTokens(d);
    return d.user;
  }, [acceptTokens]);

  const signOut = useCallback(async () => {
    try { await api.post('/auth/logout'); } catch { /* already signed out */ }
    tokens.clear();
    setMe(null);
  }, []);

  const hasModule = useCallback((m: string) => !!me?.university?.enabled_modules?.includes(m), [me]);

  return <Ctx.Provider value={{ me, ready, signIn, acceptTokens, signOut, hasModule }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

export function homeFor(role: Role) {
  return role === 'platform_admin' || role === 'platform_employee' ? '/platform' : '/app';
}
