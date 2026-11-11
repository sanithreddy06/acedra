/** ACEDRA design tokens — colours resolve to CSS variables so light and dark themes share one system. */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: v('paper'), surface: v('surface'), sunken: v('sunken'), line: v('line'), 'line-strong': v('line-strong'),
        ink: v('ink'), muted: v('muted'), faint: v('faint'),
        forest: v('forest'), 'forest-soft': v('forest-soft'), olive: v('olive'), bronze: v('bronze'),
        'bronze-soft': v('bronze-soft'), danger: v('danger'), 'danger-soft': v('danger-soft'),
        ok: v('ok'), 'ok-soft': v('ok-soft'), caution: v('caution'), 'caution-soft': v('caution-soft'),
        'on-forest': v('on-forest'),
      },
      fontFamily: {
        sans: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Newsreader', 'ui-serif', 'Georgia', 'serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      borderRadius: { DEFAULT: '6px', md: '6px', lg: '10px' },
      boxShadow: {
        pop: '0 1px 2px rgb(var(--shadow) / 0.06), 0 8px 24px -6px rgb(var(--shadow) / 0.14)',
        hair: '0 1px 0 rgb(var(--shadow) / 0.04)',
      },
      maxWidth: { content: '76rem', prose: '42rem' },
    },
  },
  plugins: [],
};
