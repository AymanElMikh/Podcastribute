'use client'

import { useState, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Tooltip } from '@/components/ui/Tooltip'

interface ContentEditorProps {
  /** The display name for this format */
  formatName: string
  /** Rendered preview content */
  children: React.ReactNode
  /** Called when user resets to the original AI-generated content */
  onReset?: () => void
  /** Whether any edits have been made */
  isDirty?: boolean
}

/**
 * Wrapper providing the top bar (format title, edit toggle, reset button)
 * around any format preview component.
 */
export function ContentEditor({
  formatName,
  children,
  onReset,
  isDirty = false,
}: ContentEditorProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <h2 className="text-xl font-bold text-primary font-display">{formatName}</h2>
        <div className="flex items-center gap-2">
          {isDirty && onReset && (
            <Tooltip content="Discard edits and restore AI output">
              <Button variant="ghost" size="sm" onClick={onReset}>
                Reset
              </Button>
            </Tooltip>
          )}
          {isDirty && (
            <span className="text-xs text-amber font-medium">Edited</span>
          )}
        </div>
      </div>

      {/* Format content */}
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  )
}

ContentEditor.displayName = 'ContentEditor'

/* ─────────────────────────────────────────────────────────────
   EditableText — single inline-editable text field
   ───────────────────────────────────────────────────────────── */

interface EditableTextProps {
  value:        string
  onChange:     (v: string) => void
  multiline?:   boolean
  className?:   string
  placeholder?: string
  /** Show character count warning at this limit (e.g. 280 for tweets) */
  charLimit?:   number
}

export function EditableText({
  value,
  onChange,
  multiline = false,
  className,
  placeholder,
  charLimit,
}: EditableTextProps) {
  const [editing, setEditing] = useState(false)
  const [draft,   setDraft]   = useState(value)
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement>(null)

  const commit = useCallback(() => {
    setEditing(false)
    onChange(draft)
  }, [draft, onChange])

  const overLimit = charLimit !== undefined && draft.length > charLimit

  if (!editing) {
    return (
      <span
        role="button"
        tabIndex={0}
        onClick={() => { setDraft(value); setEditing(true) }}
        onKeyDown={(e) => { if (e.key === 'Enter') { setDraft(value); setEditing(true) } }}
        className={cn(
          'block cursor-text rounded px-1 -mx-1',
          'hover:bg-bg-elevated transition-colors duration-150',
          'focus:outline-none focus:bg-bg-elevated',
          value !== draft && 'border-l-2 border-amber pl-2',
          className,
        )}
        aria-label="Click to edit"
        title="Click to edit"
      >
        {value || <span className="text-tertiary italic">{placeholder}</span>}
      </span>
    )
  }

  const sharedProps = {
    ref:         inputRef as React.RefObject<HTMLTextAreaElement & HTMLInputElement>,
    value:       draft,
    onChange:    (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) =>
                   setDraft(e.target.value),
    onBlur:      commit,
    onKeyDown:   (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') { setDraft(value); setEditing(false) }
      if (!multiline && e.key === 'Enter') { e.preventDefault(); commit() }
    },
    autoFocus:   true,
    placeholder,
    className:   cn(
      'w-full bg-bg-elevated border rounded-md px-2 py-1.5',
      'text-primary text-sm leading-relaxed resize-none',
      'focus:outline-none focus:border-amber',
      'transition-colors duration-150',
      overLimit ? 'border-error' : 'border-border-default',
      className,
    ),
  }

  return (
    <div className="relative">
      {multiline ? (
        <textarea {...sharedProps} rows={Math.max(3, draft.split('\n').length)} />
      ) : (
        <input type="text" {...sharedProps} />
      )}
      {charLimit !== undefined && (
        <span
          className={cn(
            'absolute bottom-1.5 right-2 text-[10px] font-mono',
            overLimit ? 'text-error' : 'text-tertiary',
          )}
        >
          {draft.length}/{charLimit}
        </span>
      )}
    </div>
  )
}

EditableText.displayName = 'EditableText'
