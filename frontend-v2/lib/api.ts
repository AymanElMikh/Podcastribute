import { toast } from 'sonner'
import { APIError } from './types'
import { getToken, clearToken } from './utils'
import type {
  User,
  Episode,
  ContentPack,
  VoiceProfile,
  PublishResult,
  Plan,
} from './types'

/* ─────────────────────────────────────────────────────────────
   Base fetcher
   ───────────────────────────────────────────────────────────── */

/**
 * All API calls go through Next.js proxy routes (/api/proxy/...)
 * which forward to FastAPI. This avoids CORS and centralises auth.
 */
const API_BASE = '/api/proxy'

async function fetcher<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  })

  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new APIError(401, 'Session expired. Please log in again.')
  }

  if (res.status === 429) {
    const data = await res.json().catch(() => ({ detail: 'Quota exceeded' }))
    const message = (data as { detail?: string }).detail ?? 'Monthly quota reached'
    toast.warning(message, { description: 'Upgrade your plan for more episodes.' })
    throw new APIError(429, message)
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: res.statusText }))
    const message = (data as { detail?: string }).detail ?? res.statusText
    throw new APIError(res.status, message)
  }

  // 204 No Content — return empty object
  if (res.status === 204) return {} as T

  return res.json() as Promise<T>
}

/* ─────────────────────────────────────────────────────────────
   Auth
   ───────────────────────────────────────────────────────────── */

export async function register(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  return fetcher('/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function login(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  return fetcher('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function getCurrentUser(): Promise<User> {
  return fetcher('/v1/auth/me')
}

/* ─────────────────────────────────────────────────────────────
   Episodes
   ───────────────────────────────────────────────────────────── */

/**
 * Upload an audio file with real XHR progress.
 * Uses XMLHttpRequest (not fetch) because fetch doesn't expose upload progress.
 */
export function uploadEpisode(
  file: File,
  onProgress: (pct: number) => void,
): Promise<{ episode_id: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status === 202) {
        resolve(JSON.parse(xhr.responseText) as { episode_id: string })
      } else {
        const message =
          (() => {
            try {
              return (JSON.parse(xhr.responseText) as { detail?: string }).detail
            } catch {
              return null
            }
          })() ?? 'Upload failed'
        reject(new APIError(xhr.status, message))
      }
    }

    xhr.onerror = () => reject(new APIError(0, 'Network error during upload'))

    const token = getToken()
    xhr.open('POST', `${API_BASE}/v1/episodes/upload`)
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.send(formData)
  })
}

export async function ingestYouTube(
  url: string,
): Promise<{ episode_id: string }> {
  return fetcher('/v1/episodes/youtube', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}

export async function ingestRSS(
  feedUrl: string,
  episodeIndex = 0,
): Promise<{ episode_id: string }> {
  return fetcher('/v1/episodes/rss', {
    method: 'POST',
    body: JSON.stringify({ feed_url: feedUrl, episode_index: episodeIndex }),
  })
}

export async function getEpisode(id: string): Promise<Episode> {
  return fetcher(`/v1/episodes/${id}`)
}

export async function getEpisodes(): Promise<Episode[]> {
  return fetcher('/v1/episodes')
}

/* ─────────────────────────────────────────────────────────────
   Content
   ───────────────────────────────────────────────────────────── */

export async function getContentPack(episodeId: string): Promise<ContentPack> {
  return fetcher(`/v1/content/${episodeId}`)
}

/* ─────────────────────────────────────────────────────────────
   Publish
   ───────────────────────────────────────────────────────────── */

export async function publishContent(
  episodeId: string,
  platforms: string[],
  contentOverrides?: Partial<ContentPack>,
  scheduleAt?: string,
): Promise<PublishResult> {
  return fetcher('/v1/publish', {
    method: 'POST',
    body: JSON.stringify({
      episode_id: episodeId,
      platforms,
      content_overrides: contentOverrides ?? {},
      schedule_at: scheduleAt ?? null,
    }),
  })
}

/* ─────────────────────────────────────────────────────────────
   Voice
   ───────────────────────────────────────────────────────────── */

export async function getVoiceProfile(): Promise<VoiceProfile> {
  return fetcher('/v1/voice')
}

export async function calibrateVoice(posts: string[]): Promise<VoiceProfile> {
  return fetcher('/v1/voice/calibrate/posts', {
    method: 'POST',
    body: JSON.stringify({ posts }),
  })
}

export async function calibrateVoiceFromTranscripts(
  transcripts: string[],
): Promise<VoiceProfile> {
  return fetcher('/v1/voice/calibrate/transcripts', {
    method: 'POST',
    body: JSON.stringify({ transcripts }),
  })
}

export async function refineVoice(feedback: string): Promise<VoiceProfile> {
  return fetcher('/v1/voice/refine', {
    method: 'PUT',
    body: JSON.stringify({ feedback }),
  })
}

/* ─────────────────────────────────────────────────────────────
   Billing
   ───────────────────────────────────────────────────────────── */

export async function createCheckout(plan: Plan): Promise<{ url: string }> {
  return fetcher('/v1/billing/checkout', {
    method: 'POST',
    body: JSON.stringify({ plan }),
  })
}

export async function createPortalSession(): Promise<{ url: string }> {
  return fetcher('/v1/billing/portal', { method: 'POST' })
}

export async function getBillingUsage(): Promise<{
  episodes_this_month: number
  limit: number | null
  plan: Plan
  reset_at: string
}> {
  return fetcher('/v1/billing/usage')
}
