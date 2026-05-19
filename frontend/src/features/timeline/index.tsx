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
import { SEGMENT_COLOURS } from '../../utils/colours'
import { ConflictPanel } from './components/ConflictPanel'
import { RecommendationsPanel } from './components/RecommendationsPanel'
import { SegmentCard } from './components/SegmentCard'
import { SegmentEditModal } from './components/SegmentEditModal'
import { StatsBar } from './components/StatsBar'
import { useApplyFix } from './hooks/useApplyFix'
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
  const fixingConflictId     = useUiStore(s => s.fixingConflictId)
  const logout               = useAuthStore(s => s.logout)
  const navigate             = useNavigate()

  const runsheetId = currentRunsheet?.runsheet_id ?? ''
  const { applyFix } = useApplyFix(runsheetId)
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

    // Pin the first segment to the programme start so backend _recalc_times
    // anchors from the correct time regardless of which segment moved to position 0.
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

  /* ── Layout ───────────────────────────────────────────────────────── */
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

        <div className="flex items-center gap-4">
          {/* Compliance badge */}
          {(() => {
            const colour =
              complianceRisk === 'compliant' ? '#22c55e'
              : complianceRisk === 'moderate' ? '#f59e0b'
              : '#ef4444'
            return (
              <span
                className="text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{ backgroundColor: `${colour}22`, color: colour, border: `1px solid ${colour}55` }}
                title={`Broadcasting compliance: ${complianceRisk}`}
              >
                {complianceScore}% {complianceRisk}
              </span>
            )
          })()}
          <Link to="/"          className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors">← Back to form</Link>
          <Link to="/validate"  className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors">Validate</Link>
          <Link to="/export"    className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors">Export ↗</Link>
          <Link to="/settings"  className="text-[#8891a8] text-sm hover:text-[#e8eaf0] transition-colors">Settings</Link>
          <button
            onClick={() => { logout(); navigate('/login', { replace: true }) }}
            className="text-[#8891a8] text-sm hover:text-[#ef4444] transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <StatsBar stats={stats} conflictCount={conflicts.length} recommendationCount={recommendations.length} />

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: sortable segment list */}
        <div className="flex-1 overflow-y-auto flex flex-col">
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

        {/* Right: panels */}
        <div className="w-80 shrink-0 border-l border-[#1e2133] overflow-y-auto p-4 space-y-6">
          <ConflictPanel
            conflicts={conflicts}
            onApplyFix={applyFix}
            fixingConflictId={fixingConflictId}
            complianceScore={complianceScore}
            complianceRisk={complianceRisk}
            complianceViolations={complianceViolations}
          />
          <div className="border-t border-[#1e2133] pt-6">
            <RecommendationsPanel recommendations={recommendations} />
          </div>
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
