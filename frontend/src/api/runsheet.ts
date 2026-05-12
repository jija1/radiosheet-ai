import client from './client'
import type { ProgrammeInput, RunSheetResponse, RunSheetSummary } from '../types/runsheet'

export const generateRunsheet = (payload: ProgrammeInput): Promise<RunSheetResponse> =>
  client.post<RunSheetResponse>('/api/v1/runsheet/generate', payload).then(r => r.data)

export const getHistory = (): Promise<RunSheetSummary[]> =>
  client.get<RunSheetSummary[]>('/api/v1/runsheet/history').then(r => r.data)

export const getRunsheet = (id: string): Promise<RunSheetResponse> =>
  client.get<RunSheetResponse>(`/api/v1/runsheet/${id}`).then(r => r.data)
