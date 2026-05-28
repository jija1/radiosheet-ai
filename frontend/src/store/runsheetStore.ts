import { create } from 'zustand'
import type {
  ComplianceViolation,
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
  complianceScore: number
  complianceRisk: string
  complianceViolations: ComplianceViolation[]
  deepDiveInsights: string[]
  isLoading: boolean
  error: string | null
  setRunsheet: (runsheet: RunSheetResponse) => void
  updateSegments: (segments: Segment[]) => void
  updateConflicts: (conflicts: Conflict[]) => void
  updateRecommendations: (recommendations: Recommendation[]) => void
  updateStats: (stats: RunSheetStats) => void
  setCompliance: (score: number, risk: string, violations: ComplianceViolation[]) => void
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
  complianceScore: 100,
  complianceRisk: 'compliant',
  complianceViolations: [],
  deepDiveInsights: [],
  isLoading: false,
  error: null,

  setRunsheet: (runsheet) =>
    set({
      currentRunsheet: runsheet,
      segments: runsheet.segments,
      conflicts: runsheet.conflicts,
      recommendations: runsheet.recommendations,
      stats: runsheet.stats,
      complianceScore: runsheet.compliance_score,
      complianceRisk: runsheet.compliance_risk,
      complianceViolations: runsheet.compliance_violations,
      deepDiveInsights: runsheet.deep_dive_insights ?? [],
    }),

  updateSegments: (segments) => set({ segments }),

  updateConflicts: (conflicts) => set({ conflicts }),

  updateRecommendations: (recommendations) => set({ recommendations }),

  updateStats: (stats) => set({ stats }),

  setCompliance: (complianceScore, complianceRisk, complianceViolations) =>
    set({ complianceScore, complianceRisk, complianceViolations }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearRunsheet: () =>
    set({
      currentRunsheet: null,
      segments: [],
      conflicts: [],
      recommendations: [],
      stats: null,
      complianceScore: 100,
      complianceRisk: 'compliant',
      complianceViolations: [],
      deepDiveInsights: [],
      isLoading: false,
      error: null,
    }),
}))
