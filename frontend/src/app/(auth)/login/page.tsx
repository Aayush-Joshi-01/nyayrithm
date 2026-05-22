"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Scale, Shield, Eye, EyeOff, Loader2 } from "lucide-react"
import { BackgroundPaths } from "@/components/ui/background-paths"
import { Separator } from "@/components/ui/separator"

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
})
type FormValues = z.infer<typeof schema>

export default function LoginPage() {
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
      setServerError(data.error ?? "Sign in failed")
      return
    }
    router.push(redirect)
  }

  return (
    <BackgroundPaths>
      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
            {/* Logo */}
            <div className="flex flex-col items-center mb-8">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center mb-4">
                <Scale className="w-6 h-6 text-amber-400" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Welcome back</h1>
              <p className="text-white/40 text-sm mt-1 text-center">
                Sign in to your Nyayrithm account to continue
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1.5">
                  Email address
                </label>
                <input
                  {...register("email")}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-white/20 outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-colors"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-white/60 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    {...register("password")}
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 pr-10 text-sm text-white placeholder-white/20 outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
                )}
              </div>

              {serverError && (
                <p className="text-sm text-red-400 text-center rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2">
                  {serverError}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold py-2.5 text-sm transition-colors flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}
                {isSubmitting ? "Signing in…" : "Sign in"}
              </button>
            </form>

            <div className="flex items-center gap-3 my-6">
              <Separator className="flex-1 bg-white/10" />
              <span className="text-white/20 text-xs">or</span>
              <Separator className="flex-1 bg-white/10" />
            </div>

            <p className="text-center text-sm text-white/30">
              {"Don't have an account? "}
              <Link href="/signup" className="text-amber-400 hover:text-amber-300 transition-colors">
                Create account
              </Link>
            </p>

            <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-center gap-2">
              <Shield className="w-3.5 h-3.5 text-white/20" />
              <p className="text-white/20 text-xs">Secured by Keycloak Identity & Access Management</p>
            </div>
          </div>

          <p className="text-center text-white/20 text-xs mt-6">
            <Link href="/" className="hover:text-white/40 transition-colors">
              ← Back to home
            </Link>
          </p>
        </div>
      </div>
    </BackgroundPaths>
  )
}
