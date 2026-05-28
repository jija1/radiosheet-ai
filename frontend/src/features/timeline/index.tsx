import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

import { useRunsheetStore } from '../../store/runsheetStore'
import { useAuthStore } from '../../store/authStore'
import { useUiStore } from '../../store/uiStore'
import { getInitials } from '../profile'
import { SEGMENT_COLOURS } from '../../utils/colours'
import { NavBar } from '../../components/layout/NavBar'
import { ConflictPanel } from './components/ConflictPanel'
import { RecommendationsPanel } from './components/RecommendationsPanel'
import { SegmentCard } from './components/SegmentCard'
import { SegmentEditModal } from './components/SegmentEditModal'
import { StatsBar } from './components/StatsBar'
import { useApplyFix } from './hooks/useApplyFix'
import { useApplySuggestion } from './hooks/useApplySuggestion'
import { useUpdateSegments } from './hooks/useUpdateSegments'
import type { Segment } from '../../types/runsheet'

/* ── Sortable wrapper ─────────────────────────────────────────────────────
   Defined at module level so React never remounts sortable items mid-render.
──────────────────────────────────────────────────────────────────────── */
interface SortableCardProps {
  segment: Segment
  onEdit: () => void
  onDelete: () => void
}

function SortableSegmentCard({ segment, onEdit, onDelete }: SortableCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: segment.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    position: isDragging ? ('relative' as const) : undefined,
    zIndex:   isDragging ? 10 : undefined,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <SegmentCard
        segment={segment}
        onEdit={onEdit}
        onDelete={onDelete}
        dragHandleProps={listeners}
      />
    </div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────────── */
export default function TimelinePage() {
  const currentRunsheet      = useRunsheetStore(s => s.currentRunsheet)
  const segments             = useRunsheetStore(s => s.segments)
  const conflicts            = useRunsheetStore(s => s.conflicts)
  const recommendations      = useRunsheetStore(s => s.recommendations)
  const stats                = useRunsheetStore(s => s.stats)
  const complianceScore      = useRunsheetStore(s => s.complianceScore)
  const complianceRisk       = useRunsheetStore(s => s.complianceRisk)
  const complianceViolations = useRunsheetStore(s => s.complianceViolations)
  const deepDiveInsights     = useRunsheetStore(s => s.deepDiveInsights)
  const fixingConflictId     = useUiStore(s => s.fixingConflictId)
  const logout               = useAuthStore(s => s.logout)
  const authUser             = useAuthStore(s => s.user)
  const navigate             = useNavigate()

  const runsheetId = currentRunsheet?.runsheet_id ?? ''
  const { applyFix } = useApplyFix(runsheetId)
  const { applySuggestion, applyingId } = useApplySuggestion(runsheetId)
  const { saveSegments, isSaving } = useUpdateSegments(runsheetId)

  // Modal state
  const [editingSegment, setEditingSegment] = useState<Segment | null>(null)
  const [isNewSegment, setIsNewSegment]     = useState(false)

  // dnd-kit sensors — PointerSensor handles mouse & touch, Keyboard for a11y
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  /* ── Drag ─────────────────────────────────────────────────────────── */
  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = segments.findIndex(s => s.id === String(active.id))
    const newIndex = segments.findIndex(s => s.id === String(over.id))
    if (oldIndex === -1 || newIndex === -1) return

    const reordered = arrayMove(segments, oldIndex, newIndex)

    const progStart = currentRunsheet!.programme_input.start_time
    const withFixedStart = reordered.map((seg, i) =>
      i === 0 ? { ...seg, start_time: progStart } : seg,
    )

    saveSegments(withFixedStart)
  }

  /* ── Edit / delete ───────────────────────────────────────────────── */
  function openEdit(segment: Segment) {
    setEditingSegment({ ...segment })
    setIsNewSegment(false)
  }

  function handleAddSegment() {
    const lastSeg   = segments[segments.length - 1]
    const startTime = lastSeg
      ? lastSeg.end_time
      : (currentRunsheet?.programme_input.start_time ?? '06:00')
    const newSeg: Segment = {
      id:               crypto.randomUUID(),
      name:             'New Segment',
      type:             'talk',
      start_time:       startTime,
      end_time:         startTime,
      duration_minutes: 5,
      colour_hex:       SEGMENT_COLOURS['talk'],
      presenter_notes:  '',
    }
    setEditingSegment(newSeg)
    setIsNewSegment(true)
  }

  async function handleSave(updated: Segment) {
    const newList = isNewSegment
      ? [...segments, updated]
      : segments.map(s => s.id === updated.id ? updated : s)
    const ok = await saveSegments(newList)
    if (ok) setEditingSegment(null)
  }

  async function handleDeleteFromModal() {
    if (!editingSegment) return
    if (isNewSegment) { setEditingSegment(null); return }
    const newList = segments.filter(s => s.id !== editingSegment.id)
    const ok = await saveSegments(newList)
    if (ok) setEditingSegment(null)
  }

  async function handleDeleteFromCard(segmentId: string) {
    await saveSegments(segments.filter(s => s.id !== segmentId))
  }

  /* ── Empty state ──────────────────────────────────────────────────── */
  if (!currentRunsheet || !stats) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-[#8891a8]">No run-sheet generated yet.</p>
          <Link
            to="/app"
            className="inline-block bg-[#2563eb] hover:bg-[#1d4ed8] text-white px-5 py-2 rounded-lg text-sm transition-colors"
          >
            Generate a run-sheet
          </Link>
        </div>
      </div>
    )
  }

  const { station_name, presenter_name } = currentRunsheet.programme_input

  const complianceColour =
    complianceRisk === 'compliant' ? '#22c55e'
    : complianceRisk === 'moderate' ? '#f59e0b'
    : '#ef4444'

  const complianceBadge = (
    <span
      className="text-xs font-semibold px-2.5 py-1 rounded-full"
      style={{
        backgroundColor: `${complianceColour}22`,
        color: complianceColour,
        border: `1px solid ${complianceColour}55`,
      }}
      title={`Broadcasting compliance: ${complianceRisk}`}
    >
      {complianceScore}% {complianceRisk}
    </span>
  )

  const profileAvatar = (
    <Link to="/profile" title="Profile" className="shrink-0">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold"
        style={{ backgroundColor: '#2E75B6' }}
      >
        {getInitials(authUser?.display_name, authUser?.email ?? '?')}
      </div>
    </Link>
  )

  const subtitle = (
    <>
      <span className="text-[#e8eaf0] font-medium hidden md:inline">
        — <span className="text-[#3b82f6]">{station_name}</span>
      </span>
      <span className="text-[#8891a8] text-xs ml-1 hidden md:inline">· {presenter_name}</span>
    </>
  )

  const navItems = [
    { label: '← Back to form', to: '/app' },
    { label: 'Validate',       to: '/validate' },
    { label: 'Export ↗',       to: '/export' },
    { label: 'Settings',       to: '/settings' },
    { label: 'Help',           to: '/info' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login', { replace: true }) }, danger: true as const },
  ]

  /* ── Layout ───────────────────────────────────────────────────────── */
  return (
    <div className="h-screen bg-[#0f1117] flex flex-col overflow-hidden">

      <NavBar
        subtitle={subtitle}
        rightFixed={
          <div className="flex items-center gap-2">
            {complianceBadge}
            {profileAvatar}
          </div>
        }
        items={navItems}
      />

      {/* Stats bar */}
      <StatsBar stats={stats} conflictCount={conflicts.length} recommendationCount={recommendations.length} />

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: sortable segment list */}
        <div className="flex-1 overflow-y-auto flex flex-col min-w-0">
          {/* Dashboard shortcut */}
          <div className="px-4 pt-3 shrink-0">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-[#8891a8] hover:text-[#e8eaf0] text-xs transition-colors"
            >
              ← Dashboard
            </button>
          </div>
          {segments.length === 0 ? (
            <div className="flex items-center justify-center flex-1 text-[#8891a8]">
              No segments. Add one below.
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={segments.map(s => s.id)}
                strategy={verticalListSortingStrategy}
              >
                {segments.map(segment => (
                  <SortableSegmentCard
                    key={segment.id}
                    segment={segment}
                    onEdit={() => openEdit(segment)}
                    onDelete={() => handleDeleteFromCard(segment.id)}
                  />
                ))}
              </SortableContext>
            </DndContext>
          )}

          {/* Add Segment */}
          <div className="p-4 shrink-0">
            <button
              type="button"
              onClick={handleAddSegment}
              disabled={isSaving}
              className="w-full border border-dashed border-[#1e2133] hover:border-[#2E75B6] text-[#8891a8] hover:text-[#2E75B6] py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              + Add Segment
            </button>
          </div>
        </div>

        {/* Right: panels — hidden on small screens, accessible via scroll */}
        <div className="w-72 md:w-80 shrink-0 border-l border-[#1e2133] overflow-y-auto p-4 space-y-6">
          <ConflictPanel
            conflicts={conflicts}
            onApplyFix={applyFix}
            fixingConflictId={fixingConflictId}
            complianceScore={complianceScore}
            complianceRisk={complianceRisk}
            complianceViolations={complianceViolations}
          />
          <div className="border-t border-[#1e2133] pt-6">
            <RecommendationsPanel
              recommendations={recommendations}
              onApplySuggestion={applySuggestion}
              applyingId={applyingId}
            />
          </div>

          {deepDiveInsights.length > 0 && (
            <div
              className="border-l-2 rounded-lg p-4 bg-[#13151f] border border-[#1e2133]"
              style={{ borderLeftColor: '#2E75B6' }}
            >
              <h3 className="text-[#2E75B6] font-medium text-sm mb-2">Deep Dive Insights</h3>
              <ul className="space-y-2">
                {deepDiveInsights.map((insight, i) => (
                  <li key={i} className="text-[#8891a8] text-xs leading-relaxed">
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Edit modal */}
      {editingSegment && (
        <SegmentEditModal
          segment={editingSegment}
          isSaving={isSaving}
          onSave={handleSave}
          onDelete={handleDeleteFromModal}
          onClose={() => setEditingSegment(null)}
        />
      )}
    </div>
  )
}
