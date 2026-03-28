/**
 * API client — thin wrappers around fetch for all backend calls.
 * All requests automatically attach the JWT from localStorage.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002";

// ---------------------------------------------------------------------------
// Core fetch helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    ...(options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? "Request failed");
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  plan: "free" | "starter" | "creator" | "studio";
  episodes_this_month: number;
}

export const auth = {
  register: (email: string, password: string) =>
    apiFetch<AuthResponse>("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    apiFetch<AuthResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => apiFetch<User>("/v1/auth/me"),
};

// ---------------------------------------------------------------------------
// Episodes
// ---------------------------------------------------------------------------

export type EpisodeStatus =
  | "queued"
  | "transcribing"
  | "detecting"
  | "generating"
  | "ready"
  | "error";

export interface Episode {
  id: string;
  title: string;
  source_type: "upload" | "youtube" | "rss";
  status: EpisodeStatus;
  duration_seconds: number | null;
  created_at: string;
  error_message: string | null;
}

export interface EpisodeList {
  items: Episode[];
  total: number;
}

export const episodes = {
  list: (page = 1, pageSize = 20) =>
    apiFetch<EpisodeList>(`/v1/episodes?page=${page}&page_size=${pageSize}`),

  get: (id: string) => apiFetch<Episode>(`/v1/episodes/${id}`),

  upload: (file: File, title: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title);
    return apiFetch<{ episode_id: string; status: string }>("/v1/episodes/upload", {
      method: "POST",
      body: fd,
    });
  },

  fromYouTube: (url: string) =>
    apiFetch<{ episode_id: string; status: string }>("/v1/episodes/youtube", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  fromRSS: (feedUrl: string, episodeIndex = 0) =>
    apiFetch<{ episode_id: string; status: string }>("/v1/episodes/rss", {
      method: "POST",
      body: JSON.stringify({ feed_url: feedUrl, episode_index: episodeIndex }),
    }),
};

// ---------------------------------------------------------------------------
// Content
// ---------------------------------------------------------------------------

export interface ContentPack {
  twitter?: TwitterContent;
  linkedin?: LinkedInContent;
  newsletter?: NewsletterContent;
  short_video?: ShortVideoContent;
  blog_post?: BlogPostContent;
  youtube?: YouTubeContent;
  quote_cards?: QuoteCardsContent;
  email_sequence?: EmailSequenceContent;
}

export interface TwitterContent {
  main_thread: string[];
  standalone_hooks: string[];
  listen_tweet: string;
  error?: string;
}

export interface LinkedInContent {
  post: string;
  carousel_outline: string[];
  post_hooks: string[];
  error?: string;
}

export interface NewsletterContent {
  section_title: string;
  section_body: string;
  subject_lines: string[];
  preview_text: string;
  error?: string;
}

export interface ShortVideoClip {
  start_time: string;
  end_time: string;
  hook: string;
  script_note: string;
  platform: string;
}

export interface ShortVideoContent {
  clips: ShortVideoClip[];
  error?: string;
}

export interface BlogPostContent {
  title: string;
  meta_description: string;
  outline: string[];
  body: string;
  internal_link_suggestions: string[];
  target_keywords: string[];
  error?: string;
}

export interface YouTubeChapter {
  time: string;
  title: string;
}

export interface YouTubeContent {
  description: string;
  chapters: YouTubeChapter[];
  tags: string[];
  end_screen_script: string;
  error?: string;
}

export interface QuoteCard {
  text: string;
  attribution: string;
  background_suggestion: string;
  caption: string;
}

export interface QuoteCardsContent {
  quotes: QuoteCard[];
  error?: string;
}

export interface EmailItem {
  subject: string;
  preview_text: string;
  body: string;
  send_day: number;
  purpose: string;
}

export interface EmailSequenceContent {
  emails: EmailItem[];
  error?: string;
}

export const content = {
  get: (episodeId: string) =>
    apiFetch<ContentPack>(`/v1/content/${episodeId}`),
};

// ---------------------------------------------------------------------------
// Voice
// ---------------------------------------------------------------------------

export interface VoiceProfile {
  vocabulary_level: string;
  sentence_style: string;
  humor_level: string;
  twitter_style: string;
  linkedin_style: string;
  signature_phrases: string[];
  topics: string[];
  words_to_avoid: string[];
  tone_adjectives: string[];
  default_cta_style: string;
}

export const voice = {
  get: () => apiFetch<VoiceProfile | null>("/v1/voice"),

  calibrateFromPosts: (posts: string[]) =>
    apiFetch<VoiceProfile>("/v1/voice/calibrate/posts", {
      method: "POST",
      body: JSON.stringify({ posts }),
    }),

  calibrateFromTranscripts: (transcripts: string[]) =>
    apiFetch<VoiceProfile>("/v1/voice/calibrate/transcripts", {
      method: "POST",
      body: JSON.stringify({ transcripts }),
    }),

  refine: (feedback: string) =>
    apiFetch<VoiceProfile>("/v1/voice/refine", {
      method: "PUT",
      body: JSON.stringify({ feedback }),
    }),

  update: (updates: Partial<VoiceProfile>) =>
    apiFetch<VoiceProfile>("/v1/voice", {
      method: "PUT",
      body: JSON.stringify(updates),
    }),
};

// ---------------------------------------------------------------------------
// Billing
// ---------------------------------------------------------------------------

export interface UsageInfo {
  episodes_this_month: number;
  limit: number | null;
  plan: string;
  reset_at: string;
}

export const billing = {
  usage: () => apiFetch<UsageInfo>("/v1/billing/usage"),

  checkout: (plan: "starter" | "creator" | "studio") =>
    apiFetch<{ url: string }>("/v1/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan }),
    }),

  portal: () =>
    apiFetch<{ url: string }>("/v1/billing/portal", { method: "POST" }),
};

// ---------------------------------------------------------------------------
// Publish
// ---------------------------------------------------------------------------

export const publish = {
  send: (
    episodeId: string,
    platforms: string[],
    contentOverrides?: Record<string, unknown>,
    scheduleAt?: string
  ) =>
    apiFetch<Record<string, string>>("/v1/publish", {
      method: "POST",
      body: JSON.stringify({
        episode_id: episodeId,
        platforms,
        content_overrides: contentOverrides ?? {},
        schedule_at: scheduleAt ?? null,
      }),
    }),

  logs: (episodeId: string) =>
    apiFetch<unknown[]>(`/v1/publish/${episodeId}`),
};

export { API_BASE };
