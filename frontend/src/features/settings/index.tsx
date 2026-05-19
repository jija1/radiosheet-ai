import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getAuditLog, getMe } from '../../api/user'
import type { AuditLogEntry, UserInfo } from '../../api/user'
import { useAuthStore } from '../../store/authStore'

/* ── Helpers ────────────────────────────────────────────────────────────── */

const ACTION_LABELS: Record<string, string> = {
  runsheet_generated:  'Run-sheet Generated',
  fix_applied:         'Conflict Fix Applied',
  segments_updated:    'Segments Updated',
  compliance_validated:'Compliance Validated',
  export_viewed:       'Export Viewed',
}

function labelFor(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString('en-GB', {
    day:    '2-digit',
    month:  'short',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function fmtDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function SettingsPage() {
  const logout   = useAuthStore(s => s.logout)
  const navigate = useNavigate()

  const [userInfo, setUserInfo]   = useState<UserInfo | null>(null)
  const [auditLog, setAuditLog]   = useState<AuditLogEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]         = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getMe(), getAuditLog()])
      .then(([info, log]) => { setUserInfo(info); setAuditLog(log) })
      .catch(() => setError('Could not load settings data.'))
      .finally(() => setIsLoading(false))
  }, [])

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
          <Link to="/validate"  className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">Validate</Link>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-[#8891a8] hover:text-[#ef4444] text-sm transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">

        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Settings</h1>
          <p className="text-[#8891a8] text-sm mt-1">Account details and activity history.</p>
        </div>

        {error && (
          <p className="text-[#ef4444] text-sm bg-[#ef444411] border border-[#ef444433] rounded px-4 py-3">
            {error}
          </p>
        )}

        {/* ── Account section ─────────────────────────────────────────── */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Account</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2].map(i => (
                  <div key={i} className="h-5 bg-[#1e2133] rounded animate-pulse w-48" />
                ))}
              </div>
            ) : userInfo ? (
              <dl className="space-y-3">
                <div className="flex gap-4">
                  <dt className="text-[#8891a8] text-sm w-32 shrink-0">Email</dt>
                  <dd className="text-[#e8eaf0] text-sm font-medium">{userInfo.email}</dd>
                </div>
                <div className="flex gap-4">
                  <dt className="text-[#8891a8] text-sm w-32 shrink-0">Member since</dt>
                  <dd className="text-[#e8eaf0] text-sm">{fmtDate(userInfo.created_at)}</dd>
                </div>
              </dl>
            ) : null}
          </div>
        </section>

        {/* ── Audit Log section ────────────────────────────────────────── */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">
            Audit Log
            {auditLog.length > 0 && (
              <span className="ml-2 text-[#8891a8] text-sm font-normal">
                ({auditLog.length} entries)
              </span>
            )}
          </h2>

          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl overflow-hidden">
            {isLoading ? (
              <div className="p-6 space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-4 bg-[#1e2133] rounded animate-pulse" />
                ))}
              </div>
            ) : auditLog.length === 0 ? (
              <p className="text-[#8891a8] text-sm text-center py-10">
                No activity recorded yet. Actions like generating run-sheets and applying fixes will appear here.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2133]">
                    <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium w-44">
                      Timestamp
                    </th>
                    <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium w-48">
                      Action
                    </th>
                    <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium">
                      Detail
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map((entry, idx) => (
                    <tr
                      key={idx}
                      className={`border-b border-[#1e2133] last:border-0 ${idx % 2 === 1 ? 'bg-[#0f1117]' : ''}`}
                    >
                      <td className="px-4 py-3 text-[#8891a8] text-xs font-mono whitespace-nowrap">
                        {fmtDateTime(entry.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[#e8eaf0] font-medium">
                          {labelFor(entry.action)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#8891a8] text-xs font-mono">
                        {entry.detail || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

      </main>
    </div>
  )
}
