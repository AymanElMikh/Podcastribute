'use client'

import { createContext, useContext, useState } from 'react'
import { cn } from '@/lib/utils'

/* ─── Context ─── */

interface TabsContextValue {
  active: string
  setActive: (value: string) => void
}

const TabsContext = createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const ctx = useContext(TabsContext)
  if (!ctx) throw new Error('Tabs subcomponents must be used inside <Tabs>')
  return ctx
}

/* ─── Root ─── */

export interface TabsProps {
  defaultValue: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}

export function Tabs({
  defaultValue,
  value,
  onValueChange,
  children,
  className,
}: TabsProps) {
  const [internal, setInternal] = useState(defaultValue)
  const active = value ?? internal

  const setActive = (v: string) => {
    if (!value) setInternal(v)
    onValueChange?.(v)
  }

  return (
    <TabsContext.Provider value={{ active, setActive }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

Tabs.displayName = 'Tabs'

/* ─── Tab List ─── */

export function TabsList({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      role="tablist"
      className={cn(
        'flex items-center gap-1 border-b border-border-subtle',
        className,
      )}
    >
      {children}
    </div>
  )
}

TabsList.displayName = 'TabsList'

/* ─── Tab Trigger ─── */

export interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
  disabled?: boolean
}

export function TabsTrigger({ value, children, className, disabled }: TabsTriggerProps) {
  const { active, setActive } = useTabsContext()
  const isActive = active === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => setActive(value)}
      className={cn(
        'relative px-4 py-2.5 text-sm transition-colors duration-150 cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber',
        isActive
          ? 'text-primary after:absolute after:bottom-0 after:left-0 after:right-0 after:h-px after:bg-amber'
          : 'text-secondary hover:text-primary',
        disabled && 'opacity-40 cursor-not-allowed',
        className,
      )}
    >
      {children}
    </button>
  )
}

TabsTrigger.displayName = 'TabsTrigger'

/* ─── Tab Content ─── */

export interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const { active } = useTabsContext()
  if (active !== value) return null

  return (
    <div role="tabpanel" className={cn('animate-fade-up', className)}>
      {children}
    </div>
  )
}

TabsContent.displayName = 'TabsContent'
