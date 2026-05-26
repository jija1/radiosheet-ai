import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getDashboard } from '../../api/user'
import type { DashboardData } from '../../api/user'
import { getRunsheet } from '../../api/runsheet'
import { useAuthStore } from '../../store/authStore'
import { useRunsheetStore } from '../../store/runsheetStore'
import { NavBar } from '../../components/layout/NavBar'
import { Spinner } from '../../components/ui/Spinner'
import { getInitials } from '../profile'

function formatProgrammeType(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

interface StatCardProps {
  label: string
  value: string | number
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 flex flex-col gap-1">
      <span className="text-[#8891a8] text-xs uppercase tracking-wide">{label}</span>
      <span className="text-[#e8eaf0] text-3xl font-semibold">{value}</span>
    </div>
  )
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const setRunsheet = useRunsheetStore((s) => s.setRunsheet)
  const navigate = useNavigate()

  const [data, setData] = useState<DashboardData | null>(null)
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError('Could not load dashboard data.'))
  }, [])

  async function handleLoad(id: string) {
    setLoadingId(id)
    try {
      const runsheet = await getRunsheet(id)
      setRunsheet(runsheet)
      navigate('/timeline')
    } catch {
      setError('Could not load run-sheet.')
    } finally {
      setLoadingId(null)
    }
  }

  const profileAvatar = (
    <button onClick={() => navigate('/profile')} title="Profile" className="shrink-0">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold"
        style={{ backgroundColor: '#2E75B6' }}
      >
        {getInitials(user?.display_name, user?.email ?? '?')}
      </div>
    </button>
  )

  const navItems = [
    { label: 'New Run-sheet', to: '/' },
    { label: 'Validate',      to: '/validate' },
    { label: 'My Station Stats', to: '/statistics' },
    { label: 'Settings',      to: '/settings' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login') }, danger: true as const },
  ]

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <NavBar items={navItems} rightFixed={profileAvatar} />

      <main className="max-w-5xl mx-auto px-4 md:px-6 py-8 space-y-8">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Dashboard</h1>
          <p className="text-[#8891a8] text-sm mt-1">
            Welcome back, <span className="text-[#e8eaf0]">{user?.email ?? ''}</span>
          </p>
        </div>

        {error && (
          <p className="text-[#ef4444] text-sm bg-[#ef444411] border border-[#ef444433] rounded px-4 py-3">
            {error}
          </p>
        )}

        {/* Stats cards */}
        {data && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard label="Total Run-sheets" value={data.total_runsheets} />
            <StatCard
              label="Average Score"
              value={data.total_runsheets > 0
                ? `${Math.round(data.average_score * 100)}%`
                : '—'}
            />
            <StatCard label="Total Conflicts" value={data.total_conflicts_resolved} />
          </div>
        )}

        {!data && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 h-24 animate-pulse" />
            ))}
          </div>
        )}

        {/* Recent run-sheets table */}
        <div>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Recent Run-sheets</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl overflow-hidden">
            {data && data.recent_runsheets.length === 0 && (
              <p className="text-[#8891a8] text-sm text-center py-10">
                No run-sheets yet —{' '}
                <button
                  onClick={() => navigate('/')}
                  className="text-[#2E75B6] hover:underline"
                >
                  generate your first one
                </button>
              </p>
            )}

            {data && data.recent_runsheets.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[520px]">
                  <thead>
                    <tr className="border-b border-[#1e2133] text-[#8891a8] text-xs uppercase tracking-wide">
                      <th className="text-left px-4 py-3">Date</th>
                      <th className="text-left px-4 py-3">Station</th>
                      <th className="text-left px-4 py-3 hidden sm:table-cell">Programme Type</th>
                      <th className="text-right px-4 py-3">Score</th>
                      <th className="text-right px-4 py-3 hidden sm:table-cell">Conflicts</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_runsheets.map((rs, idx) => (
                      <tr
                        key={rs.runsheet_id}
                        className={`border-b border-[#1e2133] last:border-0 ${idx % 2 === 1 ? 'bg-[#0f1117]' : ''}`}
                      >
                        <td className="px-4 py-3 text-[#8891a8]">{formatDate(rs.broadcast_date)}</td>
                        <td className="px-4 py-3 text-[#e8eaf0] font-medium">{rs.station_name}</td>
                        <td className="px-4 py-3 text-[#8891a8] hidden sm:table-cell">{formatProgrammeType(rs.programme_type)}</td>
                        <td className="px-4 py-3 text-right">
                          {(() => {
                            const pct = Math.round(rs.score * 100)
                            const cls =
                              pct >= 80 ? 'text-[#22c55e]'
                              : pct >= 60 ? 'text-[#f59e0b]'
                              : 'text-[#ef4444]'
                            return (
                              <span className={`font-medium ${cls}`}>{pct}%</span>
                            )
                          })()}
                        </td>
                        <td className="px-4 py-3 text-right hidden sm:table-cell">
                          <span className={rs.conflict_count > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]'}>
                            {rs.conflict_count}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleLoad(rs.runsheet_id)}
                            disabled={loadingId === rs.runsheet_id}
                            className="bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-60 text-white text-xs px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
                          >
                            {loadingId === rs.runsheet_id ? (
                              <><Spinner size={12} /> Loading…</>
                            ) : 'Load'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!data && !error && (
              <div className="h-40 animate-pulse" />
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
