import client from './client'

export interface RunSheetRecordSummary {
  runsheet_id: string
  programme_type: string
  station_name: string
  broadcast_date: string
  generated_at: string
  conflict_count: number
  score: number
}

export interface DashboardData {
  total_runsheets: number
  recent_runsheets: RunSheetRecordSummary[]
  average_score: number
  total_conflicts_resolved: number
}

export const getDashboard = (): Promise<DashboardData> =>
  client.get<DashboardData>('/api/v1/user/dashboard').then((r) => r.data)
