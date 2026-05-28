import type { Recommendation } from '../../../types/runsheet'
import { Spinner } from '../../../components/ui/Spinner'

// Recommendation IDs that have automated fixes (mirrors backend FIXABLE_IDS)
const FIXABLE_IDS = new Set(['M001', 'M002', 'M009', 'M006', 'C008', 'C009'])

const SEVERITY_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  critical:   { bg: 'bg-[#ef444422]', text: 'text-[#ef4444]', label: 'Critical' },
  warning:    { bg: 'bg-[#f59e0b22]', text: 'text-[#f59e0b]', label: 'Warning' },
  suggestion: { bg: 'bg-[#3b82f622]', text: 'text-[#3b82f6]', label: 'Suggestion' },
  tip:        { bg: 'bg-[#8891a822]', text: 'text-[#8891a8]', label: 'Tip' },
}

const CATEGORY_COLOURS: Record<string, string> = {
  balance:      '#3b82f6',
  advert:       '#f59e0b',
  placement:    '#8b5cf6',
  transition:   '#10b981',
  pacing:       '#06b6d4',
  engagement:   '#f97316',
  growth:       '#22c55e',
  cultural:     '#ec4899',
  monetisation: '#f59e0b',
  compliance:   '#ef4444',
}

const CONFIDENCE_STYLE: Record<string, string> = {
  high:   'text-[#22c55e]',
  medium: 'text-[#f59e0b]',
  low:    'text-[#8891a8]',
}

interface RecommendationsPanelProps {
  recommendations:   Recommendation[]
  onApplySuggestion: (id: string) => void
  applyingId:        string | null
}

export function RecommendationsPanel({
  recommendations,
  onApplySuggestion,
  applyingId,
}: RecommendationsPanelProps) {
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
    <>
      <style>{`
        @keyframes rec-slide-in {
          from { opacity: 0; transform: translateX(12px); }
          to   { opacity: 1; transform: translateX(0);    }
        }
        .rec-card {
          animation: rec-slide-in 250ms ease-out both;
        }
        @media (prefers-reduced-motion: reduce) {
          .rec-card { animation: none !important; }
        }
      `}</style>
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
            const isFixable = rec.recommendation_id ? FIXABLE_IDS.has(rec.recommendation_id) : false
            const isApplying = applyingId === rec.recommendation_id

            return (
              <div
                key={rec.recommendation_id || i}
                className="rec-card rounded-lg bg-[#0f1117] border border-[#1e2133] p-3"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                {/* Row 1: severity badge + category tag + history badge */}
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${badge.bg} ${badge.text}`}>
                    {badge.label}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dot }} />
                    <span className="text-[#8891a8] text-[10px] font-medium uppercase tracking-wide">
                      {rec.category}
                    </span>
                  </div>
                  {rec.based_on_history && (
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[#8891a822] text-[#8891a8]">
                      📊 Based on your history
                    </span>
                  )}
                </div>

                {/* Row 2: message */}
                <p className="text-[#c0c8dd] text-sm leading-snug mb-2">{rec.message}</p>

                {/* Row 3: source citation */}
                {rec.source && (
                  <p className="text-[#4a5166] text-xs italic mb-2 leading-snug">
                    Source: {rec.source}
                  </p>
                )}

                {/* Row 4: impact bar + confidence + apply button */}
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
                  {isFixable && (
                    <button
                      onClick={() => rec.recommendation_id && onApplySuggestion(rec.recommendation_id)}
                      disabled={isApplying || applyingId !== null}
                      className="shrink-0 text-[10px] font-semibold px-2 py-1 rounded bg-[#2E75B622] text-[#2E75B6] border border-[#2E75B644] hover:bg-[#2E75B633] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    >
                      {isApplying ? (
                        <><Spinner size={10} /> Applying…</>
                      ) : (
                        'Apply Suggestion'
                      )}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}
