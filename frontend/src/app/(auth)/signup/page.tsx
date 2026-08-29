"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { AuthShell, AuthField } from "@/components/auth/AuthShell"
import { Input } from "@/components/ui/input"

const schema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .min(8, "At least 8 characters")
      .regex(/[A-Z]/, "Needs an uppercase letter")
      .regex(/[0-9]/, "Needs a number"),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })
type FormValues = z.infer<typeof schema>

export default function SignupPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [serverError, setServerError] = useState("")

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    setServerError("")
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        firstName: values.firstName,
        lastName: values.lastName,
        email: values.email,
        password: values.password,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      setServerError(data.error ?? "Registration failed. Try a different email.")
      return
    }
    router.push(data.redirect ?? "/dashboard")
  }

  return (
    <AuthShell
      title="Open an account"
      intro="You need one to run a proceeding on the hosted instance. Self-hosting needs none."
      footer={
        <>
          Already have one?{" "}
          <Link href="/login" className="text-brass-text hover:text-brass-lit">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <AuthField label="First name" error={errors.firstName?.message}>
            <Input {...register("firstName")} autoComplete="given-name" placeholder="Aayush" />
          </AuthField>
          <AuthField label="Last name" error={errors.lastName?.message}>
            <Input {...register("lastName")} autoComplete="family-name" placeholder="Joshi" />
          </AuthField>
        </div>

        <AuthField label="Email address" error={errors.email?.message}>
          <Input {...register("email")} type="email" autoComplete="email" placeholder="you@example.com" />
        </AuthField>

        <AuthField label="Password" error={errors.password?.message}>
          <div className="relative">
            <Input
              {...register("password")}
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder="8+ characters, one capital, one number"
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

        <AuthField label="Confirm password" error={errors.confirmPassword?.message}>
          <div className="relative">
            <Input
              {...register("confirmPassword")}
              type={showConfirm ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Repeat the password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground/30 transition-colors hover:text-foreground/60"
              aria-label={showConfirm ? "Hide password" : "Show password"}
            >
              {showConfirm ? <EyeOff className="h-4 w-4" strokeWidth={1.75} /> : <Eye className="h-4 w-4" strokeWidth={1.75} />}
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
          {isSubmitting ? "Opening account" : "Open account"}
        </button>
      </form>
    </AuthShell>
  )
}
