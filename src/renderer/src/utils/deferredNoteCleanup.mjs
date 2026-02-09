/**
 * Create a safe deferred empty-note cleanup runner.
 *
 * @param {{
 *   getCurrentNoteId: () => string | null
 *   getById: (noteId: string) => Promise<any>
 *   isEmpty: (note: any) => boolean
 *   removeById: (noteId: string) => Promise<void>
 * }} deps
 */
export function createDeferredEmptyNoteCleanup(deps) {
  const inFlight = new Set()

  return async function cleanup(snapshot) {
    if (!snapshot?.id || snapshot.isDeleted) return false
    const noteId = snapshot.id
    if (inFlight.has(noteId)) return false

    inFlight.add(noteId)
    try {
      // User switched back to this note, skip cleanup.
      if (deps.getCurrentNoteId() === noteId) return false

      const latest = await deps.getById(noteId)
      if (!latest) return false
      if (latest.isDeleted) return false

      // Re-check active note after async boundary to avoid race deletion.
      if (deps.getCurrentNoteId() === noteId) return false
      if (!deps.isEmpty(latest)) return false

      await deps.removeById(noteId)
      return true
    } finally {
      inFlight.delete(noteId)
    }
  }
}
