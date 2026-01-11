import React, { useEffect, useMemo, useState } from 'react'
import Logo from '../images/Logo.png'

const TIPS = [
  'NLP automatically extracts symptom type, severity, and time context.',
  'Upload a food photo to estimate gluten risk in seconds.',
  'Use Reports to see correlation strength and time-lag patterns.',
  'Ask the AI Coach questions grounded in your recent meals and symptoms.',
]

const clamp = (n, min, max) => Math.max(min, Math.min(max, n))

export default function SplashScreen({ minDurationMs = 2000, onDone }) {
  const [progress, setProgress] = useState(0)
  const [tipIndex, setTipIndex] = useState(0)

  const tip = useMemo(() => TIPS[tipIndex % TIPS.length], [tipIndex])

  useEffect(() => {
    const startedAt = Date.now()

    const progressTimer = setInterval(() => {
      const elapsed = Date.now() - startedAt
      // Smooth-ish curve: quick start, then slows near the end.
      const pct = 100 * (1 - Math.exp(-elapsed / 850))
      setProgress(clamp(pct, 3, 98))
    }, 50)

    const tipTimer = setInterval(() => {
      setTipIndex((i) => i + 1)
    }, 2200)

    const doneTimer = setTimeout(() => {
      setProgress(100)
      // Small delay so 100% is visible (feels "complete", avoids abrupt cut)
      setTimeout(() => onDone?.(), 260)
    }, minDurationMs)

    return () => {
      clearInterval(progressTimer)
      clearInterval(tipTimer)
      clearTimeout(doneTimer)
    }
  }, [minDurationMs, onDone])

  return (
    <div className="min-h-screen bg-[#0a0e1a] relative overflow-hidden">
      {/* Brand-matched background */}
      <div className="network-pattern" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e1a]/40 via-[#0a0e1a]/70 to-[#0a0e1a]" />

      <div className="relative z-10 min-h-screen flex items-center justify-center px-6">
        <div className="w-full max-w-lg text-center">
          {/* Logo (no square boundary) */}
          <div className="mx-auto w-44 h-44 flex items-center justify-center relative">
            <div className="absolute inset-0 rounded-full bg-emerald-500/10 blur-2xl" />
            <img
              src={Logo}
              alt="GlutenGuard AI"
              className="w-36 h-36 object-contain drop-shadow-[0_18px_40px_rgba(16,185,129,0.25)]"
            />
          </div>

          {/* Title */}
          <div className="mt-6">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              GlutenGuard <span className="text-emerald-400">AI</span>
            </h1>
            <p className="mt-2 text-sm sm:text-base text-gray-300 font-medium">
              Multi‑modal gluten pattern detection • NLP + Vision + Statistics
            </p>
          </div>

          {/* Progress */}
          <div className="mt-8">
            <div className="h-3 w-full rounded-full bg-white/10 border border-emerald-500/20 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-emerald-500 to-emerald-600 transition-[width] duration-150"
                style={{ width: `${progress}%` }}
                aria-label="Loading progress"
              />
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-300">
              <span className="font-semibold text-emerald-300">Initializing</span>
              <span className="font-mono">{Math.round(progress)}%</span>
            </div>
          </div>

          {/* Helpful info (short, rotating) */}
          <div className="mt-6 rounded-2xl border border-emerald-500/20 bg-[#1a1f2e]/60 backdrop-blur-lg p-4">
            <p className="text-sm text-gray-200 font-medium leading-relaxed">
              {tip}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}


