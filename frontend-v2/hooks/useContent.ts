'use client'

import useSWR from 'swr'
import { getContentPack } from '@/lib/api'
import { getToken } from '@/lib/utils'
import type { ContentPack } from '@/lib/types'

export function useContent(episodeId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<ContentPack>(
    () => {
      if (!episodeId || !getToken()) throw new Error('no-token')
      return `/v1/content/${episodeId}`
    },
    () => getContentPack(episodeId!),
    { revalidateOnFocus: false },
  )

  return { content: data ?? null, isLoading, error, mutate }
}
