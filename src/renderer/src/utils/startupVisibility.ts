interface StartupVisibilityInput {
  isBootstrapped: boolean
  totalNotesCount: number
  hasCurrentNote: boolean
  forceShow?: boolean
}

/**
 * Controls whether the startup/guide page should be shown.
 * Keep this logic centralized to avoid mount-time white-screen regressions
 * when entry components evolve.
 */
export function shouldShowStartupPage(input: StartupVisibilityInput): boolean {
  if (!input.isBootstrapped) return false
  if (input.forceShow) return true

  // First-run scenario: no notes exist yet.
  if (input.totalNotesCount <= 0) return true

  // Existing users: if a note is already selected, go directly to workspace.
  // If not selected, still enter workspace and let list selection logic decide.
  return false
}

