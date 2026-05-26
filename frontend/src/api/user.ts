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

export interface ProfileStats {
  total_runsheets: number
  average_score: number
  total_conflicts_resolved: number
}

export interface ProfileData {
  email: string
  display_name: string | null
  created_at: string
  last_login: string | null
  stats: ProfileStats
}

export const getDashboard = (): Promise<DashboardData> =>
  client.get<DashboardData>('/api/v1/user/dashboard').then((r) => r.data)

export const getMe = (): Promise<UserInfo> =>
  client.get<UserInfo>('/api/v1/user/me').then((r) => r.data)

export const getAuditLog = (): Promise<AuditLogEntry[]> =>
  client.get<AuditLogEntry[]>('/api/v1/user/audit-log').then((r) => r.data)

export const getProfile = (): Promise<ProfileData> =>
  client.get<ProfileData>('/api/v1/user/profile').then((r) => r.data)

export const updateProfile = (display_name: string): Promise<ProfileData> =>
  client.patch<ProfileData>('/api/v1/user/profile', { display_name }).then((r) => r.data)

export interface UserSettings {
  default_station_name: string | null
  default_presenter_name: string | null
  default_programme_type: string | null
  default_duration_minutes: number | null
  default_talk_music_preference: string | null
  default_max_adverts_per_hour: number | null
  time_format: string
  cultural_calendar_enabled: boolean
  strict_mode: boolean
  auto_apply_fixes: boolean
  notifications_enabled: boolean
  default_region: string | null
  station_audience: string | null
  recommendation_depth: string
  analytics_opted_out: boolean
  audit_log_retention_days: number
}

export const getSettings = (): Promise<UserSettings> =>
  client.get<UserSettings>('/api/v1/user/settings').then((r) => r.data)

export const updateSettings = (payload: Partial<UserSettings>): Promise<UserSettings> =>
  client.patch<UserSettings>('/api/v1/user/settings', payload).then((r) => r.data)

/* ── User statistics (Session K2) ───────────────────────────────────────── */

export interface UserStatistic {
  stat_key: string
  stat_value: string
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export const listStatistics = (): Promise<UserStatistic[]> =>
  client.get<UserStatistic[]>('/api/v1/user/statistics').then((r) => r.data)

export const upsertStatistic = (payload: {
  stat_key: string
  stat_value: string
  notes?: string | null
}): Promise<UserStatistic> =>
  client.post<UserStatistic>('/api/v1/user/statistics', payload).then((r) => r.data)

export const deleteStatistic = (stat_key: string): Promise<void> =>
  client.delete(`/api/v1/user/statistics/${encodeURIComponent(stat_key)}`).then(() => undefined)

/* ── Privacy controls (Session K2) ─────────────────────────────────────── */

export const downloadUserExport = async (): Promise<void> => {
  const response = await client.get('/api/v1/user/export', { responseType: 'blob' })
  const blob = new Blob([response.data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'radiosheet_data.json'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export const deleteAccount = (password: string): Promise<void> =>
  client.delete('/api/v1/user/account', { data: { password } }).then(() => undefined)
