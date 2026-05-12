import type { Recommendation } from '../../../types/runsheet'

const CATEGORY_COLOURS: Record<string, string> = {
  balance:    '#3b82f6',
  advert:     '#f59e0b',
  placement:  '#8b5cf6',
  transition: '#10b981',
}

interface RecommendationsPanelProps {
  recommendations: Recommendation[]
}

export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  return (
    <div>
      <h3 className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
        AI Recommendations
      </h3>

      {recommendations.length === 0 ? (
        <p className="text-[#8891a8] text-sm">No recommendations</p>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, i) => {
            const dot = CATEGORY_COLOURS[rec.category] ?? '#3b82f6'
            return (
              <div key={i}>
                {/* Category header */}
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: dot }}
                  />
                  <span className="text-[#8891a8] text-xs font-medium uppercase tracking-wide">
                    {rec.category}
                  </span>
                </div>

                {/* Message */}
                <p className="text-[#6b7a99] text-sm leading-snug mb-2">{rec.message}</p>

                {/* Impact bar — wider = more room to improve */}
                <div className="h-1 bg-[#1e2133] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.round(rec.impact_score * 100)}%`,
                      backgroundColor: dot,
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
