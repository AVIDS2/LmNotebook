export function createVectorDeleteScheduler(deleteFn) {
  const queue = []
  const queued = new Set()
  const inFlight = new Set()
  let draining = false

  async function drain() {
    if (draining) return
    draining = true

    while (queue.length > 0) {
      const noteId = queue.shift()
      if (!noteId) continue

      queued.delete(noteId)
      inFlight.add(noteId)
      try {
        await deleteFn(noteId)
      } catch (err) {
        // Keep delete path non-blocking for UI interactions (note switching, list actions).
        console.warn('[VectorDeleteScheduler] delete failed:', err)
      } finally {
        inFlight.delete(noteId)
      }
    }

    draining = false
  }

  function schedule(noteId) {
    if (!noteId) return
    if (queued.has(noteId) || inFlight.has(noteId)) return

    queued.add(noteId)
    queue.push(noteId)
    queueMicrotask(() => {
      void drain()
    })
  }

  function pendingCount() {
    return queued.size + inFlight.size
  }

  return {
    schedule,
    pendingCount
  }
}
