import test from 'node:test'
import assert from 'node:assert/strict'
import { extractHeadingsFromHtml, findActiveHeadingId } from '../src/renderer/src/utils/noteOutline.mjs'

test('extract headings from html with level and order', () => {
  const html = `
    <h1>Overview</h1>
    <p>Body</p>
    <h2>Scope</h2>
    <h3>Details</h3>
    <h2> </h2>
  `

  const headings = extractHeadingsFromHtml(html)
  assert.equal(headings.length, 3)
  assert.deepEqual(
    headings.map((h) => ({ id: h.id, level: h.level, text: h.text })),
    [
      { id: 'heading-0', level: 1, text: 'Overview' },
      { id: 'heading-1', level: 2, text: 'Scope' },
      { id: 'heading-2', level: 3, text: 'Details' }
    ]
  )
})

test('find active heading by current selection index', () => {
  const headings = [
    { id: 'heading-0', level: 1, text: 'Overview', start: 0 },
    { id: 'heading-1', level: 2, text: 'Scope', start: 120 },
    { id: 'heading-2', level: 2, text: 'Appendix', start: 260 }
  ]

  assert.equal(findActiveHeadingId(headings, 0), 'heading-0')
  assert.equal(findActiveHeadingId(headings, 150), 'heading-1')
  assert.equal(findActiveHeadingId(headings, 999), 'heading-2')
})
