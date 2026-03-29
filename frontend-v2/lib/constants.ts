import type { Plan } from './types'

/* ─────────────────────────────────────────────────────────────
   Content format metadata
   ───────────────────────────────────────────────────────────── */

export const FORMATS = [
  { key: 'twitter',       label: 'Twitter / X',      icon: '𝕏',  platform: 'twitter'   },
  { key: 'linkedin',      label: 'LinkedIn',          icon: 'in', platform: 'linkedin'  },
  { key: 'newsletter',    label: 'Newsletter',        icon: '✉',  platform: 'newsletter'},
  { key: 'shortVideo',    label: 'Short Video',       icon: '▶',  platform: 'video'     },
  { key: 'blogPost',      label: 'Blog Post',         icon: '✍',  platform: 'blog'      },
  { key: 'youtube',       label: 'YouTube',           icon: '▷',  platform: 'youtube'   },
  { key: 'quoteCards',    label: 'Quote Cards',       icon: '❝',  platform: 'quotes'    },
  { key: 'emailSequence', label: 'Email Sequence',    icon: '📧', platform: 'email'     },
] as const

export type FormatKey = (typeof FORMATS)[number]['key']

/* ─────────────────────────────────────────────────────────────
   Plan config
   ───────────────────────────────────────────────────────────── */

export const PLAN_LIMITS: Record<Plan, number | null> = {
  free:    1,
  starter: 4,
  creator: 15,
  studio:  null,
}

export const PLAN_LABELS: Record<Plan, string> = {
  free:    'Free',
  starter: 'Starter',
  creator: 'Creator',
  studio:  'Studio',
}

export const PLAN_PRICES: Record<Exclude<Plan, 'free'>, number> = {
  starter: 49,
  creator: 149,
  studio:  399,
}

/* ─────────────────────────────────────────────────────────────
   Episode status labels + colors
   ───────────────────────────────────────────────────────────── */

export const STATUS_LABELS = {
  queued:       'Queued',
  transcribing: 'Transcribing',
  detecting:    'Detecting moments',
  generating:   'Generating content',
  ready:        'Ready',
  error:        'Error',
} as const

export const STATUS_COLORS = {
  queued:       'text-secondary',
  transcribing: 'text-amber',
  detecting:    'text-amber',
  generating:   'text-amber',
  ready:        'text-success',
  error:        'text-error',
} as const

/* ─────────────────────────────────────────────────────────────
   Processing step labels (SSE event → display label)
   ───────────────────────────────────────────────────────────── */

export const SSE_STEP_LABELS: Record<string, string> = {
  upload_received:     'Audio received',
  transcription_start: 'Transcribing audio…',
  transcription_done:  'Transcription complete',
  moments_detected:    'Found your best moments',
  generating_content:  'Generating content formats…',
  content_ready:       'All content ready!',
  error:               'Processing failed',
}

/* ─────────────────────────────────────────────────────────────
   Accepted audio MIME types
   ───────────────────────────────────────────────────────────── */

export const ACCEPTED_AUDIO_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp4',
  'audio/x-m4a',
  'audio/m4a',
] as const

export const MAX_UPLOAD_MB = 500
