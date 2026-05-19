import { useState } from 'react'

import { applyFix as applyFixApi } from '../../../api/conflicts'
import { useRunsheetStore } from '../../../store/runsheetStore'
import { useUiStore } from '../../../store/uiStore'
import type { Conflict } from '../../../types/runsheet'

export function useApplyFix(runsheetId: string) {
  const [isApplying, setIsApplying] = useState(false)

  const updateSegments  = useRunsheetStore(s => s.updateSegments)
  const updateConflicts = useRunsheetStore(s => s.updateConflicts)
  const setCompliance   = useRunsheetStore(s => s.setCompliance)
  const setApplyingFix  = useUiStore(s => s.setApplyingFix)

  async function applyFix(conflict: Conflict) {
    setIsApplying(true)
    setApplyingFix(conflict.rule_id)
    try {
      const response = await applyFixApi({
        runsheet_id: runsheetId,
        conflict_id: conflict.rule_id,
      })
      updateSegments(response.updated_segments)
      updateConflicts(response.remaining_conflicts)
      setCompliance(
        response.compliance_score,
        response.compliance_risk,
        response.compliance_violations,
      )
    } catch (err) {
      console.error('Apply fix failed:', err)
    } finally {
      setIsApplying(false)
      setApplyingFix(null)
    }
  }

  return { applyFix, isApplying }
}
