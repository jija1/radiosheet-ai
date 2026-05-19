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

export interface UserInfo {
  email: string
  created_at: string
}

export interface AuditLogEntry {
  action: string
  detail: string
  created_at: string
}

export const getDashboard = (): Promise<DashboardData> =>
  client.get<DashboardData>('/api/v1/user/dashboard').then((r) => r.data)

export const getMe = (): Promise<UserInfo> =>
  client.get<UserInfo>('/api/v1/user/me').then((r) => r.data)

export const getAuditLog = (): Promise<AuditLogEntry[]> =>
  client.get<AuditLogEntry[]>('/api/v1/user/audit-log').then((r) => r.data)
