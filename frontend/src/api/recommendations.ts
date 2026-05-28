import client from './client'
import type { ComplianceViolation, Conflict, Recommendation, Segment } from '../types/runsheet'

export interface SuggestionApplyResponse {
  updated_segments:        Segment[]
  remaining_conflicts:     Conflict[]
  compliance_score:        number
  compliance_risk:         string
  compliance_violations:   ComplianceViolation[]
  updated_recommendations: Recommendation[]
}

export const applySuggestion = (
  runsheet_id:      string,
  recommendation_id: string,
): Promise<SuggestionApplyResponse> =>
  client
    .post<SuggestionApplyResponse>('/api/v1/recommendations/apply', {
      runsheet_id,
      recommendation_id,
    })
    .then((r) => r.data)
