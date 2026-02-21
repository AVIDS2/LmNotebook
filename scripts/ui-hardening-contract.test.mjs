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

  assert.doesNotMatch(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-model-wrapper\s*\{[\s\S]*?max-width:\s*170px/i,
    'model wrapper should not be hard-capped too aggressively at 170px when there is still row space'
  )

  assert.doesNotMatch(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*360px\)[\s\S]*?\.composer-model-wrapper\s*\{[\s\S]*?max-width:\s*145px/i,
    'narrow-row fallback should still reserve enough room for common model names'
  )

  assert.match(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-model-wrapper\s*\{[\s\S]*?max-width:\s*min\(72cqw,\s*300px\)/i,
    'compact row should size model wrapper proportionally to available container width'
  )

  assert.match(
    agentBubble,
    /\.composer-model-wrapper\s*\{(?=[\s\S]*flex:\s*1\s+1\s+260px\s*!important)(?=[\s\S]*max-width:\s*none\s*!important)[\s\S]*?\}/i,
    'model wrapper should grow with available row space before truncating model text'
  )

  assert.match(
    agentBubble,
    /\.composer-model-btn\s*\{[\s\S]*?width:\s*fit-content\s*!important[\s\S]*?max-width:\s*100%/i,
    'model button should size to content instead of exposing a wide empty clickable area'
  )

  assert.match(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-model-wrapper\s*\{[\s\S]*?max-width:\s*min\(72cqw,\s*300px\)/i,
    'compact width rules should still reserve enough model space for common full names'
  )

  assert.match(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*360px\)[\s\S]*?\.composer-model-wrapper\s*\{[\s\S]*?max-width:\s*min\(74cqw,\s*260px\)/i,
    'very narrow widths should keep model cap proportional instead of forcing premature truncation'
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
    /\.composer-review-btn\s*\{[\s\S]*?max-width:\s*108px[\s\S]*?white-space:\s*nowrap[\s\S]*?text-overflow:\s*ellipsis/i,
    'review toggle should remain compact while preserving readable label text'
  )

  assert.doesNotMatch(
    agentBubble,
    /@container\s+composerRow\s*\(max-width:\s*420px\)[\s\S]*?\.composer-review-btn\s*\{[\s\S]*?display:\s*none/i,
    'review toggle should remain visible even on compact rows'
  )

  assert.match(
    agentBubble,
    /\.chat-input-bottom__right\s*\{(?=[\s\S]*position:\s*relative)(?=[\s\S]*height:\s*32px)(?=[\s\S]*align-items:\s*flex-end)(?=[\s\S]*z-index:\s*8)[\s\S]*?\}/i,
    'right control rail should keep compact send-row height while anchoring review separately'
  )

  assert.doesNotMatch(
    agentBubble,
    /\.chat-input-bottom__right\s*\{[\s\S]*?margin-left:\s*auto[\s\S]*?\}/i,
    'right control rail should not consume free space with auto margin, otherwise model width collapses early'
  )

  assert.match(
    agentBubble,
    /\.composer-review-btn\s*\{(?=[\s\S]*position:\s*absolute)(?=[\s\S]*bottom:\s*calc\(100%\s*\+\s*10px\))(?=[\s\S]*right:\s*0)(?=[\s\S]*pointer-events:\s*auto)[\s\S]*?\}/i,
    'review action should be overlaid above send without inflating composer row height'
  )

  assert.match(
    agentBubble,
    /composer-review-btn--auto/,
    'review action should expose explicit auto mode class for clear visual state'
  )

  assert.match(
    agentBubble,
    /composer-review-btn--manual/,
    'review action should expose explicit manual mode class for clear visual state'
  )

  assert.match(
    agentBubble,
    /\.composer-review-btn--auto\s*\{[\s\S]*?background:/i,
    'auto review state should have dedicated background styling'
  )

  assert.match(
    agentBubble,
    /\.composer-review-btn--manual\s*\{[\s\S]*?background:/i,
    'manual review state should have dedicated background styling'
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

  assert.doesNotMatch(
    agentBubble,
    /\/\*\s*Composer:\s*compact shadcn-like layout\s*\*\//i,
    'legacy duplicated composer block marker should be removed after style dedupe'
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
    /EditorState\.create\(\s*\{[\s\S]*plugins:\s*state\.plugins[\s\S]*\}\s*\)/,
    'switching notes should recreate editor state so history is truly reset per note'
  )

  assert.match(
    noteEditor,
    /\.setMeta\(\s*['"]addToHistory['"]\s*,\s*false\s*\)[\s\S]*?\.setContent\(/,
    'programmatic note-content hydration should not create undo entries'
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

test('workspace shell should use settings-grade panelized layout', async () => {
  const appVue = await readText('src/renderer/src/App.vue')

  assert.match(
    appVue,
    /\.main-content\s*\{[\s\S]*?padding:\s*10px[\s\S]*?gap:\s*10px/i,
    'main workspace should use panelized spacing like settings modal'
  )

  assert.match(
    appVue,
    /\.panel\s*\{[\s\S]*?border:\s*1px\s+solid[\s\S]*?border-radius:\s*14px/i,
    'workspace panels should have card-like border and radius'
  )

  assert.match(
    appVue,
    /:deep\(\.note-editor__toolbar\)\s*\{[\s\S]*?border-radius:\s*12px/i,
    'editor toolbar should be elevated as a shadcn-like surface'
  )
})

test('agent review state colors should remain neutral (no green/orange accents)', async () => {
  const agentBubble = await readText('src/renderer/src/components/agent/AgentBubble.vue')

  const reviewAutoBlock = agentBubble.match(/\.composer-review-btn--auto\s*\{[\s\S]*?\}/i)?.[0] || ''
  const reviewManualBlock = agentBubble.match(/\.composer-review-btn--manual\s*\{[\s\S]*?\}/i)?.[0] || ''

  assert.ok(reviewAutoBlock.length > 0, 'missing auto review state block')
  assert.ok(reviewManualBlock.length > 0, 'missing manual review state block')

  assert.doesNotMatch(
    reviewAutoBlock,
    /#10b981|#065f46/i,
    'auto review state should avoid saturated green accents'
  )

  assert.doesNotMatch(
    reviewManualBlock,
    /#f59e0b|#92400e/i,
    'manual review state should avoid saturated orange accents'
  )
})

test('workspace should provide full-shell visual refresh contract', async () => {
  const refresh = await readText('src/renderer/src/assets/styles/workspace-refresh.scss')

  assert.match(
    refresh,
    /\.app-container\s+\.main-content\s*\{[\s\S]*?background:[\s\S]*?padding:\s*12px[\s\S]*?gap:\s*12px/i,
    'workspace shell should define a stronger panelized canvas background and spacing'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.note-list__header\s*\{[\s\S]*?padding:\s*12px\s+12px\s+8px/i,
    'left note list header should receive a visible refreshed structure'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.note-editor\s+\.ProseMirror\s*\{[\s\S]*?max-width:\s*860px[\s\S]*?line-height:\s*(?:1\.88|var\(--line-height-relaxed\))/i,
    'editor prose area should expose upgraded reading rhythm and width'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.agent-chat\.sidebar-mode\s+\.message--assistant\s+\.message\s*\{(?=[\s\S]*?background:\s*transparent)(?=[\s\S]*?border:\s*none)[\s\S]*?\}/i,
    'right assistant output should stay backgroundless and integrated with chat canvas'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.agent-chat\.sidebar-mode\s+\.status-update\s*\{(?=[\s\S]*?background:\s*transparent)(?=[\s\S]*?border:\s*none)[\s\S]*?\}/i,
    'right status rows should stay backgroundless and never render as gray pills'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.agent-chat\.sidebar-mode\s+\.message--user\s+\.message\s*\{[\s\S]*?border-radius:\s*14px/i,
    'right user bubbles should have dedicated refreshed bubble styling'
  )

  assert.match(
    refresh,
    /\.app-container\s+\.rail-btn\s*\{[\s\S]*?width:\s*38px[\s\S]*?height:\s*38px/i,
    'left rail controls should have updated size and touch target'
  )
})

test('global typography tokens should be defined for cross-surface consistency', async () => {
  const globalStyles = await readText('src/renderer/src/assets/styles/global.scss')
  const refreshStyles = await readText('src/renderer/src/assets/styles/workspace-refresh.scss')

  assert.match(globalStyles, /--font-family-sans:/, 'missing sans typography token in global styles')
  assert.match(globalStyles, /--font-size-md:/, 'missing medium font-size token in global styles')
  assert.match(globalStyles, /--line-height-relaxed:/, 'missing relaxed line-height token in global styles')
  assert.match(globalStyles, /body\s*\{[\s\S]*?font-family:\s*var\(--font-family-sans\)/i, 'body should consume global sans token')

  assert.match(refreshStyles, /font-size:\s*var\(--font-size-md\)/i, 'workspace refresh should consume font-size tokens')
  assert.match(refreshStyles, /line-height:\s*var\(--line-height-relaxed\)/i, 'workspace refresh should consume line-height tokens')
})

test('renderer should define manual chunk strategy for heavy modules', async () => {
  const viteConfig = await readText('electron.vite.config.ts')

  assert.match(viteConfig, /manualChunks\(id\)/, 'renderer build should define manual chunk strategy')
  assert.match(viteConfig, /vendor-mammoth/, 'chunk strategy should isolate mammoth payload')
  assert.match(viteConfig, /vendor-editor/, 'chunk strategy should isolate editor payload')
  assert.match(viteConfig, /vendor-richtext/, 'chunk strategy should isolate richtext payload')
  assert.match(viteConfig, /vendor-markdown/, 'chunk strategy should isolate markdown payload')
})

test('release readiness automation should exist and be wired in npm scripts', async () => {
  const packageJson = await readText('package.json')
  const readinessScript = await readText('scripts/release-readiness.mjs')

  assert.match(packageJson, /"verify:release"\s*:\s*"node scripts\/release-readiness\.mjs"/, 'package scripts should expose verify:release')
  assert.match(readinessScript, /ui-hardening-contract\.test\.mjs/, 'release readiness should execute ui hardening contract tests')
  assert.match(readinessScript, /['"]npm['"]\s*,\s*\[\s*['"]run['"]\s*,\s*['"]build['"]\s*\]/, 'release readiness should execute production build verification')
  assert.match(readinessScript, /Release Readiness Checklist/, 'release readiness script should print a checklist summary')
})

test('selected note context should be visible in composer before send', async () => {
  const agentBubble = await readText('src/renderer/src/components/agent/AgentBubble.vue')

  assert.match(
    agentBubble,
    /v-if="composerAttachments\.length\s*\|\|\s*selectedContextNote"/,
    'composer context note should render inside the same attachment row as files/images'
  )

  assert.match(
    agentBubble,
    /composer-attachment-chip--note/,
    'context note should use attachment-chip styling family so it stays on the same row'
  )

  assert.match(
    agentBubble,
    /@click="clearContextNote"/,
    'selected note context chip should be dismissible'
  )

  assert.doesNotMatch(
    agentBubble,
    /composer-context-note-chip/,
    'legacy standalone context-note row should be removed'
  )
})
