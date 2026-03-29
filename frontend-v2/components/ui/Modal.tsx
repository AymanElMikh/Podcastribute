'use client'

import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

export interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  /** Max width class. Defaults to "max-w-md". */
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const sizeMap = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  size = 'md',
  className,
}: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  // Sync open state with <dialog> native API
  useEffect(() => {
    const el = dialogRef.current
    if (!el) return
    if (open && !el.open) {
      el.showModal()
    } else if (!open && el.open) {
      el.close()
    }
  }, [open])

  // Close on backdrop click
  const handleClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    const rect = dialogRef.current?.getBoundingClientRect()
    if (!rect) return
    const clickedOutside =
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom
    if (clickedOutside) onClose()
  }

  // Close on Escape (native dialog handles this, but sync state)
  useEffect(() => {
    const el = dialogRef.current
    if (!el) return
    const handler = () => onClose()
    el.addEventListener('cancel', handler)
    return () => el.removeEventListener('cancel', handler)
  }, [onClose])

  if (!open) return null

  return (
    <dialog
      ref={dialogRef}
      onClick={handleClick}
      className={cn(
        // Reset <dialog> defaults
        'p-0 m-auto border-none outline-none',
        'bg-transparent backdrop:bg-black/60 backdrop:backdrop-blur-sm',
        // Our card
        'animate-fade-up',
      )}
    >
      <div
        className={cn(
          'bg-bg-overlay border border-border-default rounded-xl',
          'p-6 w-full',
          sizeMap[size],
          className,
        )}
        role="document"
      >
        {(title || description) && (
          <div className="mb-5">
            {title && (
              <h2 className="text-lg font-semibold text-primary">{title}</h2>
            )}
            {description && (
              <p className="text-sm text-secondary mt-1">{description}</p>
            )}
          </div>
        )}

        {children}
      </div>
    </dialog>
  )
}

Modal.displayName = 'Modal'

export function ModalFooter({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-end gap-3 mt-6 pt-5 border-t border-border-subtle',
        className,
      )}
    >
      {children}
    </div>
  )
}

ModalFooter.displayName = 'ModalFooter'
