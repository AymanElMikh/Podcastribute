'use client'

import { useState } from 'react'
import { uploadEpisode } from '@/lib/api'
import { APIError } from '@/lib/types'
import { ACCEPTED_AUDIO_TYPES, MAX_UPLOAD_MB } from '@/lib/constants'

type UploadStatus = 'idle' | 'validating' | 'uploading' | 'done' | 'error'

export interface UseUploadReturn {
  upload:    (file: File) => Promise<string | null>
  progress:  number
  status:    UploadStatus
  episodeId: string | null
  error:     string | null
  reset:     () => void
}

/**
 * XHR-based file upload with real progress reporting.
 * fetch() does not expose upload progress — XHR is required.
 */
export function useUpload(): UseUploadReturn {
  const [progress,  setProgress]  = useState(0)
  const [status,    setStatus]    = useState<UploadStatus>('idle')
  const [episodeId, setEpisodeId] = useState<string | null>(null)
  const [error,     setError]     = useState<string | null>(null)

  const reset = () => {
    setProgress(0)
    setStatus('idle')
    setEpisodeId(null)
    setError(null)
  }

  const upload = async (file: File): Promise<string | null> => {
    setStatus('validating')
    setError(null)

    // Client-side validation before sending
    if (!ACCEPTED_AUDIO_TYPES.includes(file.type as typeof ACCEPTED_AUDIO_TYPES[number])) {
      const msg = `Unsupported file type: ${file.type || 'unknown'}. Use MP3, MP4, WAV or M4A.`
      setError(msg)
      setStatus('error')
      return null
    }

    const mb = file.size / (1024 * 1024)
    if (mb > MAX_UPLOAD_MB) {
      const msg = `File is ${mb.toFixed(0)} MB. Maximum allowed is ${MAX_UPLOAD_MB} MB.`
      setError(msg)
      setStatus('error')
      return null
    }

    setStatus('uploading')
    setProgress(0)

    try {
      const { episode_id } = await uploadEpisode(file, (pct) => setProgress(pct))
      setEpisodeId(episode_id)
      setStatus('done')
      return episode_id
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Upload failed. Please try again.'
      setError(msg)
      setStatus('error')
      return null
    }
  }

  return { upload, progress, status, episodeId, error, reset }
}
