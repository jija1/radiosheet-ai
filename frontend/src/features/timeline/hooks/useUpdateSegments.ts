import { useState } from 'react'

import { saveUpdatedSegments } from '../../../api/runsheet'
import { useRunsheetStore } from '../../../store/runsheetStore'
import { useToastStore } from '../../../store/toastStore'
import type { Segment } from '../../../types/runsheet'

export function useUpdateSegments(runsheetId: string) {
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError]       = useState<string | null>(null)

  const updateSegments  = useRunsheetStore(s => s.updateSegments)
  const updateConflicts = useRunsheetStore(s => s.updateConflicts)
  const updateStats     = useRunsheetStore(s => s.updateStats)
  const setCompliance   = useRunsheetStore(s => s.setCompliance)
  const toast           = useToastStore()

  async function saveSegments(segments: Segment[]): Promise<boolean> {
    setIsSaving(true)
    setError(null)
    try {
      const res = await saveUpdatedSegments(runsheetId, segments)
      updateSegments(res.segments)
      updateConflicts(res.conflicts)
      updateStats(res.stats)
      setCompliance(res.compliance_score, res.compliance_risk, res.compliance_violations)
      toast.success('Segments saved')
      return true
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save segments'
      setError(msg)
      toast.error(msg)
      return false
    } finally {
      setIsSaving(false)
    }
  }

  return { saveSegments, isSaving, error }
}
