import { create } from 'zustand'
import type {
  Conflict,
  Recommendation,
  RunSheetResponse,
  RunSheetStats,
  Segment,
} from '../types/runsheet'

interface RunsheetState {
  currentRunsheet: RunSheetResponse | null
  segments: Segment[]
  conflicts: Conflict[]
  recommendations: Recommendation[]
  stats: RunSheetStats | null
  isLoading: boolean
  error: string | null
  setRunsheet: (runsheet: RunSheetResponse) => void
  updateSegments: (segments: Segment[]) => void
  updateConflicts: (conflicts: Conflict[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearRunsheet: () => void
}

export const useRunsheetStore = create<RunsheetState>()((set) => ({
  currentRunsheet: null,
  segments: [],
  conflicts: [],
  recommendations: [],
  stats: null,
  isLoading: false,
  error: null,

  setRunsheet: (runsheet) =>
    set({
      currentRunsheet: runsheet,
      segments: runsheet.segments,
      conflicts: runsheet.conflicts,
      recommendations: runsheet.recommendations,
      stats: runsheet.stats,
    }),

  updateSegments: (segments) => set({ segments }),

  updateConflicts: (conflicts) => set({ conflicts }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearRunsheet: () =>
    set({
      currentRunsheet: null,
      segments: [],
      conflicts: [],
      recommendations: [],
      stats: null,
      isLoading: false,
      error: null,
    }),
}))
