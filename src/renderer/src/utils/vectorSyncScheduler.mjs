export function createVectorSyncScheduler(
  syncFn,
  {
    debounceMs = 1500,
    flushIntervalMs = 2600,
    retryDelayMs = 2200,
    maxBatchSize = 16
  } = {}
) {
  const perNoteTimers = new Map()
  const latestPayloads = new Map()
  const readyNoteIds = new Set()
  let flushTimer = null
  let flushInFlight = false

  function markReady(noteId) {
    if (!latestPayloads.has(noteId)) return
    readyNoteIds.add(noteId)
    scheduleFlush(0)
  }

  function schedule(payload) {
    const noteId = payload?.noteId
    if (!noteId) return

    latestPayloads.set(noteId, payload)
    const existing = perNoteTimers.get(noteId)
    if (existing) clearTimeout(existing)

    const timer = setTimeout(() => {
      perNoteTimers.delete(noteId)
      markReady(noteId)
    }, debounceMs)
    perNoteTimers.set(noteId, timer)
  }

  function scheduleFlush(delay = flushIntervalMs) {
    if (flushTimer) return
    flushTimer = setTimeout(() => {
      flushTimer = null
      void flushReady()
    }, delay)
  }

  async function flushReady() {
    if (flushInFlight) return
    if (readyNoteIds.size === 0) return

    flushInFlight = true
    let batch = []
    try {
      const noteIds = Array.from(readyNoteIds).slice(0, maxBatchSize)
      noteIds.forEach((id) => readyNoteIds.delete(id))
      batch = noteIds
        .map((id) => latestPayloads.get(id))
        .filter(Boolean)

      for (const payload of batch) {
        latestPayloads.delete(payload.noteId)
      }

      if (batch.length === 0) return
      await syncFn(batch)
    } catch (err) {
      console.warn('[VectorSyncScheduler] batch sync failed:', err)
      // Requeue failed payloads for retry.
      for (const payload of batch) {
        latestPayloads.set(payload.noteId, payload)
        readyNoteIds.add(payload.noteId)
      }
      scheduleFlush(retryDelayMs)
    } finally {
      flushInFlight = false
      if (readyNoteIds.size > 0) {
        scheduleFlush(0)
      }
    }
  }

  async function flushAll() {
    // Promote debounced payloads into ready queue first.
    for (const [noteId, timer] of perNoteTimers.entries()) {
      clearTimeout(timer)
      perNoteTimers.delete(noteId)
      readyNoteIds.add(noteId)
    }
    await flushReady()
  }

  function cancel(noteId) {
    const timer = perNoteTimers.get(noteId)
    if (timer) clearTimeout(timer)
    perNoteTimers.delete(noteId)
    latestPayloads.delete(noteId)
    readyNoteIds.delete(noteId)
  }

  function cancelAll() {
    for (const timer of perNoteTimers.values()) {
      clearTimeout(timer)
    }
    perNoteTimers.clear()
    latestPayloads.clear()
    readyNoteIds.clear()
    if (flushTimer) {
      clearTimeout(flushTimer)
      flushTimer = null
    }
  }

  function pendingCount() {
    return perNoteTimers.size + readyNoteIds.size
  }

  return {
    schedule,
    flushAll,
    cancel,
    cancelAll,
    pendingCount
  }
}
