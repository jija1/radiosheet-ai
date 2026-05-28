import { useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { validateRunsheet } from '../../api/validate'
import { BackButton } from '../../components/ui/BackButton'
import type { ValidateResponse } from '../../api/validate'
import { getHistory, getRunsheet } from '../../api/runsheet'
import { useAuthStore } from '../../store/authStore'
import { useRunsheetStore } from '../../store/runsheetStore'
import { NavBar } from '../../components/layout/NavBar'
import { Spinner } from '../../components/ui/Spinner'
import type { ProgrammeInput, RunSheetSummary, Segment } from '../../types/runsheet'

/* ── Helpers ────────────────────────────────────────────────────────────── */

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatProgrammeType(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const SEVERITY_STYLES: Record<string, string> = {
  blocking: 'bg-red-900/30 text-red-400',
  warning:  'bg-amber-900/30 text-amber-400',
  high:     'bg-red-900/30 text-red-400',
  moderate: 'bg-amber-900/30 text-amber-400',
  low:      'bg-blue-900/30 text-blue-400',
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function ValidatePage() {
  const currentRunsheet = useRunsheetStore(s => s.currentRunsheet)
  const storeSegments   = useRunsheetStore(s => s.segments)
  const logout          = useAuthStore(s => s.logout)
  const navigate        = useNavigate()

  const [source, setSource]           = useState<'history' | 'current'>('history')
  const [history, setHistory]         = useState<RunSheetSummary[]>([])
  const [selectedId, setSelectedId]   = useState('')
  const [result, setResult]           = useState<ValidateResponse | null>(null)
  const [isLoading, setIsLoading]     = useState(false)
  const [isFetching, setIsFetching]   = useState(true)
  const [error, setError]             = useState<string | null>(null)

  useEffect(() => {
    getHistory()
      .then(items => { setHistory(items); if (items[0]) setSelectedId(items[0].id) })
      .catch(() => setError('Could not load run-sheet history.'))
      .finally(() => setIsFetching(false))
  }, [])

  async function handleValidate() {
    setError(null)
    setIsLoading(true)
    try {
      let request: { segments: Segment[]; programme_input: ProgrammeInput }

      if (source === 'current') {
        if (!currentRunsheet) {
          setError('No run-sheet loaded. Generate one first or choose from history.')
          return
        }
        request = {
          segments: storeSegments,
          programme_input: currentRunsheet.programme_input,
        }
      } else {
        if (!selectedId) {
          setError('Please select a run-sheet from history.')
          return
        }
        const rs = await getRunsheet(selectedId)
        request = { segments: rs.segments, programme_input: rs.programme_input }
      }

      const res = await validateRunsheet(request)
      setResult(res)
    } catch {
      setError('Validation failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  function badgeColour(risk: string): string {
    if (risk === 'compliant') return '#22c55e'
    if (risk === 'moderate')  return '#f59e0b'
    return '#ef4444'
  }

  const inputCls =
    'bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm focus:outline-none focus:border-[#2E75B6] transition-colors'

  const navItems = [
    { label: 'Dashboard',     to: '/dashboard' },
    { label: 'New Run-sheet', to: '/app' },
    { label: 'Timeline',      to: '/timeline' },
    { label: 'Help',          to: '/info' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login') }, danger: true as const },
  ]

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <NavBar items={navItems} />

      <main className="max-w-3xl mx-auto px-4 md:px-6 py-8 space-y-8">
        <BackButton />

        {/* Title */}
        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Validate Run-sheet</h1>
          <p className="text-[#8891a8] text-sm mt-1">
            Re-run conflict detection and compliance checks on any saved run-sheet.
          </p>
        </div>

        {/* Source selector */}
        <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4">
          <p className="text-[#e8eaf0] text-sm font-medium">Select source</p>

          {/* Radio buttons */}
          <div className="flex gap-6 flex-wrap">
            {(['history', 'current'] as const).map(opt => (
              <label key={opt} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="source"
                  value={opt}
                  checked={source === opt}
                  onChange={() => { setSource(opt); setResult(null); setError(null) }}
                  className="accent-[#2E75B6]"
                />
                <span className="text-[#e8eaf0] text-sm capitalize">
                  {opt === 'history' ? 'Load from history' : 'Load current run-sheet'}
                </span>
              </label>
            ))}
          </div>

          {/* History dropdown */}
          {source === 'history' && (
            <div>
              {isFetching ? (
                <div className="flex items-center gap-2 text-[#8891a8] text-sm">
                  <Spinner size={14} /> Loading history…
                </div>
              ) : history.length === 0 ? (
                <p className="text-[#8891a8] text-sm">No saved run-sheets</p>
              ) : (
                <select
                  value={selectedId}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedId(e.target.value)}
                  className={`${inputCls} w-full`}
                >
                  {history.map(rs => (
                    <option key={rs.id} value={rs.id}>
                      {formatDate(rs.generated_at)} — {rs.station_name} ({formatProgrammeType(rs.programme_type)})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Current run-sheet info */}
          {source === 'current' && (
            <p className="text-[#8891a8] text-sm">
              {currentRunsheet
                ? `Current: ${currentRunsheet.programme_input.station_name} — ${formatProgrammeType(currentRunsheet.programme_input.programme_type)}`
                : 'No run-sheet loaded. Generate one first.'}
            </p>
          )}

          {error && (
            <p className="text-[#ef4444] text-xs bg-[#ef444411] border border-[#ef444433] rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={handleValidate}
            disabled={isLoading || (source === 'current' && !currentRunsheet) || (source === 'history' && history.length === 0)}
            className="bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            {isLoading ? <><Spinner size={14} /> Validating…</> : 'Validate'}
          </button>
        </div>

        {/* ── Results ─────────────────────────────────────────────────── */}
        {result && (
          <div className="space-y-6">

            {/* Summary line */}
            <div className="bg-[#13151f] border border-[#1e2133] rounded-xl px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
              <p className="text-[#e8eaf0] text-sm">
                <span className={result.conflicts.length > 0 ? 'text-[#ef4444] font-semibold' : 'text-[#22c55e] font-semibold'}>
                  {result.conflicts.length} conflict{result.conflicts.length !== 1 ? 's' : ''} detected
                </span>
                <span className="text-[#8891a8]"> · compliance score </span>
                <span className="font-semibold" style={{ color: badgeColour(result.compliance_risk) }}>
                  {result.compliance_score}
                </span>
                <span className="text-[#8891a8]"> — Risk: </span>
                <span className="font-semibold capitalize" style={{ color: badgeColour(result.compliance_risk) }}>
                  {result.compliance_risk}
                </span>
              </p>
              <span
                className="text-xs font-semibold px-2.5 py-1 rounded-full shrink-0"
                style={{
                  backgroundColor: `${badgeColour(result.compliance_risk)}22`,
                  color: badgeColour(result.compliance_risk),
                  border: `1px solid ${badgeColour(result.compliance_risk)}55`,
                }}
              >
                {result.compliance_score}% {result.compliance_risk}
              </span>
            </div>

            {/* Stats */}
            <div className="bg-[#13151f] border border-[#1e2133] rounded-xl px-6 py-4">
              <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">Statistics</p>
              <div className="flex flex-wrap gap-8">
                {[
                  { label: 'Segments',    value: String(result.stats.total_segments) },
                  { label: 'Duration',    value: `${result.stats.total_duration_minutes} min` },
                  { label: 'Music %',     value: `${result.stats.music_percentage}%` },
                  { label: 'Talk %',      value: `${result.stats.talk_percentage}%` },
                  { label: 'Advert %',    value: `${result.stats.advert_percentage}%` },
                  { label: 'Score',       value: `${Math.round(result.stats.score * 100)}%` },
                ].map(({ label, value }) => (
                  <div key={label} className="flex flex-col gap-0.5">
                    <span className="text-[#8891a8] text-xs uppercase tracking-wide">{label}</span>
                    <span className="text-[#e8eaf0] text-lg font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Conflicts */}
            <div>
              <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
                Scheduling Conflicts ({result.conflicts.length})
              </p>
              {result.conflicts.length === 0 ? (
                <div className="flex items-center gap-2 text-[#22c55e] text-sm bg-[#13151f] border border-[#1e2133] rounded-xl px-4 py-3">
                  <span>✓</span><span>No scheduling conflicts</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {result.conflicts.map((c, i) => (
                    <div key={`${c.rule_id}-${i}`} className="bg-[#13151f] border border-[#1e2133] rounded-xl px-4 py-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[#ef4444] text-xs font-mono font-semibold">{c.rule_id}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEVERITY_STYLES[c.severity] ?? 'bg-gray-800 text-gray-400'}`}>
                          {c.severity}
                        </span>
                      </div>
                      <p className="text-[#f87171] text-sm leading-snug">{c.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Compliance violations */}
            <div>
              <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
                Broadcasting Compliance ({result.compliance_violations.length} violation{result.compliance_violations.length !== 1 ? 's' : ''})
              </p>
              {result.compliance_violations.length === 0 ? (
                <div className="flex items-center gap-2 text-[#22c55e] text-sm bg-[#13151f] border border-[#1e2133] rounded-xl px-4 py-3">
                  <span>✓</span><span>No compliance issues</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {result.compliance_violations.map((v, i) => (
                    <div key={`${v.rule_id}-${i}`} className="bg-[#13151f] border border-[#1e2133] rounded-xl px-4 py-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[#8891a8] text-xs font-mono font-semibold">{v.rule_id}</span>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEVERITY_STYLES[v.severity] ?? 'bg-gray-800 text-gray-400'}`}>
                            {v.severity}
                          </span>
                          <span className="text-[#8891a8] text-xs">−{v.penalty} pts</span>
                        </div>
                      </div>
                      <p className="text-[#8891a8] text-sm leading-snug">{v.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  )
}
