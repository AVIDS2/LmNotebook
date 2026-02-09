export function createVectorSyncScheduler(syncFn, debounceMs = 1500) {
  const timers = new Map()
  const latestPayloads = new Map()

  async function flush(noteId) {
    const payload = latestPayloads.get(noteId)
    latestPayloads.delete(noteId)
    timers.delete(noteId)
    if (!payload) return

    try {
      await syncFn(payload)
    } catch (err) {
      // Keep scheduler non-blocking for editor UX.
      console.warn('[VectorSyncScheduler] sync failed:', err)
    }
  }

  function schedule(payload) {
    const noteId = payload?.noteId
    if (!noteId) return

    latestPayloads.set(noteId, payload)
    const existing = timers.get(noteId)
    if (existing) {
      clearTimeout(existing)
    }

    const timer = setTimeout(() => {
      void flush(noteId)
    }, debounceMs)
    timers.set(noteId, timer)
  }

  function cancel(noteId) {
    const timer = timers.get(noteId)
    if (timer) clearTimeout(timer)
    timers.delete(noteId)
    latestPayloads.delete(noteId)
  }

  function cancelAll() {
    for (const timer of timers.values()) {
      clearTimeout(timer)
    }
    timers.clear()
    latestPayloads.clear()
  }

  function pendingCount() {
    return timers.size
  }

  return {
    schedule,
    cancel,
    cancelAll,
    pendingCount
  }
}

