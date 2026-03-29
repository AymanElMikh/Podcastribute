'use client'

import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize    = 'sm' | 'md' | 'lg'

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:   ButtonVariant
  size?:      ButtonSize
  loading?:   boolean
  fullWidth?: boolean
  /**
   * When true, renders the className and styles onto the single child element
   * instead of a <button>. Useful for wrapping Next.js <Link>.
   */
  asChild?:   boolean
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-amber text-black font-semibold hover:bg-gold active:scale-[0.98]',
  secondary:
    'bg-transparent border border-border-default text-primary hover:border-border-strong hover:bg-bg-elevated',
  ghost:
    'bg-transparent text-secondary hover:text-primary hover:bg-bg-elevated',
  danger:
    'bg-transparent border border-error text-error hover:bg-error/10',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-7 px-3 text-xs gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
  lg: 'h-11 px-6 text-base gap-2.5',
}

const BASE_CLASSES =
  'inline-flex items-center justify-center rounded-md font-body ' +
  'transition-all duration-150 cursor-pointer ' +
  'focus-visible:outline-2 focus-visible:outline-amber focus-visible:outline-offset-2'

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant   = 'primary',
      size      = 'md',
      loading   = false,
      fullWidth = false,
      asChild   = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading

    const resolvedClassName = cn(
      BASE_CLASSES,
      variantStyles[variant],
      sizeStyles[size],
      isDisabled && 'opacity-40 cursor-not-allowed pointer-events-none',
      fullWidth && 'w-full',
      className,
    )

    const inner = (
      <>
        {loading && (
          <span
            aria-hidden="true"
            className="size-3.5 rounded-full border-2 border-current border-t-transparent animate-spin-slow shrink-0"
          />
        )}
        {children}
      </>
    )

    // asChild: clone the single React child and merge our props onto it
    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<React.HTMLAttributes<HTMLElement>>
      return React.cloneElement(child, {
        ...props,
        className: cn(resolvedClassName, child.props.className),
      })
    }

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={resolvedClassName}
        aria-busy={loading}
        {...props}
      >
        {inner}
      </button>
    )
  },
)

Button.displayName = 'Button'

// React needs to be in scope for React.isValidElement / React.cloneElement
import React from 'react'

export { Button }
