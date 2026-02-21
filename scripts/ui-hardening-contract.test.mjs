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
    /\.composer-model-wrapper\s*\{[\s\S]*?flex:\s*0\s+1\s+[0-9]+px[\s\S]*?min-width:\s*0/i,
    'model wrapper should be shrinkable so model text collapses first'
  )

  assert.match(
    agentBubble,
    /\.composer-model-btn__label\s*\{[\s\S]*?flex:\s*0\s+1\s+auto[\s\S]*?max-width:\s*calc\(100%\s*-\s*14px\)/i,
    'model label should truncate while keeping caret adjacent instead of pushing caret far right'
  )

  assert.match(
    agentBubble,
    /\.composer-model-btn\s*\{[\s\S]*?width:\s*auto[\s\S]*?max-width:\s*100%/i,
    'model button should size to content instead of exposing a wide empty clickable area'
  )

  assert.match(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-mode-btn--mode\s*\{[\s\S]*?min-width:\s*48px/i,
    'very narrow composer width should keep mode toggle compact without forcing it hidden'
  )

  const compactModeMedia = agentBubble.match(
    /@media\s*\(max-width:\s*780px\)\s*\{[\s\S]*?\.composer-mode-btn--mode[\s\S]*?\}\s*\}/i
  )?.[0]
  assert.ok(compactModeMedia, 'missing compact mode media block for composer controls')
  assert.doesNotMatch(
    compactModeMedia,
    /\.composer-review-btn\s*\{[\s\S]*?display:\s*none/i,
    'review toggle should not be hidden by broad viewport media query'
  )

  assert.match(
    agentBubble,
    /\.composer-review-btn\s*\{[\s\S]*?flex:\s*0\s+0\s+auto[\s\S]*?min-width:\s*max-content/i,
    'review toggle should keep intrinsic width and not collapse away'
  )

  assert.doesNotMatch(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-review-btn\s*\{[\s\S]*?display:\s*none/i,
    'review toggle should remain visible even on compact rows'
  )

  assert.match(
    agentBubble,
    /\.chat-input-bottom__right\s*\{[\s\S]*?position:\s*relative[\s\S]*?min-height:\s*32px[\s\S]*?z-index:\s*8/i,
    'right control rail should anchor overlayed review action without stretching row height'
  )

  assert.match(
    agentBubble,
    /\.composer-review-btn\s*\{[\s\S]*?position:\s*absolute[\s\S]*?bottom:\s*calc\(100%\s*\+\s*8px\)[\s\S]*?z-index:\s*10/i,
    'review action should be overlaid above send action instead of increasing control row height'
  )

  assert.match(
    agentBubble,
    /\.chat-input-bottom\s*\{[\s\S]*?position:\s*relative[\s\S]*?z-index:\s*6/i,
    'bottom control row should sit above textarea layer to keep review button fully clickable'
  )

  assert.doesNotMatch(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-mode-btn--mode\s*\{[\s\S]*?display:\s*none/i,
    'mode toggle should not be force-hidden by container query'
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
