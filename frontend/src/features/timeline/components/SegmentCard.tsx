import { useState } from 'react'
import type { DraggableSyntheticListeners } from '@dnd-kit/core'

import type { Segment } from '../../../types/runsheet'

interface SegmentCardProps {
  segment: Segment
  onEdit: () => void
  onDelete: () => void
  dragHandleProps?: DraggableSyntheticListeners
}

export function SegmentCard({ segment, onEdit, onDelete, dragHandleProps }: SegmentCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="bg-[#13151f] hover:bg-[#1a1d2e] border-b border-[#1e2133] border-l-4 transition-all duration-150 hover:scale-[1.01] origin-left"
      style={{ borderLeftColor: segment.colour_hex }}
    >
      <div className="px-2 py-3 flex items-center gap-1">

        {/* Drag handle — listeners only here, so card click still opens modal */}
        <div
          {...dragHandleProps}
          onClick={e => e.stopPropagation()}
          className="shrink-0 flex items-center justify-center w-6 h-6 text-[#3a4060] hover:text-[#8891a8] cursor-grab active:cursor-grabbing touch-none select-none"
          aria-label="Drag to reorder"
        >
          ⠿
        </div>

        {/* Clickable content area */}
        <div
          className="flex items-center justify-between flex-1 min-w-0 cursor-pointer"
          onClick={onEdit}
        >
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-[#8891a8] text-xs font-mono shrink-0 w-12">
              {segment.start_time}
            </span>
            <span className="text-[#e8eaf0] text-sm font-medium truncate">
              {segment.name}
            </span>
          </div>

          <div className="flex items-center gap-2 ml-3 shrink-0">
            <span className="text-[#8891a8] text-xs">{segment.duration_minutes}m</span>
            <span
              className="text-white text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ backgroundColor: segment.colour_hex }}
            >
              {segment.type.replace(/_/g, ' ')}
            </span>
            {segment.presenter_notes && (
              <button
                type="button"
                onClick={e => { e.stopPropagation(); setExpanded(v => !v) }}
                className="text-[#8891a8] hover:text-[#e8eaf0] transition-colors text-xs leading-none"
                aria-label={expanded ? 'Collapse notes' : 'Expand notes'}
              >
                {expanded ? '▲' : '▼'}
              </button>
            )}
            <button
              type="button"
              onClick={e => { e.stopPropagation(); onDelete() }}
              className="text-[#8891a8] hover:text-[#ef4444] transition-colors text-xs leading-none px-1"
              aria-label="Delete segment"
            >
              ×
            </button>
          </div>
        </div>
      </div>

      {/* Presenter notes */}
      {expanded && segment.presenter_notes && (
        <p className="text-[#8891a8] text-sm italic pb-3 ml-9 pr-4 leading-relaxed">
          {segment.presenter_notes}
        </p>
      )}
    </div>
  )
}
