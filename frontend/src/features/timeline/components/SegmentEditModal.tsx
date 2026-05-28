import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'

import type { Segment, SegmentType } from '../../../types/runsheet'
import { SEGMENT_COLOURS } from '../../../utils/colours'

const ALL_SEGMENT_TYPES: SegmentType[] = [
  'intro', 'sig_tune', 'music', 'talk', 'news', 'weather',
  'interview', 'vox_pop', 'phone_in_segment', 'storytelling',
  'drama', 'scripted_report', 'advert', 'sponsor', 'station_id', 'close',
]

function labelFor(type: SegmentType): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

interface SegmentEditModalProps {
  segment: Segment
  isSaving: boolean
  onSave: (updated: Segment) => void
  onDelete: () => void
  onClose: () => void
}

export function SegmentEditModal({
  segment,
  isSaving,
  onSave,
  onDelete,
  onClose,
}: SegmentEditModalProps) {
  const [name, setName]           = useState(segment.name)
  const [type, setType]           = useState<SegmentType>(segment.type)
  const [duration, setDuration]   = useState(segment.duration_minutes)

  // Re-initialise if the segment prop changes (e.g. opening different segment)
  useEffect(() => {
    setName(segment.name)
    setType(segment.type)
    setDuration(segment.duration_minutes)
  }, [segment.id])

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const updated: Segment = {
      ...segment,
      name: name.trim() || segment.name,
      type,
      duration_minutes: duration,
      colour_hex: SEGMENT_COLOURS[type],
    }
    onSave(updated)
  }

  const inputCls =
    'w-full bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm focus:outline-none focus:border-[#2E75B6] transition-colors'

  return (
    /* Overlay */
    <>
    <style>{`
      @keyframes modal-in {
        from { opacity: 0; transform: scale(0.95); }
        to   { opacity: 1; transform: scale(1);    }
      }
      .modal-panel { animation: modal-in 150ms ease-out both; }
      @media (prefers-reduced-motion: reduce) {
        .modal-panel { animation: none !important; }
      }
    `}</style>
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60"
      onClick={onClose}
    >
      {/* Panel — stop propagation so clicks inside don't close */}
      <div
        className="modal-panel bg-[#13151f] border border-[#1e2133] rounded-xl w-full max-w-sm mx-4 p-6 space-y-5"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-[#2E75B6] font-semibold">Edit Segment</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-[#8891a8] hover:text-[#e8eaf0] text-lg leading-none transition-colors"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-[#8891a8] text-xs mb-1">Name</label>
            <input
              type="text"
              value={name}
              maxLength={100}
              required
              onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
              className={inputCls}
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-[#8891a8] text-xs mb-1">Type</label>
            <select
              value={type}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setType(e.target.value as SegmentType)}
              className={inputCls}
            >
              {ALL_SEGMENT_TYPES.map(t => (
                <option key={t} value={t}>{labelFor(t)}</option>
              ))}
            </select>
          </div>

          {/* Duration */}
          <div>
            <label className="block text-[#8891a8] text-xs mb-1">Duration (minutes)</label>
            <input
              type="number"
              value={duration}
              min={1}
              max={120}
              required
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setDuration(Math.min(120, Math.max(1, Number(e.target.value))))}
              className={inputCls}
            />
          </div>

          {/* Start time (read-only) */}
          <div>
            <label className="block text-[#8891a8] text-xs mb-1">Start time (recalculated on save)</label>
            <input
              type="text"
              value={segment.start_time}
              readOnly
              className={`${inputCls} opacity-50 cursor-default`}
            />
          </div>

          {/* Colour preview */}
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full shrink-0"
              style={{ backgroundColor: SEGMENT_COLOURS[type] }}
            />
            <span className="text-[#8891a8] text-xs">{labelFor(type)}</span>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-60 disabled:cursor-not-allowed text-white py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {isSaving ? 'Saving…' : 'Save'}
            </button>
            <button
              type="button"
              onClick={onDelete}
              disabled={isSaving}
              className="flex-1 bg-[#1f1520] border border-red-900/40 hover:bg-[#2a1a20] disabled:opacity-60 disabled:cursor-not-allowed text-[#ef4444] py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Delete
            </button>
          </div>
        </form>
      </div>
    </div>
    </>
  )
}
