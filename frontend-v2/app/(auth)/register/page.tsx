'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { register as registerUser } from '@/lib/api'
import { setToken } from '@/lib/utils'
import type { APIError } from '@/lib/types'

/* ─── Schema ─── */

const schema = z
  .object({
    email:           z.string().email('Enter a valid email address'),
    password:        z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path:    ['confirmPassword'],
  })

type FormValues = z.infer<typeof schema>

/* ─── Page ─── */

export default function RegisterPage() {
  const router = useRouter()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      const { access_token } = await registerUser(values.email, values.password)
      setToken(access_token)
      // Send new users to onboarding
      router.replace('/onboarding')
    } catch (err) {
      const apiErr = err as APIError
      if (apiErr.status === 409) {
        setError('email', { message: 'An account with this email already exists' })
      } else {
        toast.error('Registration failed', { description: apiErr.message })
      }
    }
  }

  return (
    <>
      {/* Heading */}
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-primary font-display">Get started free</h1>
        <p className="text-sm text-secondary mt-1">
          Turn your first episode into 8 content formats
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          error={errors.email?.message}
          {...register('email')}
        />

        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          hint="Minimum 8 characters"
          error={errors.password?.message}
          {...register('password')}
        />

        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        <Button
          type="submit"
          fullWidth
          size="lg"
          loading={isSubmitting}
          className="mt-2"
        >
          Create free account
        </Button>
      </form>

      {/* Trust line */}
      <p className="text-center text-xs text-tertiary mt-4">
        Free plan includes 1 episode. No credit card required.
      </p>

      {/* Footer */}
      <p className="text-center text-sm text-secondary mt-4">
        Already have an account?{' '}
        <Link
          href="/login"
          className="text-amber hover:text-gold transition-colors duration-150"
        >
          Sign in
        </Link>
      </p>
    </>
  )
}
