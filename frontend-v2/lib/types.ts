/* ─────────────────────────────────────────────────────────────
   Core domain types — mirrored from FastAPI backend schemas
   ───────────────────────────────────────────────────────────── */

export type Plan = 'free' | 'starter' | 'creator' | 'studio'

export type EpisodeStatus =
  | 'queued'
  | 'transcribing'
  | 'detecting'
  | 'generating'
  | 'ready'
  | 'error'

export type SourceType = 'upload' | 'youtube' | 'rss'

export interface User {
  id: string
  email: string
  plan: Plan
  episodesThisMonth: number
  planLimit: number | null
  planResetAt: string
  voiceProfileId?: string
}

export interface Episode {
  id: string
  title: string
  sourceType: SourceType
  sourceUrl?: string
  durationSeconds?: number
  status: EpisodeStatus
  errorMessage?: string
  createdAt: string
  processingCompletedAt?: string
}

export interface Moment {
  id: string
  startTime: string
  endTime: string
  text: string
  momentType: string
  shareabilityScore: number
  oneLineHook: string
}

/* ─────────────────────────────────────────────────────────────
   Content format types
   ───────────────────────────────────────────────────────────── */

export interface TwitterContent {
  mainThread: string[]
  standaloneHooks: string[]
  listenTweet: string
}

export interface LinkedInContent {
  post: string
  carouselOutline: string[]
  postHooks: string[]
}

export interface NewsletterContent {
  sectionTitle: string
  sectionBody: string
  subjectLines: string[]
  previewText: string
}

export interface VideoClip {
  startTime: string
  endTime: string
  hook: string
  scriptNote: string
  platform: 'tiktok' | 'reels' | 'shorts'
}

export interface ShortVideoContent {
  clips: VideoClip[]
}

export interface BlogContent {
  title: string
  metaDescription: string
  outline: string[]
  body: string
  internalLinkSuggestions: string[]
  targetKeywords: string[]
}

export interface YouTubeChapter {
  time: string
  title: string
}

export interface YouTubeContent {
  description: string
  chapters: YouTubeChapter[]
  tags: string[]
  endScreenScript: string
}

export interface QuoteCard {
  text: string
  attribution: string
  backgroundSuggestion: string
  caption: string
}

export interface QuoteCardsContent {
  quotes: QuoteCard[]
}

export interface EmailItem {
  subject: string
  previewText: string
  body: string
  sendDay: number
  purpose: 'announce' | 'insight' | 'cta'
}

export interface EmailContent {
  emails: EmailItem[]
}

export interface ContentPack {
  twitter: TwitterContent | null
  linkedin: LinkedInContent | null
  newsletter: NewsletterContent | null
  shortVideo: ShortVideoContent | null
  blogPost: BlogContent | null
  youtube: YouTubeContent | null
  quoteCards: QuoteCardsContent | null
  emailSequence: EmailContent | null
}

/* ─────────────────────────────────────────────────────────────
   Streaming
   ───────────────────────────────────────────────────────────── */

export interface StreamEvent {
  type: string
  data: Record<string, unknown>
  label: string
  timestamp: string
}

/* ─────────────────────────────────────────────────────────────
   Voice
   ───────────────────────────────────────────────────────────── */

export interface VoiceProfile {
  vocabularyLevel: string
  sentenceStyle: string
  humorLevel: string
  twitterStyle: string
  linkedinStyle: string
  signaturePhrases: string[]
  topics: string[]
  wordsToAvoid: string[]
  toneAdjectives: string[]
  defaultCtaStyle: string
}

/* ─────────────────────────────────────────────────────────────
   API
   ───────────────────────────────────────────────────────────── */

export class APIError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export type PublishStatus = 'sent' | 'failed' | 'scheduled'

export interface PublishResult {
  [platform: string]: PublishStatus
}
