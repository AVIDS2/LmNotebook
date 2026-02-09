import test from 'node:test'
import assert from 'node:assert/strict'
import { setTimeout as sleep } from 'node:timers/promises'

import { createVectorDeleteScheduler } from '../src/renderer/src/utils/vectorDeleteScheduler.mjs'

test('schedules vector delete asynchronously (non-blocking call site)', async () => {
  const calls = []
  const scheduler = createVectorDeleteScheduler(async (noteId) => {
    calls.push(noteId)
  })

  scheduler.schedule('n1')
  assert.equal(calls.length, 0)

  await sleep(5)
  assert.equal(calls.length, 1)
  assert.equal(calls[0], 'n1')
})

test('deduplicates the same note while request is in flight', async () => {
  const calls = []
  const scheduler = createVectorDeleteScheduler(async (noteId) => {
    calls.push(noteId)
    await sleep(25)
  })

  scheduler.schedule('n1')
  await sleep(5)
  scheduler.schedule('n1')
  await sleep(50)

  assert.equal(calls.length, 1)
  assert.equal(calls[0], 'n1')
})

test('keeps independent deletes for different notes', async () => {
  const calls = []
  const scheduler = createVectorDeleteScheduler(async (noteId) => {
    calls.push(noteId)
  })

  scheduler.schedule('n1')
  scheduler.schedule('n2')
  await sleep(10)

  assert.equal(calls.length, 2)
  assert.deepEqual(calls.sort(), ['n1', 'n2'])
})
