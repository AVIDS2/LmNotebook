import test from 'node:test'
import assert from 'node:assert/strict'
import { setTimeout as sleep } from 'node:timers/promises'

import { createVectorSyncScheduler } from '../src/renderer/src/utils/vectorSyncScheduler.mjs'

test('schedules one sync after debounce delay', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(async (payload) => {
    calls.push(payload)
  }, 25)

  scheduler.schedule({ noteId: 'n1', title: 'A', content: 'hello' })
  await sleep(40)

  assert.equal(calls.length, 1)
  assert.equal(calls[0].noteId, 'n1')
})

test('coalesces repeated updates for the same note', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(async (payload) => {
    calls.push(payload)
  }, 30)

  scheduler.schedule({ noteId: 'n1', title: 'T1', content: 'v1' })
  await sleep(10)
  scheduler.schedule({ noteId: 'n1', title: 'T2', content: 'v2' })
  await sleep(45)

  assert.equal(calls.length, 1)
  assert.equal(calls[0].title, 'T2')
  assert.equal(calls[0].content, 'v2')
})

test('keeps independent timers for different notes', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(async (payload) => {
    calls.push(payload)
  }, 20)

  scheduler.schedule({ noteId: 'n1', title: 'A', content: '1' })
  scheduler.schedule({ noteId: 'n2', title: 'B', content: '2' })
  await sleep(40)

  assert.equal(calls.length, 2)
  const ids = calls.map((c) => c.noteId).sort()
  assert.deepEqual(ids, ['n1', 'n2'])
})

