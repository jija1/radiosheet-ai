import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { apiRegister } from '../../api/auth'
import { Spinner } from '../../components/ui/Spinner'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function RegisterPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [emailErr, setEmailErr] = useState<string | null>(null)
  const [error, setError]       = useState<string | null>(null)
  const [loading, setLoading]   = useState(false)

  const navigate = useNavigate()

  function handleEmailChange(e: ChangeEvent<HTMLInputElement>) {
    const val = e.target.value
    setEmail(val)
    if (val && !EMAIL_RE.test(val.trim())) {
      setEmailErr('Enter a valid email address')
    } else {
      setEmailErr(null)
    }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const trimmedEmail = email.trim()
    if (!EMAIL_RE.test(trimmedEmail)) {
      setEmailErr('Enter a valid email address')
      return
    }

    setError(null)

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await apiRegister(trimmedEmail, password)
      navigate('/login', { replace: true })
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Registration failed — please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const inputCls =
    'w-full bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm placeholder-[#8891a8] focus:outline-none focus:border-[#2E75B6] transition-colors'
  const inputErrCls =
    'w-full bg-[#0f1117] border border-[#ef4444] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm placeholder-[#8891a8] focus:outline-none focus:border-[#ef4444] transition-colors'

  return (
    <div className="min-h-screen bg-[#0f1117] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Brand */}
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-8 h-8 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
            <span className="text-[#2E75B6] font-bold text-sm">R</span>
          </div>
          <span className="text-[#e8eaf0] font-medium">
            Radio<span className="text-[#2E75B6]">Sheet</span> AI
          </span>
        </div>

        {/* Card */}
        <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-8 space-y-5">
          <h1 className="text-xl font-semibold text-[#2E75B6]">Create account</h1>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="block text-[#8891a8] text-xs mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="you@example.com"
                required
                className={emailErr ? inputErrCls : inputCls}
              />
              {emailErr && (
                <p className="text-[#ef4444] text-xs mt-1">{emailErr}</p>
              )}
            </div>

            <div>
              <label className="block text-[#8891a8] text-xs mb-1">Password (min 8 characters)</label>
              <input
                type="password"
                value={password}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className={inputCls}
              />
            </div>

            <div>
              <label className="block text-[#8891a8] text-xs mb-1">Confirm password</label>
              <input
                type="password"
                value={confirm}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirm(e.target.value)}
                placeholder="••••••••"
                required
                className={inputCls}
              />
            </div>

            {error && (
              <p className="text-[#ef4444] text-xs bg-[#ef444411] border border-[#ef444433] rounded px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-60 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? <><Spinner size={16} /> Creating account…</> : 'Create account'}
            </button>
          </form>

          <p className="text-[#8891a8] text-xs text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-[#2E75B6] hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
