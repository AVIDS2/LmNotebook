import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function readText(path) {
  const raw = await readFile(new URL(`../${path}`, import.meta.url), 'utf8')
  return raw.replace(/^\uFEFF/, '')
}

test('agent composer should avoid control overlap on compact widths', async () => {
  const agentBubble = await readText('src/renderer/src/components/agent/AgentBubble.vue')

  assert.match(
    agentBubble,
    /\.chat-input-bottom\s*\{[\s\S]*?flex-wrap:\s*nowrap/i,
    'chat-input-bottom should stay single-line and not wrap into multiple rows'
  )

  assert.match(
    agentBubble,
    /\.composer-model-wrapper\s*\{[\s\S]*?flex:\s*1\s+1\s+auto[\s\S]*?min-width:\s*0/i,
    'model wrapper should be shrinkable so model text collapses first'
  )

  assert.match(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-review-btn\s*\{[\s\S]*?display:\s*none/i,
    'very narrow composer width should hide review toggle via container query'
  )
})

test('note editor should isolate undo/redo history per note', async () => {
  const noteEditor = await readText('src/renderer/src/components/notes/NoteEditor.vue')

  assert.match(
    noteEditor,
    /import\s*\{[^}]*undoDepth[^}]*redoDepth[^}]*\}\s*from\s*'@tiptap\/pm\/history'/,
    'undo/redo availability should be based on history depth, not command capability probing'
  )

  assert.match(
    noteEditor,
    /state\.reconfigure\(\s*\{\s*plugins:\s*state\.plugins\s*\}\s*\)/,
    'switching notes should reset history plugin state to avoid undoing into previous/empty notes'
  )
})

test('data settings should expose embedding model config entry', async () => {
  const dataSettings = await readText('src/renderer/src/components/sidebar/DataSettings.vue')
  const preloadTypes = await readText('src/preload/index.d.ts')
  const mainDb = await readText('src/main/database.ts')

  assert.match(dataSettings, /v-model="config\.embeddingMode"/, 'missing embedding mode selector in settings UI')
  assert.match(dataSettings, /v-model="config\.embeddingModel"/, 'missing embedding model input in settings UI')

  assert.match(preloadTypes, /embeddingMode:\s*string/, 'preload AppConfig should include embeddingMode')
  assert.match(preloadTypes, /embeddingModel:\s*string/, 'preload AppConfig should include embeddingModel')

  assert.match(mainDb, /embeddingMode:\s*string/, 'main AppConfig should include embeddingMode')
  assert.match(mainDb, /embeddingModel:\s*string/, 'main AppConfig should include embeddingModel')
})

test('agent bubble should not keep legacy ORIGIN wordmark', async () => {
  const agentBubble = await readText('src/renderer/src/components/agent/AgentBubble.vue')

  assert.ok(!agentBubble.includes('<span>ORIGIN</span>'), 'legacy ORIGIN wordmark should be replaced')
  assert.ok(!agentBubble.includes('Origin asterisk logo'), 'legacy origin-specific logo comment should be removed')
})
