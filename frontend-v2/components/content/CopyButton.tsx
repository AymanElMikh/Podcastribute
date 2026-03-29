'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface CopyButtonProps {
  text:      string
  label?:    string
  size?:     'xs' | 'sm'
  className?: string
}

export function CopyButton({ text, label = 'Copy', size = 'sm', className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      aria-label={copied ? 'Copied!' : `Copy ${label}`}
      className={cn(
        'inline-flex items-center gap-1 rounded transition-colors duration-150 cursor-pointer',
        'text-tertiary hover:text-primary',
        size === 'xs' && 'text-[10px] px-1.5 py-0.5',
        size === 'sm' && 'text-xs px-2 py-1',
        copied && 'text-success',
        className,
      )}
    >
      {copied ? (
        <>
          <CheckIcon className={size === 'xs' ? 'size-3' : 'size-3.5'} />
          Copied
        </>
      ) : (
        <>
          <ClipboardIcon className={size === 'xs' ? 'size-3' : 'size-3.5'} />
          {label}
        </>
      )}
    </button>
  )
}

CopyButton.displayName = 'CopyButton'

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
      <rect x="5" y="3" width="8" height="11" rx="1.5" />
      <path d="M5 5H4a1.5 1.5 0 0 0-1.5 1.5v7A1.5 1.5 0 0 0 4 15h6a1.5 1.5 0 0 0 1.5-1.5V12" strokeLinecap="round" />
      <path d="M7 3V2a1 1 0 0 1 2 0v1" strokeLinecap="round" />
    </svg>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M3 8l3.5 3.5L13 5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
