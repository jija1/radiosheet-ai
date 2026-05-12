import { useState } from 'react'

import type { Segment } from '../../../types/runsheet'

interface SegmentCardProps {
  segment: Segment
}

export function SegmentCard({ segment }: SegmentCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="bg-[#13151f] hover:bg-[#1a1d2e] border-b border-[#1e2133] border-l-4 transition-colors"
      style={{ borderLeftColor: segment.colour_hex }}
    >
      <div className="px-4 py-3">
        {/* Main row */}
        <div className="flex items-center justify-between">
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
              {segment.type.replace('_', ' ')}
            </span>
            {segment.presenter_notes && (
              <button
                type="button"
                onClick={() => setExpanded(v => !v)}
                className="text-[#8891a8] hover:text-[#e8eaf0] transition-colors text-xs leading-none"
                aria-label={expanded ? 'Collapse notes' : 'Expand notes'}
              >
                {expanded ? '▲' : '▼'}
              </button>
            )}
          </div>
        </div>

        {/* Presenter notes */}
        {expanded && segment.presenter_notes && (
          <p className="text-[#8891a8] text-sm italic mt-2 ml-[60px] leading-relaxed">
            {segment.presenter_notes}
          </p>
        )}
      </div>
    </div>
  )
}
