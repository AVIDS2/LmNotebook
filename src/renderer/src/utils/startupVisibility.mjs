/**
 * @param {{ isBootstrapped: boolean, totalNotesCount: number, hasCurrentNote: boolean, forceShow: boolean }} input
 */
export function shouldShowStartupPage(input) {
  if (!input.isBootstrapped) return false
  if (input.forceShow) return true
  return input.totalNotesCount === 0 && !input.hasCurrentNote
}
