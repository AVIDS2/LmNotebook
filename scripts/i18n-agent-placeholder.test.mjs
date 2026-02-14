import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function loadMessages() {
  const raw = await readFile(new URL('../src/renderer/src/i18n/messages.json', import.meta.url), 'utf8')
  return JSON.parse(raw.replace(/^\uFEFF/, ''))
}

test('zh-CN composer placeholder should be readable Chinese text', async () => {
  const messages = await loadMessages()
  const value = messages['zh-CN']?.agent?.composerPlaceholder

  assert.equal(typeof value, 'string', 'composerPlaceholder should be a string')
  assert.ok(value.trim().length > 0, 'composerPlaceholder should not be empty')
  assert.ok(!/^\?+/.test(value.trim()), 'composerPlaceholder should not start with question marks')
  assert.match(value, /\p{Script=Han}/u, 'composerPlaceholder should contain Chinese characters')
})

test('zh-CN model menu label should be readable Chinese text', async () => {
  const messages = await loadMessages()
  const value = messages['zh-CN']?.agent?.menuChooseModel

  assert.equal(typeof value, 'string', 'menuChooseModel should be a string')
  assert.ok(value.trim().length > 0, 'menuChooseModel should not be empty')
  assert.ok(!/^\?+/.test(value.trim()), 'menuChooseModel should not start with question marks')
  assert.match(value, /\p{Script=Han}/u, 'menuChooseModel should contain Chinese characters')
})
