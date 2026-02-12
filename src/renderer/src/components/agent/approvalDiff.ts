import type { Note } from '@/database/noteRepository'

export interface NoteSnapshot {
  id: string
  title: string
  content: string
  markdownSource: string | null
}

export type DiffOp = 'same' | 'add' | 'del'
export type DiffBlockKind = 'unchanged' | 'modified' | 'added' | 'removed'

export interface DiffLine {
  op: DiffOp
  text: string
}

export interface DiffBlockView {
  id: string
  label: string
  kind: DiffBlockKind
  lines: DiffLine[]
}

interface TextBlock {
  id: string
  label: string
  text: string
  key: string
}

export function snapshotFromNote(note: Note): NoteSnapshot {
  return {
    id: note.id,
    title: note.title || '',
    content: note.content || '',
    markdownSource: note.markdownSource ?? null
  }
}

export function snapshotsDiffer(a: NoteSnapshot, b: NoteSnapshot): boolean {
  return a.title !== b.title || a.content !== b.content || (a.markdownSource ?? '') !== (b.markdownSource ?? '')
}

function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return (div.textContent || div.innerText || '').trim()
}

export function snapshotToText(snapshot: NoteSnapshot): string {
  const raw = (snapshot.markdownSource && snapshot.markdownSource.trim())
    ? snapshot.markdownSource
    : stripHtml(snapshot.content)
  return raw.trim()
}

export function previewText(input: string, maxLen = 220): string {
  if (!input) return '(empty)'
  return input.length > maxLen ? `${input.slice(0, maxLen)}...` : input
}

function countByRegex(text: string, regex: RegExp): number {
  const matches = text.match(regex)
  return matches ? matches.length : 0
}

function normalizeKey(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s#-]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function makeLabelFromText(text: string, fallback: string): string {
  const firstLine = text.split('\n').find(line => line.trim())?.trim() || ''
  if (!firstLine) return fallback
  return firstLine.length > 40 ? `${firstLine.slice(0, 40)}...` : firstLine
}

function splitIntoBlocks(text: string): TextBlock[] {
  const normalized = text.replace(/\r\n/g, '\n').trim()
  if (!normalized) return []
  const rawBlocks = normalized
    .split(/\n{2,}/)
    .map(block => block.trim())
    .filter(Boolean)
  return rawBlocks.map((block, idx) => {
    const label = makeLabelFromText(block, `Block ${idx + 1}`)
    const key = normalizeKey(label)
    return {
      id: `b-${idx}`,
      label,
      text: block,
      key
    }
  })
}

function buildLcsIndices(left: string[], right: string[]): Array<[number, number]> {
  const m = left.length
  const n = right.length
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i -= 1) {
    for (let j = n - 1; j >= 0; j -= 1) {
      if (left[i] === right[j]) dp[i][j] = dp[i + 1][j + 1] + 1
      else dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }
  const pairs: Array<[number, number]> = []
  let i = 0
  let j = 0
  while (i < m && j < n) {
    if (left[i] === right[j]) {
      pairs.push([i, j])
      i += 1
      j += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i += 1
    } else {
      j += 1
    }
  }
  return pairs
}

function buildLineDiff(beforeText: string, afterText: string): DiffLine[] {
  const before = beforeText.split('\n')
  const after = afterText.split('\n')
  const pairs = buildLcsIndices(before, after)
  const lines: DiffLine[] = []
  let i = 0
  let j = 0
  for (const [pi, pj] of pairs) {
    while (i < pi) {
      lines.push({ op: 'del', text: before[i] })
      i += 1
    }
    while (j < pj) {
      lines.push({ op: 'add', text: after[j] })
      j += 1
    }
    lines.push({ op: 'same', text: before[pi] })
    i = pi + 1
    j = pj + 1
  }
  while (i < before.length) {
    lines.push({ op: 'del', text: before[i] })
    i += 1
  }
  while (j < after.length) {
    lines.push({ op: 'add', text: after[j] })
    j += 1
  }
  return lines
}

function pairSegments(beforeSeg: TextBlock[], afterSeg: TextBlock[]): DiffBlockView[] {
  const out: DiffBlockView[] = []
  let i = 0
  let j = 0
  while (i < beforeSeg.length && j < afterSeg.length) {
    const b = beforeSeg[i]
    const a = afterSeg[j]
    out.push({
      id: `${b.id}:${a.id}`,
      label: a.label || b.label,
      kind: 'modified',
      lines: buildLineDiff(b.text, a.text)
    })
    i += 1
    j += 1
  }
  while (i < beforeSeg.length) {
    const b = beforeSeg[i]
    out.push({
      id: `${b.id}:removed`,
      label: b.label,
      kind: 'removed',
      lines: b.text.split('\n').map(line => ({ op: 'del' as const, text: line }))
    })
    i += 1
  }
  while (j < afterSeg.length) {
    const a = afterSeg[j]
    out.push({
      id: `added:${a.id}`,
      label: a.label,
      kind: 'added',
      lines: a.text.split('\n').map(line => ({ op: 'add' as const, text: line }))
    })
    j += 1
  }
  return out
}

export function buildStructuredDiff(beforeText: string, afterText: string): DiffBlockView[] {
  const beforeBlocks = splitIntoBlocks(beforeText)
  const afterBlocks = splitIntoBlocks(afterText)
  const pairs = buildLcsIndices(beforeBlocks.map(b => b.key), afterBlocks.map(b => b.key))
  const out: DiffBlockView[] = []
  let bi = 0
  let ai = 0
  for (const [pb, pa] of pairs) {
    if (bi < pb || ai < pa) {
      out.push(...pairSegments(beforeBlocks.slice(bi, pb), afterBlocks.slice(ai, pa)))
    }
    const b = beforeBlocks[pb]
    const a = afterBlocks[pa]
    if (b.text === a.text) {
      out.push({
        id: `${b.id}:${a.id}`,
        label: a.label || b.label,
        kind: 'unchanged',
        lines: [{ op: 'same', text: previewText(a.text, 280) }]
      })
    } else {
      out.push({
        id: `${b.id}:${a.id}`,
        label: a.label || b.label,
        kind: 'modified',
        lines: buildLineDiff(b.text, a.text)
      })
    }
    bi = pb + 1
    ai = pa + 1
  }
  if (bi < beforeBlocks.length || ai < afterBlocks.length) {
    out.push(...pairSegments(beforeBlocks.slice(bi), afterBlocks.slice(ai)))
  }
  return out
}

export function summarizeChange(before: NoteSnapshot, after: NoteSnapshot): string {
  const beforeText = snapshotToText(before)
  const afterText = snapshotToText(after)
  const beforeHeadings = countByRegex(beforeText, /^#{1,6}\s/mg)
  const afterHeadings = countByRegex(afterText, /^#{1,6}\s/mg)
  const beforeLists = countByRegex(beforeText, /^\s*([-*+]|\d+\.)\s/mg)
  const afterLists = countByRegex(afterText, /^\s*([-*+]|\d+\.)\s/mg)
  const deltaChars = afterText.length - beforeText.length
  return `chars ${beforeText.length} -> ${afterText.length} (${deltaChars >= 0 ? '+' : ''}${deltaChars}), headings ${beforeHeadings} -> ${afterHeadings}, lists ${beforeLists} -> ${afterLists}`
}
