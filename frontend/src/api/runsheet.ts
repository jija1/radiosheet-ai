import client from './client'
import type {
  ComplianceViolation,
  Conflict,
  ProgrammeInput,
  RunSheetResponse,
  RunSheetStats,
  RunSheetSummary,
  Segment,
} from '../types/runsheet'

export interface UpdateSegmentsResponse {
  segments: Segment[]
  conflicts: Conflict[]
  stats: RunSheetStats
  compliance_score: number
  compliance_risk: string
  compliance_violations: ComplianceViolation[]
}

export const generateRunsheet = (payload: ProgrammeInput): Promise<RunSheetResponse> =>
  client.post<RunSheetResponse>('/api/v1/runsheet/generate', payload).then(r => r.data)

export const getHistory = (): Promise<RunSheetSummary[]> =>
  client.get<RunSheetSummary[]>('/api/v1/runsheet/history').then(r => r.data)

export const getRunsheet = (id: string): Promise<RunSheetResponse> =>
  client.get<RunSheetResponse>(`/api/v1/runsheet/${id}`).then(r => r.data)

export const saveUpdatedSegments = (
  runsheetId: string,
  segments: Segment[],
): Promise<UpdateSegmentsResponse> =>
  client
    .post<UpdateSegmentsResponse>('/api/v1/runsheet/update-segments', {
      runsheet_id: runsheetId,
      segments,
    })
    .then(r => r.data)
