"use client"

import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { AuthShell, AuthField } from "@/components/auth/AuthShell"
import { Input } from "@/components/ui/input"

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
})
type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get("redirect") ?? "/dashboard"

  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState("")

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    setServerError("")
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) {
      setServerError(data.error ?? "Sign in failed. Check the email and password.")
      return
    }
    router.push(redirect)
  }

  return (
    <AuthShell
      title="Return to chambers"
      intro="Sign in to your cases and proceedings."
      footer={
        <>
          No account yet?{" "}
          <Link href="/signup" className="text-brass-text hover:text-brass-lit">
            Open one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <AuthField label="Email address" error={errors.email?.message}>
          <Input {...register("email")} type="email" autoComplete="email" placeholder="you@example.com" />
        </AuthField>

        <AuthField label="Password" error={errors.password?.message}>
          <div className="relative">
            <Input
              {...register("password")}
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="Your password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground/30 transition-colors hover:text-foreground/60"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" strokeWidth={1.75} /> : <Eye className="h-4 w-4" strokeWidth={1.75} />}
            </button>
          </div>
        </AuthField>

        {serverError && (
          <p className="rounded-sm border border-oxblood-bright/25 bg-oxblood-bright/10 px-3 py-2 text-center text-[0.8rem] text-oxblood-bright">
            {serverError}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex w-full items-center justify-center gap-2 rounded-sm bg-brass py-2.5 text-[0.85rem] font-semibold text-[#12100A] transition-colors hover:bg-brass-lit disabled:opacity-50 active:translate-y-px"
        >
          {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSubmitting ? "Signing in" : "Sign in"}
        </button>
      </form>
    </AuthShell>
  )
}
