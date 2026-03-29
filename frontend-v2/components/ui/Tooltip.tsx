'use client'

import { useState, useRef, useId } from 'react'
import { cn } from '@/lib/utils'

type TooltipSide = 'top' | 'bottom' | 'left' | 'right'

export interface TooltipProps {
  content: React.ReactNode
  side?: TooltipSide
  children: React.ReactElement<React.HTMLAttributes<HTMLElement>>
  className?: string
}

const sideStyles: Record<TooltipSide, string> = {
  top:    'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left:   'right-full top-1/2 -translate-y-1/2 mr-2',
  right:  'left-full top-1/2 -translate-y-1/2 ml-2',
}

export function Tooltip({ content, side = 'top', children, className }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const tooltipId = useId()
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const show = () => {
    timeoutRef.current = setTimeout(() => setVisible(true), 300)
  }

  const hide = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setVisible(false)
  }

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {/* Clone child to attach aria-describedby */}
      {/* We render the child directly; the tooltip is positioned absolutely */}
      <span aria-describedby={visible ? tooltipId : undefined}>
        {children}
      </span>

      {visible && (
        <span
          id={tooltipId}
          role="tooltip"
          className={cn(
            'absolute z-50 whitespace-nowrap',
            'px-2.5 py-1.5 rounded-md',
            'bg-bg-overlay border border-border-default',
            'text-xs text-primary shadow-lg',
            'animate-fade-up pointer-events-none',
            sideStyles[side],
            className,
          )}
        >
          {content}
        </span>
      )}
    </span>
  )
}

Tooltip.displayName = 'Tooltip'
