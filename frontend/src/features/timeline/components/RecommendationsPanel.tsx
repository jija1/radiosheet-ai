import type { Recommendation } from '../../../types/runsheet'

const SEVERITY_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  critical:   { bg: 'bg-[#ef444422]', text: 'text-[#ef4444]', label: 'Critical' },
  warning:    { bg: 'bg-[#f59e0b22]', text: 'text-[#f59e0b]', label: 'Warning' },
  suggestion: { bg: 'bg-[#3b82f622]', text: 'text-[#3b82f6]', label: 'Suggestion' },
  tip:        { bg: 'bg-[#8891a822]', text: 'text-[#8891a8]', label: 'Tip' },
}

const CATEGORY_COLOURS: Record<string, string> = {
  balance:     '#3b82f6',
  advert:      '#f59e0b',
  placement:   '#8b5cf6',
  transition:  '#10b981',
  pacing:      '#06b6d4',
  engagement:  '#f97316',
  growth:      '#22c55e',
  cultural:    '#ec4899',
  monetisation:'#f59e0b',
  compliance:  '#ef4444',
}

const CONFIDENCE_STYLE: Record<string, string> = {
  high:   'text-[#22c55e]',
  medium: 'text-[#f59e0b]',
  low:    'text-[#8891a8]',
}

interface RecommendationsPanelProps {
  recommendations: Recommendation[]
}

export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  if (recommendations.length === 0) {
    return (
      <div>
        <h3 className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
          AI Recommendations
        </h3>
        <div className="flex items-center gap-2 text-[#22c55e] text-sm">
          <span>✓</span>
          <span>Run-sheet looks good — no recommendations at this time.</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h3 className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
        AI Recommendations
      </h3>
      <div className="space-y-4">
        {recommendations.map((rec, i) => {
          const dot      = CATEGORY_COLOURS[rec.category] ?? '#3b82f6'
          const badge    = SEVERITY_BADGE[rec.severity]    ?? SEVERITY_BADGE.suggestion
          const confCls  = CONFIDENCE_STYLE[rec.confidence] ?? 'text-[#8891a8]'
          const impactPct = Math.round(rec.impact_score * 100)

          return (
            <div key={rec.recommendation_id || i} className="rounded-lg bg-[#0f1117] border border-[#1e2133] p-3">
              {/* Row 1: severity badge + category tag */}
              <div className="flex items-center gap-2 mb-1.5">
                <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${badge.bg} ${badge.text}`}>
                  {badge.label}
                </span>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dot }} />
                  <span className="text-[#8891a8] text-[10px] font-medium uppercase tracking-wide">
                    {rec.category}
                  </span>
                </div>
              </div>

              {/* Row 2: message */}
              <p className="text-[#c0c8dd] text-sm leading-snug mb-2">{rec.message}</p>

              {/* Row 3: source citation */}
              {rec.source && (
                <p className="text-[#4a5166] text-xs italic mb-2 leading-snug">
                  Source: {rec.source}
                </p>
              )}

              {/* Row 4: impact bar + confidence */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-1 bg-[#1e2133] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${impactPct}%`, backgroundColor: dot }}
                  />
                </div>
                <span className="text-[10px] shrink-0 text-[#4a5166]">
                  {impactPct}%
                </span>
                {rec.confidence && (
                  <span className={`text-[10px] shrink-0 ${confCls}`}>
                    {rec.confidence} confidence
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
