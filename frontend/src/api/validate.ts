import client from './client'
import type {
  ComplianceViolation,
  Conflict,
  ProgrammeInput,
  Recommendation,
  RunSheetStats,
  Segment,
} from '../types/runsheet'

export interface ValidateRequest {
  segments: Segment[]
  programme_input: ProgrammeInput
}

export interface ValidateResponse {
  segments: Segment[]
  conflicts: Conflict[]
  compliance_score: number
  compliance_risk: string
  compliance_violations: ComplianceViolation[]
  stats: RunSheetStats
  recommendations: Recommendation[]
}

export const validateRunsheet = (payload: ValidateRequest): Promise<ValidateResponse> =>
  client.post<ValidateResponse>('/api/v1/validate/runsheet', payload).then(r => r.data)
