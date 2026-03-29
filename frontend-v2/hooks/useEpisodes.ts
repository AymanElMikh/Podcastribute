'use client'

import useSWR from 'swr'
import { getEpisodes, getEpisode } from '@/lib/api'
import { getToken } from '@/lib/utils'
import type { Episode } from '@/lib/types'

/** Fetch the full list of the current user's episodes. */
export function useEpisodes() {
  const { data, error, isLoading, mutate } = useSWR<Episode[]>(
    () => {
      if (!getToken()) throw new Error('no-token')
      return '/v1/episodes'
    },
    () => getEpisodes(),
    { refreshInterval: 5000 }, // poll so in-progress statuses update
  )

  return {
    episodes: data ?? [],
    isLoading,
    error,
    mutate,
  }
}

/** Fetch a single episode by id, polling while it is still processing. */
export function useEpisode(id: string | null) {
  const episode = useSWR<Episode>(
    () => {
      if (!id || !getToken()) throw new Error('no-token')
      return `/v1/episodes/${id}`
    },
    () => getEpisode(id!),
    {
      refreshInterval: (data) => {
        // Stop polling once the episode is terminal (ready or error)
        if (!data) return 3000
        return data.status === 'ready' || data.status === 'error' ? 0 : 3000
      },
    },
  )

  return {
    episode:   episode.data ?? null,
    isLoading: episode.isLoading,
    error:     episode.error,
    mutate:    episode.mutate,
  }
}
