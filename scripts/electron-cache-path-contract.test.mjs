import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function readMain() {
  const raw = await readFile(new URL('../src/main/index.ts', import.meta.url), 'utf8')
  return raw.replace(/^\uFEFF/, '')
}

test('dev mode should isolate Chromium cache/session paths', async () => {
  const main = await readMain()

  assert.match(main, /if\s*\(!app\.isPackaged\)\s*\{[\s\S]*app\.setPath\('sessionData'/, 'missing dev sessionData override')
  assert.match(main, /appendSwitch\('disk-cache-dir'/, 'missing dev disk cache dir override')
})
