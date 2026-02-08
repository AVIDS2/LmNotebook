import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function loadMessages() {
  const raw = await readFile(new URL('../src/renderer/src/i18n/messages.json', import.meta.url), 'utf8')
  return JSON.parse(raw.replace(/^\uFEFF/, ''))
}

function flatten(obj, prefix = '', out = new Set()) {
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      flatten(v, key, out)
    } else {
      out.add(key)
    }
  }
  return out
}

test('i18n messages should include zh-CN and en-US with aligned keys', async () => {
  const messages = await loadMessages()
  assert.ok(messages['zh-CN'], 'missing zh-CN locale')
  assert.ok(messages['en-US'], 'missing en-US locale')

  const zhKeys = flatten(messages['zh-CN'])
  const enKeys = flatten(messages['en-US'])

  assert.deepEqual([...zhKeys].sort(), [...enKeys].sort(), 'locale keys are not aligned')
  assert.ok(zhKeys.has('language.zh-CN'), 'missing language.zh-CN key')
  assert.ok(zhKeys.has('language.en-US'), 'missing language.en-US key')
})
