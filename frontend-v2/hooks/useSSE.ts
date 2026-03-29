'use client'

import { useState, useEffect, useRef } from 'react'
import type { StreamEvent } from '@/lib/types'

type SSEStatus = 'idle' | 'connecting' | 'streaming' | 'done' | 'error'

export interface UseSSEReturn {
  events:  StreamEvent[]
  status:  SSEStatus
  /** Latest event of a given type, or undefined */
  latest:  (type: string) => StreamEvent | undefined
}

const TERMINAL_EVENTS = new Set(['content_ready', 'error'])

/**
 * Connects to the SSE proxy route and accumulates events.
 * Closes automatically when a terminal event ('content_ready' or 'error') arrives.
 * Cleans up EventSource on unmount — no memory leaks.
 */
export function useSSE(episodeId: string | null): UseSSEReturn {
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [status, setStatus] = useState<SSEStatus>('idle')
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!episodeId) return

    // Clean up any previous connection
    esRef.current?.close()
    setEvents([])
    setStatus('connecting')

    const es = new EventSource(`/api/stream/${episodeId}`)
    esRef.current = es

    es.onopen = () => setStatus('streaming')

    es.onmessage = (e: MessageEvent<string>) => {
      try {
        const event = JSON.parse(e.data) as StreamEvent
        setEvents((prev) => [...prev, event])
        setStatus('streaming')

        if (TERMINAL_EVENTS.has(event.type)) {
          setStatus(event.type === 'content_ready' ? 'done' : 'error')
          es.close()
          esRef.current = null
        }
      } catch {
        // Malformed event — ignore
      }
    }

    es.onerror = () => {
      setStatus('error')
      es.close()
      esRef.current = null
    }

    return () => {
      es.close()
      esRef.current = null
      setStatus('idle')
    }
  }, [episodeId])

  const latest = (type: string) =>
    [...events].reverse().find((e) => e.type === type)

  return { events, status, latest }
}
