import type { ComplianceViolation, Conflict } from '../../../types/runsheet'

const SEVERITY_STYLES: Record<string, string> = {
  high:     'bg-red-900/30 text-red-400',
  moderate: 'bg-amber-900/30 text-amber-400',
  low:      'bg-blue-900/30 text-blue-400',
}

interface ConflictPanelProps {
  conflicts: Conflict[]
  onApplyFix: (conflict: Conflict) => void
  fixingConflictId: string | null
  complianceScore: number
  complianceRisk: string
  complianceViolations: ComplianceViolation[]
}

export function ConflictPanel({
  conflicts,
  onApplyFix,
  fixingConflictId,
  complianceScore,
  complianceRisk,
  complianceViolations,
}: ConflictPanelProps) {
  const badgeColour =
    complianceRisk === 'compliant' ? '#22c55e'
    : complianceRisk === 'moderate' ? '#f59e0b'
    : '#ef4444'

  return (
    <div className="space-y-6">

      {/* ── Scheduling Conflicts ─────────────────────────────────────── */}
      <div>
        <h3 className="text-[#4a5166] uppercase text-xs tracking-wider mb-3 font-medium">
          Conflicts
        </h3>

        {conflicts.length === 0 ? (
          <div className="flex items-center gap-2 text-[#22c55e] text-sm">
            <span>✓</span>
            <span>No conflicts detected</span>
          </div>
        ) : (
          <div className="space-y-2">
            {conflicts.map((conflict, index) => (
              <div
                key={`${conflict.rule_id}-${index}`}
                className="bg-[#1f1520] border border-red-900/30 rounded-lg p-3"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[#ef4444] text-xs font-mono font-semibold">
                    {conflict.rule_id}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      conflict.severity === 'blocking'
                        ? 'bg-red-900/30 text-red-400'
                        : 'bg-amber-900/30 text-amber-400'
                    }`}
                  >
                    {conflict.severity}
                  </span>
                </div>

                <p className="text-[#f87171] text-sm mb-2 leading-snug">{conflict.message}</p>

                <button
                  type="button"
                  onClick={() => onApplyFix(conflict)}
                  disabled={fixingConflictId !== null}
                  className="bg-[#1a2b1a] border border-green-600/30 text-[#4ade80] text-xs px-3 py-1 rounded hover:bg-[#1f3a1f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {fixingConflictId === conflict.rule_id ? 'Applying…' : 'Apply Fix'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Broadcasting Compliance ───────────────────────────────────── */}
      <div className="border-t border-[#1e2133] pt-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[#4a5166] uppercase text-xs tracking-wider font-medium">
            Broadcasting Compliance
          </h3>
          {/* Score badge */}
          <span
            className="text-xs font-semibold px-2.5 py-1 rounded-full"
            style={{ backgroundColor: `${badgeColour}22`, color: badgeColour, border: `1px solid ${badgeColour}55` }}
          >
            {complianceScore}%
          </span>
        </div>

        {complianceViolations.length === 0 ? (
          <div className="flex items-center gap-2 text-[#22c55e] text-sm">
            <span>✓</span>
            <span>No compliance issues</span>
          </div>
        ) : (
          <div className="space-y-2">
            {complianceViolations.map((v, i) => (
              <div
                key={`${v.rule_id}-${i}`}
                className="bg-[#13151f] border border-[#1e2133] rounded-lg p-3"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[#8891a8] text-xs font-mono font-semibold">
                    {v.rule_id}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEVERITY_STYLES[v.severity] ?? 'bg-gray-800 text-gray-400'}`}>
                    {v.severity}
                  </span>
                </div>
                <p className="text-[#8891a8] text-xs leading-snug">{v.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
