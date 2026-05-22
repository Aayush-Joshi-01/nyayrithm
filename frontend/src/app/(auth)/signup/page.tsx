"use client"

import Link from "next/link"
import { Scale, Shield, ArrowRight, UserPlus } from "lucide-react"
import { BackgroundPaths } from "@/components/ui/background-paths"
import { LiquidButton } from "@/components/ui/liquid-glass-button"
import { Separator } from "@/components/ui/separator"
import { getKeycloakRegisterUrl } from "@/lib/keycloak"

export default function SignupPage() {
  const handleRegister = () => {
    const redirectUri = typeof window !== "undefined"
      ? `${window.location.origin}/dashboard`
      : "http://localhost:3000/dashboard"
    window.location.href = getKeycloakRegisterUrl(redirectUri)
  }

  return (
    <BackgroundPaths>
      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
            <div className="flex flex-col items-center mb-8">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center mb-4">
                <Scale className="w-6 h-6 text-amber-400" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Create account</h1>
              <p className="text-white/40 text-sm mt-1 text-center">
                Join Nyayrithm to start simulating courtroom proceedings
              </p>
            </div>

            <div className="flex justify-center mb-6">
              <LiquidButton
                size="xl"
                className="text-white border border-white/30 rounded-full w-full justify-center font-semibold"
                onClick={handleRegister}
              >
                <UserPlus className="w-4 h-4 mr-2 inline" />
                Register with Keycloak
                <ArrowRight className="w-4 h-4 ml-2 inline" />
              </LiquidButton>
            </div>

            <div className="flex items-center gap-3 mb-6">
              <Separator className="flex-1 bg-white/10" />
              <span className="text-white/20 text-xs">or</span>
              <Separator className="flex-1 bg-white/10" />
            </div>

            <p className="text-center text-sm text-white/30">
              Already have an account?{" "}
              <Link href="/login" className="text-amber-400 hover:text-amber-300 transition-colors">
                Sign in
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
