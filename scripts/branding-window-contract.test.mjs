import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function readText(path) {
  const raw = await readFile(new URL(`../${path}`, import.meta.url), 'utf8')
  return raw.replace(/^\uFEFF/, '')
}

test('package and shell branding should use LmNotebook', async () => {
  const pkgRaw = await readText('package.json')
  const pkg = JSON.parse(pkgRaw)

  assert.equal(pkg.build?.productName, 'LmNotebook')
  assert.equal(pkg.build?.nsis?.shortcutName, 'LmNotebook')

  const appVue = await readText('src/renderer/src/App.vue')
  const startupVue = await readText('src/renderer/src/components/common/StartupPage.vue')
  const mainTs = await readText('src/main/index.ts')

  assert.ok(!appVue.includes('Origin Notes'), 'App title should not use Origin Notes')
  assert.ok(!startupVue.includes('Origin Notes'), 'Startup page should not use Origin Notes')
  assert.ok(!mainTs.includes("tray.setToolTip('Origin Notes')"), 'Tray tooltip should use LmNotebook')
})

test('main process should enforce single-instance and close-to-tray behavior', async () => {
  const mainTs = await readText('src/main/index.ts')

  assert.match(mainTs, /requestSingleInstanceLock\(\)/, 'single-instance lock is missing')
  assert.match(mainTs, /app\.on\('second-instance'/, 'second-instance handler is missing')

  const closeHandler = mainTs.match(/ipcMain\.on\('window-close',[\s\S]*?\n\}\)/)
  assert.ok(closeHandler, 'window-close IPC handler missing')
  assert.ok(!closeHandler[0].includes('quitting = true'), 'window-close should not force quit state')
  assert.match(closeHandler[0], /mainWindow\.close\(\)/, 'window-close should delegate to BrowserWindow close flow')

  const closeEventHandler = mainTs.match(/mainWindow\.on\('close',[\s\S]*?\n\s*\}\)/)
  assert.ok(closeEventHandler, 'mainWindow close event handler should be present for tray behavior')
  assert.match(closeEventHandler[0], /event\.preventDefault\(\)/, 'close event should prevent default when app is not quitting')
  assert.match(closeEventHandler[0], /mainWindow\?\.hide\(\)/, 'close event should hide the window to tray')
})

test('main process should set explicit Windows app/taskbar icon wiring', async () => {
  const mainTs = await readText('src/main/index.ts')

  assert.match(
    mainTs,
    /app\.setAppUserModelId\(/,
    'Windows taskbar grouping/icon stability needs explicit AppUserModelId'
  )

  const createWindowBlock = mainTs.match(/function createWindow\(\): void \{[\s\S]*?\n\}/)
  assert.ok(createWindowBlock, 'createWindow implementation missing')
  assert.match(
    createWindowBlock[0],
    /icon:\s*getTrayIconPath\(\)/,
    'BrowserWindow should set icon explicitly for taskbar/window icon consistency'
  )
})
