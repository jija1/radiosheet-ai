import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getProfile, updateProfile } from '../../api/user'
import type { ProfileData } from '../../api/user'
import { useAuthStore } from '../../store/authStore'

/* ── Helpers ────────────────────────────────────────────────────────────── */

export function getInitials(displayName: string | null | undefined, email: string): string {
  if (displayName && displayName.trim()) {
    const parts = displayName.trim().split(/\s+/)
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return parts[0].slice(0, 2).toUpperCase()
  }
  return email[0].toUpperCase()
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
}

function fmtDateTime(iso: string | null): string {
  if (!iso) return 'Never'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function ProfilePage() {
  const user           = useAuthStore(s => s.user)
  const logout         = useAuthStore(s => s.logout)
  const setDisplayName = useAuthStore(s => s.setDisplayName)
  const navigate       = useNavigate()

  const [profile, setProfile]     = useState<ProfileData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]         = useState<string | null>(null)

  // Inline edit state
  const [isEditing, setIsEditing]   = useState(false)
  const [editValue, setEditValue]   = useState('')
  const [isSaving, setIsSaving]     = useState(false)
  const [saveError, setSaveError]   = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    getProfile()
      .then(p => {
        setProfile(p)
        setEditValue(p.display_name ?? '')
      })
      .catch(() => setError('Could not load profile.'))
      .finally(() => setIsLoading(false))
  }, [])

  useEffect(() => {
    if (isEditing) inputRef.current?.focus()
  }, [isEditing])

  async function saveDisplayName() {
    if (!profile) return
    setIsSaving(true)
    setSaveError(null)
    try {
      const updated = await updateProfile(editValue)
      setProfile(updated)
      setDisplayName(updated.display_name)
      setIsEditing(false)
    } catch {
      setSaveError('Could not save. Try again.')
    } finally {
      setIsSaving(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter')  { e.preventDefault(); saveDisplayName() }
    if (e.key === 'Escape') { setIsEditing(false); setEditValue(profile?.display_name ?? '') }
  }

  const initials = getInitials(profile?.display_name ?? user?.display_name, user?.email ?? '?')

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">

      {/* Nav */}
      <header className="border-b border-[#1e2133] bg-[#13151f] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
            <span className="text-[#2E75B6] font-bold text-xs">R</span>
          </div>
          <span className="text-[#e8eaf0] font-medium text-sm">
            Radio<span className="text-[#2E75B6]">Sheet</span> AI
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">Dashboard</Link>
          <Link to="/"          className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">New Run-sheet</Link>
          <Link to="/settings"  className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">Settings</Link>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-[#8891a8] hover:text-[#ef4444] text-sm transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6">

        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Profile</h1>
          <p className="text-[#8891a8] text-sm mt-1">Your account details and usage statistics.</p>
        </div>

        {error && (
          <p className="text-[#ef4444] text-sm bg-[#ef444411] border border-[#ef444433] rounded px-4 py-3">{error}</p>
        )}

        {/* ── Identity card ─────────────────────────────────────────────── */}
        <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6">
          <div className="flex items-start gap-5">

            {/* Avatar */}
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center shrink-0 text-white text-xl font-bold select-none"
              style={{ backgroundColor: '#2E75B6' }}
            >
              {isLoading ? '…' : initials}
            </div>

            {/* Details */}
            <div className="flex-1 space-y-3 min-w-0">

              {/* Display name — inline edit */}
              <div>
                <label className="block text-[#8891a8] text-xs mb-1">Display Name</label>
                {isEditing ? (
                  <div className="flex items-center gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={editValue}
                      maxLength={100}
                      onChange={e => setEditValue(e.target.value)}
                      onBlur={saveDisplayName}
                      onKeyDown={handleKeyDown}
                      disabled={isSaving}
                      placeholder="Enter display name"
                      className="bg-[#0f1117] border border-[#2E75B6] rounded-lg px-3 py-1.5 text-[#e8eaf0] text-sm focus:outline-none w-64 disabled:opacity-60"
                    />
                    <span className="text-[#8891a8] text-xs">Enter to save · Esc to cancel</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => { setEditValue(profile?.display_name ?? ''); setIsEditing(true) }}
                    className="group flex items-center gap-2 text-left"
                    title="Click to edit display name"
                  >
                    <span className="text-[#e8eaf0] font-medium text-sm">
                      {isLoading ? '…' : (profile?.display_name || <span className="text-[#8891a8] italic">Not set</span>)}
                    </span>
                    <span className="text-[#4a5166] group-hover:text-[#8891a8] text-xs transition-colors">✎</span>
                  </button>
                )}
                {saveError && (
                  <p className="text-[#ef4444] text-xs mt-1">{saveError}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label className="block text-[#8891a8] text-xs mb-1">Email</label>
                <span className="text-[#e8eaf0] text-sm">
                  {isLoading ? '…' : (profile?.email ?? user?.email ?? '—')}
                </span>
              </div>

              {/* Member since */}
              <div className="flex gap-8">
                <div>
                  <label className="block text-[#8891a8] text-xs mb-1">Member since</label>
                  <span className="text-[#e8eaf0] text-sm">
                    {isLoading ? '…' : fmtDate(profile?.created_at ?? null)}
                  </span>
                </div>
                <div>
                  <label className="block text-[#8891a8] text-xs mb-1">Last login</label>
                  <span className="text-[#e8eaf0] text-sm">
                    {isLoading ? '…' : fmtDateTime(profile?.last_login ?? null)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Stats cards ─────────────────────────────────────────────────── */}
        <div>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Statistics</h2>
          {isLoading ? (
            <div className="grid grid-cols-3 gap-4">
              {[0, 1, 2].map(i => (
                <div key={i} className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 h-24 animate-pulse" />
              ))}
            </div>
          ) : profile ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { label: 'Total Run-sheets',   value: String(profile.stats.total_runsheets) },
                { label: 'Average Score',      value: profile.stats.total_runsheets > 0 ? `${profile.stats.average_score}%` : '—' },
                { label: 'Total Conflicts',    value: String(profile.stats.total_conflicts_resolved) },
              ].map(({ label, value }) => (
                <div key={label} className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 flex flex-col gap-1">
                  <span className="text-[#8891a8] text-xs uppercase tracking-wide">{label}</span>
                  <span className="text-[#e8eaf0] text-3xl font-semibold">{value}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>

      </main>
    </div>
  )
}
