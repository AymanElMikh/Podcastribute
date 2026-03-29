'use client'

import useSWR from 'swr'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { getCurrentUser } from '@/lib/api'
import { getToken } from '@/lib/utils'
import type { User } from '@/lib/types'

/**
 * Returns the current authenticated user.
 * If `redirectIfUnauthenticated` is true (default inside app shell),
 * sends the user to /login when there is no token or the request fails.
 */
export function useAuth(redirectIfUnauthenticated = true) {
  const router = useRouter()

  const {
    data: user,
    error,
    isLoading,
    mutate,
  } = useSWR<User>(
    () => {
      // Only fetch if a token exists — avoids a redundant 401 on public pages
      if (!getToken()) throw new Error('no-token')
      return '/v1/auth/me'
    },
    () => getCurrentUser(),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    },
  )

  useEffect(() => {
    if (!redirectIfUnauthenticated) return
    if (isLoading) return
    if (!user && (error || !getToken())) {
      router.replace('/login')
    }
  }, [user, error, isLoading, redirectIfUnauthenticated, router])

  return { user, isLoading, error, mutate }
}
