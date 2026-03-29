'use client'

import { useEffect, useRef } from 'react'

const BAR_COUNT = 48

export function WaveformAnimation() {
  const barsRef = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    const intervals: ReturnType<typeof setInterval>[] = []

    barsRef.current.forEach((bar, i) => {
      if (!bar) return
      const base = 20 + Math.random() * 30
      const amp  = 10 + Math.random() * 40
      const speed = 600 + Math.random() * 800
      const phase = Math.random() * Math.PI * 2

      let t = phase
      const interval = setInterval(() => {
        t += (Math.PI * 2) / (speed / 16)
        const h = base + amp * Math.abs(Math.sin(t + i * 0.15))
        bar.style.height = `${h}px`
      }, 16)

      intervals.push(interval)
    })

    return () => intervals.forEach(clearInterval)
  }, [])

  return (
    <div
      className="flex items-end justify-center gap-[3px] h-24 w-full"
      aria-hidden="true"
      role="presentation"
    >
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <div
          key={i}
          ref={(el) => { barsRef.current[i] = el }}
          className="w-1.5 rounded-full transition-none"
          style={{
            height: '20px',
            background: i % 5 === 0
              ? 'var(--color-amber)'
              : `rgba(245,166,35,${0.25 + (i % 3) * 0.15})`,
            minHeight: '4px',
          }}
        />
      ))}
    </div>
  )
}

WaveformAnimation.displayName = 'WaveformAnimation'
