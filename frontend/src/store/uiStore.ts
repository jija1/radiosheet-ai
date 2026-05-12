import { create } from 'zustand'

type ActiveView = 'input' | 'timeline' | 'history' | 'export'

interface UiState {
  activeView: ActiveView
  isApplyingFix: boolean
  fixingConflictId: string | null
  setActiveView: (view: ActiveView) => void
  setApplyingFix: (conflictId: string | null) => void
}

export const useUiStore = create<UiState>()((set) => ({
  activeView: 'input',
  isApplyingFix: false,
  fixingConflictId: null,

  setActiveView: (activeView) => set({ activeView }),

  setApplyingFix: (conflictId) =>
    set({
      isApplyingFix: conflictId !== null,
      fixingConflictId: conflictId,
    }),
}))
