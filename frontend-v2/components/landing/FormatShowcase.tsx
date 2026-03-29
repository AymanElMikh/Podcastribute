import { FORMATS } from '@/lib/constants'

const FORMAT_PREVIEWS: Record<string, string> = {
  twitter:        '"The one thing nobody talks about in podcasting is..."  🧵 Thread →',
  linkedin:       'Three years ago I made a decision that changed everything about how I record...',
  newsletter:     '**This week\'s insight:** After 200 episodes, here\'s what I\'ve learned about keeping listeners...',
  short_video:    'Hook (0–3s): "What if I told you podcasting is dead?" B-roll: waveform animation...',
  blog_post:      '# How to Turn One Podcast Episode Into a Week of Content\n\nMost podcasters are leaving 90% of their...',
  youtube:        'In this episode we explore [TOPIC]. Chapters:\n0:00 Intro\n2:14 The core insight...',
  quote_cards:    '"The best content you\'ll ever make is content you\'ve already made."',
  email_sequence: 'Subject: You need to hear this episode\n\nHey [first name], this week we recorded something special...',
}

// Responsive bento layout: each item spans different columns
const SPANS = [
  'md:col-span-2',   // twitter — wide
  'md:col-span-1',   // linkedin
  'md:col-span-1',   // newsletter
  'md:col-span-1',   // short_video
  'md:col-span-2',   // blog_post — wide
  'md:col-span-1',   // youtube
  'md:col-span-1',   // quote_cards
  'md:col-span-2',   // email — wide
]

export function FormatShowcase() {
  return (
    <section
      id="formats"
      className="relative py-24 px-6 bg-bg-elevated/40"
      aria-labelledby="formats-heading"
    >
      <div className="max-w-5xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-12">
          <p className="text-xs text-amber uppercase tracking-widest font-medium mb-3">8 formats</p>
          <h2
            id="formats-heading"
            className="font-display text-4xl sm:text-5xl font-bold text-primary leading-tight"
          >
            One episode.{' '}
            <span className="text-amber">Eight outputs.</span>
          </h2>
          <p className="text-secondary text-lg mt-4 max-w-xl mx-auto">
            Every format is written in your voice and ready to paste — no editing required.
          </p>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {FORMATS.map(({ key, label, icon }, i) => (
            <div
              key={key}
              className={`group relative overflow-hidden rounded-2xl border border-border-subtle bg-bg-base p-5 cursor-default transition-all duration-200 hover:border-amber/40 hover:bg-bg-elevated ${SPANS[i]}`}
            >
              {/* Amber glow on hover */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ background: 'radial-gradient(circle at 50% 0%, rgba(245,166,35,0.06) 0%, transparent 60%)' }}
              />

              {/* Header */}
              <div className="flex items-center gap-2.5 mb-3">
                <span className="text-xl" aria-hidden="true">{icon}</span>
                <span className="text-sm font-semibold text-primary">{label}</span>
              </div>

              {/* Preview text */}
              <p className="text-xs text-tertiary font-mono leading-relaxed line-clamp-3 whitespace-pre-line">
                {FORMAT_PREVIEWS[key]}
              </p>

              {/* Hover reveal badge */}
              <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <span className="text-[10px] font-medium text-amber bg-amber/10 px-2 py-0.5 rounded-full">
                  AI-generated
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

FormatShowcase.displayName = 'FormatShowcase'
