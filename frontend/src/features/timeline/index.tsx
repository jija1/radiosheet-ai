import { Link, useNavigate } from 'react-router-dom'

import { useRunsheetStore } from '../../store/runsheetStore'
import { useAuthStore } from '../../store/authStore'
import { useUiStore } from '../../store/uiStore'
import { ConflictPanel } from './components/ConflictPanel'
import { RecommendationsPanel } from './components/RecommendationsPanel'
import { SegmentCard } from './components/SegmentCard'
import { StatsBar } from './components/StatsBar'
import { useApplyFix } from './hooks/useApplyFix'

export default function TimelinePage() {
  const currentRunsheet  = useRunsheetStore(s => s.currentRunsheet)
  const segments         = useRunsheetStore(s => s.segments)
  const conflicts        = useRunsheetStore(s => s.conflicts)
  const recommendations  = useRunsheetStore(s => s.recommendations)
  const stats            = useRunsheetStore(s => s.stats)
  const fixingConflictId = useUiStore(s => s.fixingConflictId)
  const logout           = useAuthStore(s => s.logout)
  const navigate         = useNavigate()

  const runsheetId = currentRunsheet?.runsheet_id ?? ''
  const { applyFix } = useApplyFix(runsheetId)

  /* ── Empty state ─────────────────────────────────────────────────── */
  if (!currentRunsheet || !stats) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-[#8891a8]">No run-sheet generated yet.</p>
          <Link
            to="/"
            className="inline-block bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-5 py-2 rounded-lg text-sm transition-colors"
          >
            Generate a run-sheet
          </Link>
        </div>
      </div>
    )
  }

  const { station_name, presenter_name } = currentRunsheet.programme_input

  /* ── Main layout ─────────────────────────────────────────────────── */
  return (
    <div className="h-screen bg-[#0f1117] flex flex-col overflow-hidden">

      {/* Top nav */}
      <div className="bg-[#13151f] border-b border-[#1e2133] px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
            <span className="text-[#3b82f6] font-bold text-xs">R</span>
          </div>
          <div>
            <span className="text-[#e8eaf0] font-medium">
              Run-sheet — <span className="text-[#3b82f6]">{station_name}</span>
            </span>
            <span className="text-[#8891a8] text-xs ml-2">· {presenter_name}</span>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <Link
            to="/"
            className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors"
          >
            ← Back to form
          </Link>
          <Link
            to="/export"
            className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors"
          >
            Export ↗
          </Link>
          <button
            onClick={() => { logout(); navigate('/login', { replace: true }) }}
            className="text-[#8891a8] text-sm hover:text-[#ef4444] transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <StatsBar
        stats={stats}
        conflictCount={conflicts.length}
        recommendationCount={recommendations.length}
      />

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: segment list */}
        <div className="flex-1 overflow-y-auto">
          {segments.length === 0 ? (
            <div className="flex items-center justify-center h-full text-[#8891a8]">
              No segments found.
            </div>
          ) : (
            segments.map(segment => (
              <SegmentCard key={segment.id} segment={segment} />
            ))
          )}
        </div>

        {/* Right: panels */}
        <div className="w-80 shrink-0 border-l border-[#1e2133] overflow-y-auto p-4 space-y-6">
          <ConflictPanel
            conflicts={conflicts}
            onApplyFix={applyFix}
            fixingConflictId={fixingConflictId}
          />
          <div className="border-t border-[#1e2133] pt-6">
            <RecommendationsPanel recommendations={recommendations} />
          </div>
        </div>
      </div>
    </div>
  )
}
