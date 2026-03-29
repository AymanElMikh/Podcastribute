const STEPS = [
  {
    n: '01',
    title: 'Upload your episode',
    body:  'Drop an MP3, paste a YouTube URL, or point to your RSS feed. We handle the rest.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    n: '02',
    title: 'AI learns your voice',
    body:  'Your voice profile captures vocabulary, tone, humor, and style — so every output sounds like you, not a robot.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    n: '03',
    title: '8 formats in 90 seconds',
    body:  'Twitter thread, LinkedIn post, newsletter section, blog post, YouTube description, quote cards, short-video scripts, email sequence — all ready to publish.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

export function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="relative py-24 px-6 overflow-hidden"
      aria-labelledby="how-heading"
    >
      {/* Subtle top border */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-24 bg-gradient-to-b from-transparent to-border-subtle" aria-hidden="true" />

      <div className="max-w-5xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-16">
          <p className="text-xs text-amber uppercase tracking-widest font-medium mb-3">How it works</p>
          <h2
            id="how-heading"
            className="font-display text-4xl sm:text-5xl font-bold text-primary leading-tight"
          >
            Three steps. Eight formats.
          </h2>
        </div>

        {/* Steps */}
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6">
          {/* Connecting line (desktop only) */}
          <div
            aria-hidden="true"
            className="hidden md:block absolute top-10 left-[calc(16.67%+1.5rem)] right-[calc(16.67%+1.5rem)] h-px"
            style={{ background: 'linear-gradient(to right, var(--color-amber), transparent 50%, var(--color-amber))' }}
          />

          {STEPS.map(({ n, title, body, icon }) => (
            <div key={n} className="relative flex flex-col items-center text-center gap-4">
              {/* Number + icon */}
              <div className="relative">
                <div className="size-20 rounded-2xl bg-bg-elevated border border-border-subtle flex items-center justify-center text-amber">
                  {icon}
                </div>
                <span className="absolute -top-3 -right-3 font-display text-5xl font-bold text-amber/10 leading-none select-none">
                  {n}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-primary font-display">{title}</h3>
              <p className="text-sm text-secondary leading-relaxed max-w-xs">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

HowItWorksSection.displayName = 'HowItWorksSection'
