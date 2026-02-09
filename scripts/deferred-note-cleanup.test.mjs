import test from 'node:test'
import assert from 'node:assert/strict'
import { setTimeout as sleep } from 'node:timers/promises'

import { createDeferredEmptyNoteCleanup } from '../src/renderer/src/utils/deferredNoteCleanup.mjs'

test('removes empty stale note when it is no longer active', async () => {
  let currentNoteId = 'n2'
  const removed = []

  const cleanup = createDeferredEmptyNoteCleanup({
    getCurrentNoteId: () => currentNoteId,
    getById: async (id) => ({ id, title: '', plainText: '', isDeleted: false }),
    isEmpty: (note) => !note.title && !note.plainText,
    removeById: async (id) => {
      removed.push(id)
    }
  })

  const result = await cleanup({ id: 'n1', isDeleted: false })

  assert.equal(result, true)
  assert.deepEqual(removed, ['n1'])
})

test('skips removal when note becomes active again before delete', async () => {
  let currentNoteId = 'n2'
  const removed = []

  const cleanup = createDeferredEmptyNoteCleanup({
    getCurrentNoteId: () => currentNoteId,
    getById: async (id) => {
      await sleep(15)
      return { id, title: '', plainText: '', isDeleted: false }
    },
    isEmpty: (note) => !note.title && !note.plainText,
    removeById: async (id) => {
      removed.push(id)
    }
  })

  const pending = cleanup({ id: 'n1', isDeleted: false })
  await sleep(5)
  currentNoteId = 'n1'
  const result = await pending

  assert.equal(result, false)
  assert.equal(removed.length, 0)
})

test('deduplicates same note cleanup while one run is in-flight', async () => {
  const removed = []
  let reads = 0

  const cleanup = createDeferredEmptyNoteCleanup({
    getCurrentNoteId: () => 'n2',
    getById: async (id) => {
      reads += 1
      await sleep(20)
      return { id, title: '', plainText: '', isDeleted: false }
    },
    isEmpty: (note) => !note.title && !note.plainText,
    removeById: async (id) => {
      removed.push(id)
    }
  })

  const [a, b] = await Promise.all([
    cleanup({ id: 'n1', isDeleted: false }),
    cleanup({ id: 'n1', isDeleted: false })
  ])

  assert.equal(a, true)
  assert.equal(b, false)
  assert.equal(reads, 1)
  assert.deepEqual(removed, ['n1'])
})
