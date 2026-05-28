import { Link, useNavigate } from 'react-router-dom'
import { BackButton } from '../../components/ui/BackButton'

import { useAuthStore } from '../../store/authStore'
import { useRunsheetStore } from '../../store/runsheetStore'

/* ── Helpers ────────────────────────────────────────────────────────────── */

function fmtDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso.includes('T') ? iso : `${iso}T00:00:00`)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
}

function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function fmtProgrammeType(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function fmtSegmentType(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

/* ── Print CSS (injected once via <style>) ──────────────────────────────── */
const PRINT_CSS = `
@media print {
  .no-print { display: none !important; }

  @page { margin: 12mm 10mm; size: A4 landscape; }

  body {
    background: white !important;
    color: #111 !important;
    font-family: Arial, sans-serif;
    font-size: 9pt;
  }

  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .export-wrapper {
    background: white !important;
    padding: 0 !important;
  }

  .export-card {
    background: white !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  .section-card {
    background: white !important;
    border: 1px solid #ddd !important;
    margin-bottom: 10px !important;
    padding: 8px 10px !important;
    border-radius: 4px !important;
  }

  /* Force table header colour */
  .fri-table thead tr {
    background-color: #2E75B6 !important;
    color: white !important;
  }

  /* Alternating row overrides for print */
  .fri-row-odd  { background-color: #f4f6fb !important; }
  .fri-row-even { background-color: white   !important; }

  .fri-table td, .fri-table th {
    color: #111 !important;
    border-color: #bbb !important;
    font-size: 8.5pt !important;
  }

  .compliance-badge {
    border: 1px solid #999 !important;
    color: #111 !important;
  }

  .section-heading {
    color: #2E75B6 !important;
    border-bottom-color: #2E75B6 !important;
  }

  .stat-value {
    color: #111 !important;
  }

  .stat-label {
    color: #555 !important;
  }

  .violation-penalty {
    color: #c00 !important;
  }

  .footer-text {
    color: #555 !important;
  }
}
`

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function ExportPage() {
  const currentRunsheet      = useRunsheetStore(s => s.currentRunsheet)
  const segments             = useRunsheetStore(s => s.segments)
  const conflicts            = useRunsheetStore(s => s.conflicts)
  const recommendations      = useRunsheetStore(s => s.recommendations)
  const stats                = useRunsheetStore(s => s.stats)
  const complianceScore      = useRunsheetStore(s => s.complianceScore)
  const complianceRisk       = useRunsheetStore(s => s.complianceRisk)
  const complianceViolations = useRunsheetStore(s => s.complianceViolations)
  const logout               = useAuthStore(s => s.logout)
  const navigate             = useNavigate()

  /* ── Empty state ─────────────────────────────────────────────────────── */
  if (!currentRunsheet || !stats) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-[#8891a8]">No run-sheet loaded. Generate one first.</p>
          <Link
            to="/app"
            className="inline-block bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-5 py-2 rounded-lg text-sm transition-colors"
          >
            Generate a run-sheet
          </Link>
        </div>
      </div>
    )
  }

  const { programme_input } = currentRunsheet

  const badgeColour =
    complianceRisk === 'compliant' ? '#22c55e'
    : complianceRisk === 'moderate' ? '#f59e0b'
    : '#ef4444'

  /* ── Render ──────────────────────────────────────────────────────────── */
  return (
    <>
      <style>{PRINT_CSS}</style>

      <div className="min-h-screen bg-[#0f1117] export-wrapper">

        {/* ── Screen-only nav ──────────────────────────────────────────── */}
        <div className="no-print bg-[#13151f] border-b border-[#1e2133] px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
              <span className="text-[#2E75B6] font-bold text-xs">R</span>
            </div>
            <span className="text-[#e8eaf0] font-medium text-sm">
              Radio<span className="text-[#2E75B6]">Sheet</span> AI — Export
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/timeline" className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">
              ← Timeline
            </Link>
            <Link to="/validate" className="text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors">
              Validate
            </Link>
            <button
              onClick={() => window.print()}
              className="bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
            >
              Print / Save as PDF
            </button>
            <button
              onClick={() => { logout(); navigate('/login', { replace: true }) }}
              className="text-[#8891a8] hover:text-[#ef4444] text-sm transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* ── Printable content ────────────────────────────────────────── */}
        <div className="max-w-5xl mx-auto px-6 py-8 export-card">
          <div className="no-print mb-2"><BackButton /></div>

          {/* ── Run-sheet header ─────────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 mb-5 section-card">
            {/* Brand + title row */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-[#2E75B6] text-2xl font-bold leading-tight section-heading">
                  Radio Run-Sheet
                </h1>
                <p className="text-[#8891a8] text-sm mt-0.5">
                  RadioSheet AI — Broadcast Schedule
                </p>
              </div>
              {/* Compliance badge */}
              <span
                className="compliance-badge text-sm font-semibold px-3 py-1.5 rounded-full"
                style={{
                  backgroundColor: `${badgeColour}22`,
                  color: badgeColour,
                  border: `1px solid ${badgeColour}66`,
                }}
              >
                Compliance: {complianceScore}% — {complianceRisk.charAt(0).toUpperCase() + complianceRisk.slice(1)}
              </span>
            </div>

            {/* Programme details grid */}
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
              {[
                ['Station',          programme_input.station_name],
                ['Presenter',        programme_input.presenter_name],
                ['Broadcast Date',   fmtDate(String(programme_input.broadcast_date))],
                ['Programme Type',   fmtProgrammeType(programme_input.programme_type)],
                ['Start Time',       programme_input.start_time],
                ['Total Duration',   `${programme_input.total_duration_minutes} minutes`],
              ].map(([label, value]) => (
                <div key={label} className="flex gap-2">
                  <span className="text-[#8891a8] stat-label w-32 shrink-0">{label}:</span>
                  <span className="text-[#e8eaf0] stat-value font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Stats row ────────────────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl px-6 py-4 mb-5 section-card">
            <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium section-heading">
              Programme Statistics
            </p>
            <div className="flex flex-wrap gap-8">
              {[
                { label: 'Segments',   value: String(stats.total_segments) },
                { label: 'Duration',   value: `${stats.total_duration_minutes} min` },
                { label: 'Music',      value: `${stats.music_percentage}%` },
                { label: 'Talk',       value: `${stats.talk_percentage}%` },
                { label: 'Adverts',    value: `${stats.advert_percentage}%` },
                { label: 'Conflicts',  value: String(conflicts.length) },
                { label: 'Score',      value: `${Math.round(stats.score * 100)}%` },
              ].map(({ label, value }) => (
                <div key={label} className="flex flex-col gap-0.5">
                  <span className="text-[#8891a8] text-xs uppercase tracking-wide stat-label">{label}</span>
                  <span className="text-[#e8eaf0] text-lg font-semibold stat-value">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Segment table ────────────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl overflow-hidden mb-5 section-card">
            <p className="text-[#4a5166] uppercase text-xs tracking-wider px-5 pt-4 pb-2 font-medium section-heading">
              Run-Sheet — {segments.length} Segment{segments.length !== 1 ? 's' : ''}
            </p>

            <table
              className="fri-table w-full text-sm"
              style={{ borderCollapse: 'collapse' }}
            >
              <thead>
                <tr style={{ backgroundColor: '#2E75B6' }}>
                  {['Start', 'End', 'Duration', 'Segment Name', 'Type', 'Presenter Notes'].map(h => (
                    <th
                      key={h}
                      className="text-left"
                      style={{
                        padding: '8px 12px',
                        color: '#fff',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                        border: '1px solid #1a5ea8',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {segments.map((seg, idx) => {
                  const rowBg = idx % 2 === 0 ? '#13151f' : '#1e2133'
                  const rowClass = idx % 2 === 0 ? 'fri-row-odd' : 'fri-row-even'
                  const cellStyle = {
                    padding: '7px 12px',
                    border: '1px solid #1e2133',
                    color: '#e8eaf0',
                    verticalAlign: 'top' as const,
                  }
                  return (
                    <tr key={seg.id} className={rowClass} style={{ backgroundColor: rowBg }}>
                      <td style={{ ...cellStyle, fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'nowrap' as const }}>
                        {seg.start_time}
                      </td>
                      <td style={{ ...cellStyle, fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'nowrap' as const }}>
                        {seg.end_time}
                      </td>
                      <td style={{ ...cellStyle, whiteSpace: 'nowrap' as const }}>
                        {seg.duration_minutes} min
                      </td>
                      <td style={{ ...cellStyle, fontWeight: 500 }}>
                        {seg.name}
                      </td>
                      <td style={cellStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span
                            style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              backgroundColor: seg.colour_hex,
                              display: 'inline-block',
                              flexShrink: 0,
                            }}
                          />
                          {fmtSegmentType(seg.type)}
                        </div>
                      </td>
                      <td style={{ ...cellStyle, color: '#8891a8', fontSize: '0.78rem', maxWidth: '240px' }}>
                        {seg.presenter_notes || '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* ── Conflicts ────────────────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 mb-5 section-card">
            <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium section-heading">
              Scheduling Conflicts ({conflicts.length})
            </p>
            {conflicts.length === 0 ? (
              <p className="text-[#22c55e] text-sm">✓ No scheduling conflicts detected</p>
            ) : (
              <div className="space-y-2">
                {conflicts.map((c, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="text-[#ef4444] font-mono text-xs font-semibold w-12 shrink-0 pt-0.5">
                      {c.rule_id}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
                        c.severity === 'blocking' ? 'bg-red-900/30 text-red-400' : 'bg-amber-900/30 text-amber-400'
                      }`}
                    >
                      {c.severity}
                    </span>
                    <p className="text-[#f87171] text-sm leading-snug">{c.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Compliance violations ─────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 mb-5 section-card">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[#4a5166] uppercase text-xs tracking-wider font-medium section-heading">
                Broadcasting Compliance ({complianceViolations.length} violation{complianceViolations.length !== 1 ? 's' : ''})
              </p>
              <span
                className="compliance-badge text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{
                  backgroundColor: `${badgeColour}22`,
                  color: badgeColour,
                  border: `1px solid ${badgeColour}55`,
                }}
              >
                {complianceScore}% — {complianceRisk}
              </span>
            </div>
            {complianceViolations.length === 0 ? (
              <p className="text-[#22c55e] text-sm">✓ No compliance issues</p>
            ) : (
              <div className="space-y-2">
                {complianceViolations.map((v, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="text-[#8891a8] font-mono text-xs font-semibold w-12 shrink-0 pt-0.5">
                      {v.rule_id}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
                        v.severity === 'high' ? 'bg-red-900/30 text-red-400'
                        : v.severity === 'moderate' ? 'bg-amber-900/30 text-amber-400'
                        : 'bg-blue-900/30 text-blue-400'
                      }`}
                    >
                      {v.severity}
                    </span>
                    <p className="text-[#8891a8] text-sm leading-snug flex-1">{v.message}</p>
                    <span className="text-[#ef4444] text-xs font-medium shrink-0 violation-penalty">
                      −{v.penalty} pts
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Recommendations ──────────────────────────────────────── */}
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 mb-5 section-card">
            <p className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium section-heading">
              AI Recommendations ({recommendations.length})
            </p>
            {recommendations.length === 0 ? (
              <p className="text-[#8891a8] text-sm">No recommendations.</p>
            ) : (
              <div className="space-y-3">
                {recommendations.map((r, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="text-[#2E75B6] text-xs font-semibold w-24 shrink-0 pt-0.5 uppercase tracking-wide">
                      {r.category}
                    </span>
                    <p className="text-[#8891a8] text-sm leading-snug flex-1">{r.message}</p>
                    <span className="text-[#8891a8] text-xs shrink-0">
                      {Math.round(r.impact_score * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Footer ───────────────────────────────────────────────── */}
          <div className="border-t border-[#1e2133] pt-4 mt-2 flex items-center justify-between text-xs text-[#4a5166] footer-text">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-[#1a2a4a] flex items-center justify-center">
                <span className="text-[#2E75B6] font-bold text-xs leading-none">R</span>
              </div>
              <span>
                <strong className="text-[#8891a8]">RadioSheet AI</strong> — AI-assisted broadcast scheduling
              </span>
            </div>
            <span>Generated {fmtDateTime(currentRunsheet.generated_at)}</span>
          </div>

        </div>{/* /export-card */}
      </div>{/* /export-wrapper */}
    </>
  )
}
