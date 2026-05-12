import type { SegmentType } from '../types/runsheet'

export const SEGMENT_COLOURS: Record<SegmentType, string> = {
  music:      '#22c55e',
  talk:       '#3b82f6',
  advert:     '#f59e0b',
  news:       '#8b5cf6',
  station_id: '#06b6d4',
  weather:    '#10b981',
  close:      '#6b7280',
  intro:      '#3b82f6',
}

export function segmentColour(type: SegmentType): string {
  return SEGMENT_COLOURS[type]
}
