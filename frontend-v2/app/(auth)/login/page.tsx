'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { login } from '@/lib/api'
import { setToken } from '@/lib/utils'
import type { APIError } from '@/lib/types'

/* ─── Schema ─── */

const schema = z.object({
  email:    z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type FormValues = z.infer<typeof schema>

/* ─── Page ─── */

export default function LoginPage() {
  const router = useRouter()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      const { access_token } = await login(values.email, values.password)
      setToken(access_token)
      router.replace('/dashboard')
    } catch (err) {
      const apiErr = err as APIError
      if (apiErr.status === 401) {
        setError('password', { message: 'Incorrect email or password' })
      } else {
        toast.error('Sign in failed', { description: apiErr.message })
      }
    }
  }

  return (
    <>
      {/* Heading */}
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-primary font-display">Welcome back</h1>
        <p className="text-sm text-secondary mt-1">Sign in to your PodcastAI account</p>
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
          autoComplete="current-password"
          placeholder="••••••••"
          error={errors.password?.message}
          {...register('password')}
        />

        <Button
          type="submit"
          fullWidth
          size="lg"
          loading={isSubmitting}
          className="mt-2"
        >
          Sign in
        </Button>
      </form>

      {/* Footer */}
      <p className="text-center text-sm text-secondary mt-6">
        Don&apos;t have an account?{' '}
        <Link
          href="/register"
          className="text-amber hover:text-gold transition-colors duration-150"
        >
          Create one free
        </Link>
      </p>
    </>
  )
}
