export type ProgrammeType =
  | 'morning_show'
  | 'drive_time'
  | 'news_hour'
  | 'music_only'
  | 'sports_show'
  | 'talk_show'
  | 'religious_show'
  | 'farmer_show'

export type TalkMusicPreference = 'heavy_music' | 'balanced' | 'talk_heavy'

export type SegmentType =
  | 'music'
  | 'talk'
  | 'advert'
  | 'news'
  | 'station_id'
  | 'weather'
  | 'close'
  | 'intro'
  | 'sig_tune'
  | 'interview'
  | 'vox_pop'
  | 'phone_in_segment'
  | 'drama'
  | 'storytelling'
  | 'sponsor'
  | 'scripted_report'

export interface FixedSegment {
  name: string
  type: SegmentType
  start_time?: string
  duration_minutes: number
}

export interface ProgrammeInput {
  programme_type: ProgrammeType
  station_name: string
  broadcast_date: string
  start_time: string
  total_duration_minutes: number
  presenter_name: string
  max_advert_blocks_per_hour: number
  fixed_segments: FixedSegment[]
  talk_music_preference: TalkMusicPreference
  deep_dive?: boolean
}

export interface Segment {
  id: string
  name: string
  type: SegmentType
  start_time: string
  end_time: string
  duration_minutes: number
  colour_hex: string
  presenter_notes: string
}

export interface Conflict {
  rule_id: string
  severity: string
  message: string
  affected_segment_ids: string[]
  suggested_fix: Record<string, unknown>
}

export interface Recommendation {
  category: string
  message: string
  impact_score: number
  source: string
  confidence: string
  severity: string
  based_on_history: boolean
  recommendation_id: string
}

export interface ComplianceViolation {
  rule_id: string
  severity: string
  message: string
  penalty: number
}

export interface RunSheetStats {
  total_segments: number
  total_duration_minutes: number
  music_percentage: number
  talk_percentage: number
  advert_percentage: number
  conflict_count: number
  score: number
}

export interface RunSheetResponse {
  runsheet_id: string
  programme_input: ProgrammeInput
  segments: Segment[]
  conflicts: Conflict[]
  recommendations: Recommendation[]
  compliance_score: number
  compliance_risk: string
  compliance_violations: ComplianceViolation[]
  stats: RunSheetStats
  generated_at: string
  deep_dive_insights?: string[]
}

export interface FixRequest {
  runsheet_id: string
  conflict_id: string
}

export interface FixResponse {
  updated_segments: Segment[]
  remaining_conflicts: Conflict[]
  compliance_score: number
  compliance_risk: string
  compliance_violations: ComplianceViolation[]
}

export interface RunSheetSummary {
  id: string
  station_name: string
  programme_type: string
  total_duration_minutes: number
  generated_at: string
}
