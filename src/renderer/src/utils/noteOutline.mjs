/**
 * @typedef {{ id: string; level: number; text: string; start: number }} NoteHeading
 */

/**
 * Extract heading outline from editor HTML.
 * @param {string} html
 * @returns {NoteHeading[]}
 */
export function extractHeadingsFromHtml(html) {
  if (!html || typeof html !== 'string') return []
  const matches = [...html.matchAll(/<h([1-3])[^>]*>([\s\S]*?)<\/h\1>/gi)]
  let cursor = 0

  return matches
    .map((match, index) => {
      const level = Number(match[1])
      const text = stripHtml(match[2]).trim()
      if (!text) return null
      const full = match[0] || ''
      const found = html.indexOf(full, cursor)
      const start = found >= 0 ? found : cursor
      cursor = start + full.length
      return { id: `heading-${index}`, level, text, start }
    })
    .filter(Boolean)
}

/**
 * @param {NoteHeading[]} headings
 * @param {number} selectionIndex
 * @returns {string}
 */
export function findActiveHeadingId(headings, selectionIndex) {
  if (!Array.isArray(headings) || headings.length === 0) return ''
  const index = Number.isFinite(selectionIndex) ? selectionIndex : 0
  let active = headings[0]
  for (const item of headings) {
    if (index >= item.start) active = item
    else break
  }
  return active?.id || ''
}

function stripHtml(input) {
  return String(input)
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
}
