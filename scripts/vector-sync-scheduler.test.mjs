import test from 'node:test'
import assert from 'node:assert/strict'
import { setTimeout as sleep } from 'node:timers/promises'

import { createVectorSyncScheduler } from '../src/renderer/src/utils/vectorSyncScheduler.mjs'

test('schedules one batch after debounce delay', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(
    async (batch) => {
      calls.push(batch)
    },
    { debounceMs: 25, flushIntervalMs: 5 }
  )

  scheduler.schedule({ noteId: 'n1', title: 'A', content: 'hello' })
  await sleep(45)

  assert.equal(calls.length, 1)
  assert.equal(calls[0].length, 1)
  assert.equal(calls[0][0].noteId, 'n1')
})

test('coalesces repeated updates for the same note', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(
    async (batch) => {
      calls.push(batch)
    },
    { debounceMs: 30, flushIntervalMs: 5 }
  )

  scheduler.schedule({ noteId: 'n1', title: 'T1', content: 'v1' })
  await sleep(10)
  scheduler.schedule({ noteId: 'n1', title: 'T2', content: 'v2' })
  await sleep(50)

  assert.equal(calls.length, 1)
  assert.equal(calls[0].length, 1)
  assert.equal(calls[0][0].title, 'T2')
  assert.equal(calls[0][0].content, 'v2')
})

test('keeps independent payloads for different notes', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(
    async (batch) => {
      calls.push(batch)
    },
    { debounceMs: 20, flushIntervalMs: 5 }
  )

  scheduler.schedule({ noteId: 'n1', title: 'A', content: '1' })
  scheduler.schedule({ noteId: 'n2', title: 'B', content: '2' })
  await sleep(45)

  const ids = calls
    .flat()
    .map((item) => item.noteId)
    .sort()

  assert.equal(ids.length, 2)
  assert.deepEqual(ids, ['n1', 'n2'])
})
