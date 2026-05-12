import client from './client'
import type {
  Conflict,
  FixRequest,
  FixResponse,
  ProgrammeInput,
  Segment,
} from '../types/runsheet'

export interface DetectPayload {
  segments: Segment[]
  programme_input: ProgrammeInput
}

export const detectConflicts = (payload: DetectPayload): Promise<Conflict[]> =>
  client.post<Conflict[]>('/api/v1/conflicts/detect', payload).then(r => r.data)

export const applyFix = (payload: FixRequest): Promise<FixResponse> =>
  client.post<FixResponse>('/api/v1/conflicts/apply-fix', payload).then(r => r.data)
