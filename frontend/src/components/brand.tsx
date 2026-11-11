/** ACEDRA identity: mark, wordmark and copy constants. Colours come from the design tokens. */
export const BRAND = {
  name: 'ACEDRA',
  tagline: 'University Intelligence. Connected.',
  description:
    'ACEDRA is a configurable university intelligence platform that connects student academic analytics, early-warning systems, personalised recommendations, skill-gap analysis, AI assistance and intervention tracking into one institutional workspace.',
};

/** The mark: an open "A" whose crossbar is a link between two nodes. */
export function AcedraMark({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden className={className}>
      <rect width="32" height="32" rx="8" className="fill-forest" />
      <g fill="none" strokeLinecap="round" strokeLinejoin="round" className="stroke-paper">
        <path d="M8.5 24.5 16 7.5l7.5 17" strokeWidth="3" />
        <path d="M12.2 18.6h7.6" strokeWidth="2" />
      </g>
      <circle cx="12.2" cy="18.6" r="2" className="fill-paper" />
      <circle cx="19.8" cy="18.6" r="2" className="fill-paper" />
    </svg>
  );
}

/** Mark + letter-spaced wordmark. `tagline` adds the descriptor beneath the name. */
export function AcedraWordmark({ size = 24, tagline = false, className }: { size?: number; tagline?: boolean; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className || ''}`}>
      <AcedraMark size={size} />
      <span className="leading-none">
        <span className="block font-semibold tracking-[0.14em] text-ink" style={{ fontSize: Math.round(size * 0.6) }} aria-label="ACEDRA">ACEDRA</span>
        {tagline && <span className="mt-1 block text-[11px] tracking-normal text-muted">{BRAND.tagline}</span>}
      </span>
    </span>
  );
}
