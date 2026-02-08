import test from 'node:test'
import assert from 'node:assert/strict'
import { shouldShowStartupPage } from '../src/renderer/src/utils/startupVisibility.mjs'

test('shows startup when force preview is enabled even with notes', () => {
  const visible = shouldShowStartupPage({
    isBootstrapped: true,
    totalNotesCount: 3,
    hasCurrentNote: true,
    forceShow: true
  })

  assert.equal(visible, true)
})

test('hides startup by default when notes exist', () => {
  const visible = shouldShowStartupPage({
    isBootstrapped: true,
    totalNotesCount: 1,
    hasCurrentNote: true,
    forceShow: false
  })

  assert.equal(visible, false)
})
