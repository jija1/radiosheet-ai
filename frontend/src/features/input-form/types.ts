import type { ProgrammeType, TalkMusicPreference } from '../../types/runsheet'

export interface FormState {
  programme_type: ProgrammeType
  station_name: string
  broadcast_date: string
  start_time: string
  total_duration_minutes: number
  presenter_name: string
  max_advert_blocks_per_hour: number
  talk_music_preference: TalkMusicPreference
  deep_dive: boolean
}

export interface FormErrors {
  programme_type?: string
  station_name?: string
  broadcast_date?: string
  start_time?: string
  total_duration_minutes?: string
  presenter_name?: string
  max_advert_blocks_per_hour?: string
}

export const DEFAULT_FORM_VALUES: FormState = {
  programme_type: 'morning_show',
  station_name: '',
  broadcast_date: new Date().toISOString().slice(0, 10),
  start_time: '06:00',
  total_duration_minutes: 60,
  presenter_name: '',
  max_advert_blocks_per_hour: 3,
  talk_music_preference: 'balanced',
  deep_dive: false,
}
