import { useState } from 'react'

import { applySuggestion as applySuggestionApi } from '../../../api/recommendations'
import { useRunsheetStore } from '../../../store/runsheetStore'
import { useToastStore } from '../../../store/toastStore'

export function useApplySuggestion(runsheetId: string) {
  const [applyingId, setApplyingId] = useState<string | null>(null)

  const updateSegments        = useRunsheetStore(s => s.updateSegments)
  const updateConflicts       = useRunsheetStore(s => s.updateConflicts)
  const updateRecommendations = useRunsheetStore(s => s.updateRecommendations)
  const setCompliance         = useRunsheetStore(s => s.setCompliance)
  const toast                 = useToastStore()

  async function applySuggestion(recommendationId: string) {
    setApplyingId(recommendationId)
    try {
      const res = await applySuggestionApi(runsheetId, recommendationId)
      updateSegments(res.updated_segments)
      updateConflicts(res.remaining_conflicts)
      updateRecommendations(res.updated_recommendations)
      setCompliance(res.compliance_score, res.compliance_risk, res.compliance_violations)
      toast.success('Suggestion applied')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to apply suggestion'
      toast.error(msg)
    } finally {
      setApplyingId(null)
    }
  }

  return { applySuggestion, applyingId }
}
