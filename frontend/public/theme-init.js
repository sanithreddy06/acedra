// Applies the saved theme before first paint. Kept as a file (not inline) so the Content-Security-Policy
// can forbid inline scripts entirely.
try {
  if (localStorage.getItem('acedra-theme') === 'dark') document.documentElement.classList.add('dark');
} catch (e) { /* storage unavailable: keep the light theme */ }
