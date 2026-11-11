import { preferencesAllowed, THEME_KEY } from './consent';

export function getTheme(): 'light' | 'dark' {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}
/** Applies the appearance; it is remembered only if the person allowed preference storage. */
export function setTheme(t: 'light' | 'dark') {
  document.documentElement.classList.toggle('dark', t === 'dark');
  if (!preferencesAllowed()) return;
  try { localStorage.setItem(THEME_KEY, t); } catch { /* ignore */ }
}
