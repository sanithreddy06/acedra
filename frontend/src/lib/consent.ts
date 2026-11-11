/**
 * Browser-storage consent. ACEDRA sets no cookies and loads no trackers; the only optional item is the saved
 * appearance (`acedra-theme`). The choice itself is strictly necessary storage (see the Cookie Policy).
 */
export const CONSENT_KEY = 'acedra.cookie-consent';
export const THEME_KEY = 'acedra-theme';
const CONSENT_VERSION = 1;
const CHANGED = 'acedra:consent-changed';
const OPEN = 'acedra:open-cookie-preferences';

export interface ConsentChoice { version: number; preferences: boolean; decidedAt: string }

export function getConsent(): ConsentChoice | null {
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    const c = JSON.parse(raw) as Partial<ConsentChoice>;
    return c && c.version === CONSENT_VERSION && typeof c.preferences === 'boolean' && typeof c.decidedAt === 'string'
      ? (c as ConsentChoice) : null;
  } catch { return null; }
}

export const preferencesAllowed = () => getConsent()?.preferences === true;

export function saveConsent(preferences: boolean): ConsentChoice {
  const choice: ConsentChoice = { version: CONSENT_VERSION, preferences, decidedAt: new Date().toISOString() };
  try {
    localStorage.setItem(CONSENT_KEY, JSON.stringify(choice));
    if (preferences) {
      // Keep the appearance the person is currently using.
      localStorage.setItem(THEME_KEY, document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    } else {
      localStorage.removeItem(THEME_KEY);
    }
  } catch { /* storage unavailable: the choice applies to this page only */ }
  window.dispatchEvent(new CustomEvent(CHANGED, { detail: choice }));
  return choice;
}

export function onConsentChange(fn: (c: ConsentChoice) => void) {
  const h = (e: Event) => fn((e as CustomEvent<ConsentChoice>).detail);
  window.addEventListener(CHANGED, h);
  return () => window.removeEventListener(CHANGED, h);
}

/** Re-open the cookie preferences dialog from anywhere (footer links, legal pages). */
export const openCookiePreferences = () => window.dispatchEvent(new Event(OPEN));
export function onOpenCookiePreferences(fn: () => void) {
  window.addEventListener(OPEN, fn);
  return () => window.removeEventListener(OPEN, fn);
}
