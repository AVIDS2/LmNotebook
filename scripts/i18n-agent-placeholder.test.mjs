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

test('zh-CN locale should not contain placeholder question-mark strings', async () => {
  const messages = await loadMessages()
  const hits = []

  function walk(node, trail = []) {
    if (typeof node === 'string') {
      if (/\?{2,}/.test(node)) hits.push(`${trail.join('.')}: ${node}`)
      return
    }
    if (Array.isArray(node)) {
      node.forEach((v, i) => walk(v, trail.concat(String(i))))
      return
    }
    if (node && typeof node === 'object') {
      for (const [k, v] of Object.entries(node)) walk(v, trail.concat(k))
    }
  }

  walk(messages['zh-CN'], ['zh-CN'])
  assert.equal(hits.length, 0, `zh-CN contains placeholder strings:\n${hits.join('\n')}`)
})
