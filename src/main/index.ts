import { app, BrowserWindow, ipcMain, shell, dialog, Menu, Tray, protocol } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { createWriteStream } from 'fs'
import { is } from '@electron-toolkit/utils'
import { autoUpdater } from 'electron-updater'
import * as database from './database'
import * as imageStore from './imageStore'

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let quitting = false
let backendProcess: ChildProcess | null = null

type UpdaterStage =
  | 'idle'
  | 'checking'
  | 'available'
  | 'not-available'
  | 'downloading'
  | 'downloaded'
  | 'error'
  | 'disabled-dev'

interface UpdaterState {
  stage: UpdaterStage
  message: string
  currentVersion: string
  availableVersion?: string
  percent?: number
  autoCheck: boolean
  lastCheckedAt?: number
}

let updaterState: UpdaterState = {
  stage: app.isPackaged ? 'idle' : 'disabled-dev',
  message: app.isPackaged ? 'Ready' : 'Updater disabled in development mode',
  currentVersion: app.getVersion(),
  autoCheck: database.getConfig().updateAutoCheck
}

function emitUpdaterState(partial: Partial<UpdaterState> = {}): UpdaterState {
  updaterState = { ...updaterState, ...partial }
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('updater-event', updaterState)
  }
  return updaterState
}

function setupAutoUpdater(): void {
  if (!app.isPackaged) {
    emitUpdaterState({
      stage: 'disabled-dev',
      message: 'Updater disabled in development mode',
      currentVersion: app.getVersion()
    })
    return
  }

  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true

  autoUpdater.on('checking-for-update', () => {
    emitUpdaterState({
      stage: 'checking',
      message: 'Checking for updates...',
      lastCheckedAt: Date.now()
    })
  })

  autoUpdater.on('update-available', (info) => {
    emitUpdaterState({
      stage: 'available',
      message: `Update available: ${info.version}`,
      availableVersion: info.version,
      percent: undefined
    })
  })

  autoUpdater.on('update-not-available', () => {
    emitUpdaterState({
      stage: 'not-available',
      message: 'You are using the latest version',
      availableVersion: undefined,
      percent: undefined
    })
  })

  autoUpdater.on('download-progress', (progress) => {
    emitUpdaterState({
      stage: 'downloading',
      message: `Downloading update (${Math.round(progress.percent)}%)`,
      percent: progress.percent
    })
  })

  autoUpdater.on('update-downloaded', (info) => {
    emitUpdaterState({
      stage: 'downloaded',
      message: `Update ready to install: ${info.version}`,
      availableVersion: info.version,
      percent: 100
    })
  })

  autoUpdater.on('error', (error) => {
    emitUpdaterState({
      stage: 'error',
      message: error?.message || 'Failed to check for updates',
      percent: undefined
    })
  })
}

// Register custom protocol as privileged before app ready.
protocol.registerSchemesAsPrivileged([
  { scheme: 'origin-image', privileges: { bypassCSP: true, stream: true, supportFetchAPI: true } }
])

function startBackend(): void {
  // Only auto-start backend in production to avoid conflicts during dev.
  if (!app.isPackaged) return

  const backendDir = join(process.resourcesPath, 'backend_src')
  const logPath = join(app.getPath('userData'), 'backend_error.log')
  const logStream = createWriteStream(logPath, { flags: 'a' })

  logStream.write(`\n[${new Date().toISOString()}] Attempting to start backend from ${backendDir}\n`)

  let backendExec: string
  let execArgs: string[] = []
  let cwd: string

  if (app.isPackaged) {
    // Production: run the compiled executable.
    backendExec = join(process.resourcesPath, 'backend', 'origin_backend.exe')
    cwd = join(process.resourcesPath, 'backend')

    if (!require('fs').existsSync(backendExec)) {
      logStream.write(`[FATAL] Backend executable not found at: ${backendExec}\n`)
    } else {
      logStream.write(`[Production] Starting compiled backend: ${backendExec}\n`)
    }
  } else {
    // Development: run python script from local env.
    const pythonExe = join(process.cwd(), 'backend_env', 'Scripts', 'python.exe')
    backendExec = pythonExe
    execArgs = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8765']
    cwd = join(process.cwd(), 'src', 'backend')

    logStream.write(`[Development] Starting backend from source using: ${backendExec}\n`)
  }

  backendProcess = spawn(backendExec, execArgs, {
    cwd,
    shell: false,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe']
  })

  backendProcess.stdout?.on('data', (data) => {
    logStream.write(`[stdout] ${data}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    logStream.write(`[${new Date().toISOString()}] STDERR: ${data}\n`)
  })

  backendProcess.on('error', (err) => {
    dialog.showErrorBox(
      'AI 服务启动失败',
      `无法启动后端服务 (Python)。\n错误: ${err.message}\n\n请确认系统已安装 Python 且可用。\n详细日志: ${logPath}`
    )
  })

  backendProcess.on('exit', (code) => {
    if (code !== 0 && code !== null) {
      logStream.write(`[${new Date().toISOString()}] Backend exited with code ${code}\n`)
    }
  })
}

function getTrayIconPath(): string {
  if (app.isPackaged) {
    return join(process.resourcesPath, 'build', 'icon.ico')
  }
  return join(app.getAppPath(), 'build', 'icon.ico')
}

function createTray(window: BrowserWindow): void {
  const iconPath = getTrayIconPath()
  tray = new Tray(iconPath)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示',
      click: () => {
        window.show()
        window.focus()
      }
    },
    {
      label: '退出',
      click: () => {
        quitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('Origin Notes')
  tray.setContextMenu(contextMenu)

  tray.on('click', () => {
    if (window.isVisible()) {
      window.hide()
    } else {
      window.show()
      window.focus()
    }
  })
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#FAFAF8',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      spellcheck: false
    },
    show: false
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  // Enterprise-grade security: block in-app external navigation.
  if (mainWindow) {
    mainWindow.webContents.on('will-navigate', (event, url) => {
      if (mainWindow && url !== mainWindow.webContents.getURL()) {
        event.preventDefault()
        require('electron').shell.openExternal(url)
      }
    })

    mainWindow.webContents.setWindowOpenHandler((details) => {
      require('electron').shell.openExternal(details.url)
      return { action: 'deny' }
    })
  }

  mainWindow.on('close', (event) => {
    if (!quitting) {
      event.preventDefault()
      mainWindow?.hide()
    }
  })

  // Handle external links.
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // Load renderer URL in dev, or local file in production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// Window control IPC.
ipcMain.on('window-minimize', () => {
  mainWindow?.minimize()
})

ipcMain.on('window-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow?.maximize()
  }
})

ipcMain.on('window-close', () => {
  mainWindow?.close()
})

ipcMain.handle('window-is-maximized', () => {
  return mainWindow?.isMaximized()
})

ipcMain.handle('app-get-meta', () => ({
  name: app.getName(),
  version: app.getVersion(),
  packaged: app.isPackaged
}))

// Export file dialog.
ipcMain.handle('export-file', async (_event, options: { defaultName: string; filters: { name: string; extensions: string[] }[]; content: string }) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    defaultPath: options.defaultName,
    filters: options.filters
  })

  if (!result.canceled && result.filePath) {
    await writeFile(result.filePath, options.content, 'utf-8')
    return { success: true, filePath: result.filePath }
  }

  return { success: false }
})

// Import file dialog.
ipcMain.handle('import-file', async (_event, options: { filters: { name: string; extensions: string[] }[] }) => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    filters: options.filters,
    properties: ['openFile']
  })

  if (!result.canceled && result.filePaths.length > 0) {
    const content = await readFile(result.filePaths[0], 'utf-8')
    return { success: true, content, filePath: result.filePaths[0] }
  }

  return { success: false }
})

// Export PDF.
ipcMain.handle('export-pdf', async (_event, htmlContent: string) => {
  const pdfWindow = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  try {
    await pdfWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`)
    await new Promise((resolve) => setTimeout(resolve, 500))

    const pdfData = await pdfWindow.webContents.printToPDF({
      printBackground: true,
      pageSize: 'A4',
      margins: {
        top: 0.5,
        bottom: 0.5,
        left: 0.5,
        right: 0.5
      }
    })

    return pdfData
  } catch (error) {
    console.error('PDF export error:', error)
    return null
  } finally {
    pdfWindow.destroy()
  }
})

// ==================== SQLite IPC ====================

// Note operations.
ipcMain.handle('db-get-all-notes', () => database.getAllNotes())
ipcMain.handle('db-get-deleted-notes', () => database.getDeletedNotes())
ipcMain.handle('db-get-notes-by-category', (_event, categoryId: string) => database.getNotesByCategory(categoryId))
ipcMain.handle('db-get-note-by-id', (_event, id: string) => database.getNoteById(id))
ipcMain.handle('db-create-note', (_event, note: Partial<database.Note> & { id: string }) => database.createNote(note))
ipcMain.handle('db-update-note', (_event, id: string, updates: Partial<database.Note>) => database.updateNote(id, updates))
ipcMain.handle('db-delete-note', (_event, id: string) => database.deleteNote(id))
ipcMain.handle('db-restore-note', (_event, id: string) => database.restoreNote(id))
ipcMain.handle('db-permanent-delete-note', (_event, id: string) => database.permanentDeleteNote(id))
ipcMain.handle('db-cleanup-old-deleted', (_event, daysAgo?: number) => database.cleanupOldDeleted(daysAgo))
ipcMain.handle('db-search-notes', (_event, query: string) => database.searchNotes(query))
ipcMain.handle('db-count-non-empty-notes', () => database.countNonEmptyNotes())
ipcMain.handle('db-get-backlink-notes', (_event, noteId: string, noteTitle: string, limit?: number) => database.getBacklinkNotes(noteId, noteTitle, limit))

// Category operations.
ipcMain.handle('db-get-all-categories', () => database.getAllCategories())
ipcMain.handle('db-get-category-by-id', (_event, id: string) => database.getCategoryById(id))
ipcMain.handle('db-create-category', (_event, category: database.Category) => database.createCategory(category))
ipcMain.handle('db-update-category', (_event, id: string, updates: Partial<database.Category>) => database.updateCategory(id, updates))
ipcMain.handle('db-delete-category', (_event, id: string) => database.deleteCategory(id))

// Import/export.
ipcMain.handle('db-export-all-data', () => database.exportAllData())
ipcMain.handle('db-import-data', (_event, data: { notes: database.Note[]; categories: database.Category[] }) => database.importData(data))

// Path & stats.
ipcMain.handle('db-get-path', () => database.dbPath)
ipcMain.handle('db-get-stats', () => database.getDatabaseStats())
ipcMain.handle('db-get-data-path', () => database.appDataPath)
ipcMain.handle('db-get-default-data-path', () => database.getDefaultDataDirectory())
ipcMain.handle('shell-open-path', async (_event, path: string) => shell.openPath(path))

// ==================== Config & Backup IPC ====================

ipcMain.handle('config-get', () => database.getConfig())
ipcMain.handle('config-save', (_event, config: Parameters<typeof database.saveConfig>[0]) => database.saveConfig(config))
ipcMain.handle('backup-create', (_event, customPath?: string) => database.createBackup(customPath))
ipcMain.handle('backup-list', () => database.getBackupList())

ipcMain.handle('updater-get-state', () => emitUpdaterState())
ipcMain.handle('updater-set-auto-check', (_event, enabled: boolean) => {
  const cfg = database.saveConfig({ updateAutoCheck: !!enabled })
  return emitUpdaterState({ autoCheck: cfg.updateAutoCheck })
})
ipcMain.handle('updater-check-for-updates', async () => {
  if (!app.isPackaged) {
    return emitUpdaterState({
      stage: 'disabled-dev',
      message: 'Updater disabled in development mode'
    })
  }
  try {
    emitUpdaterState({ stage: 'checking', message: 'Checking for updates...', lastCheckedAt: Date.now() })
    await autoUpdater.checkForUpdates()
    return emitUpdaterState()
  } catch (error) {
    return emitUpdaterState({
      stage: 'error',
      message: error instanceof Error ? error.message : 'Failed to check for updates'
    })
  }
})
ipcMain.handle('updater-download-update', async () => {
  if (!app.isPackaged) {
    return emitUpdaterState({
      stage: 'disabled-dev',
      message: 'Updater disabled in development mode'
    })
  }
  try {
    await autoUpdater.downloadUpdate()
    return emitUpdaterState()
  } catch (error) {
    return emitUpdaterState({
      stage: 'error',
      message: error instanceof Error ? error.message : 'Failed to download update'
    })
  }
})
ipcMain.handle('updater-quit-and-install', () => {
  if (!app.isPackaged) {
    return false
  }
  setImmediate(() => {
    autoUpdater.quitAndInstall()
  })
  return true
})

ipcMain.handle('backup-restore', async (_event, backupPath: string) => {
  const result = database.restoreFromBackup(backupPath)
  if (result) {
    dialog.showMessageBox(mainWindow!, {
      type: 'info',
      title: '恢复成功',
      message: '数据已恢复，应用将重启以生效。',
      buttons: ['确定']
    }).then(() => {
      app.relaunch()
      app.exit(0)
    })
  }
  return result
})

ipcMain.handle('data-migrate', async (_event, newPath: string) => {
  const result = database.migrateDataDirectory(newPath)
  if (result.success) {
    const response = await dialog.showMessageBox(mainWindow!, {
      type: 'info',
      title: '迁移成功',
      message: '数据目录已迁移，应用将重启以生效。',
      buttons: ['确定']
    })
    if (response.response === 0) {
      app.relaunch()
      app.exit(0)
    }
  }
  return result
})

ipcMain.handle('dialog-select-directory', async (_event, options?: { title?: string; defaultPath?: string }) => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    title: options?.title || '选择目录',
    defaultPath: options?.defaultPath,
    properties: ['openDirectory', 'createDirectory']
  })

  if (!result.canceled && result.filePaths.length > 0) {
    return { success: true, path: result.filePaths[0] }
  }
  return { success: false }
})

// ==================== Image storage IPC ====================

ipcMain.handle('image-store', (_event, base64DataUrl: string) => imageStore.storeImage(base64DataUrl))
ipcMain.handle('image-load', (_event, imageRef: string) => imageStore.loadImage(imageRef))
ipcMain.handle('image-delete', (_event, imageRef: string) => imageStore.deleteImage(imageRef))
ipcMain.handle('image-stats', () => imageStore.getImageStats())
ipcMain.handle('image-cleanup', (_event, usedImageRefs: string[]) => imageStore.cleanupUnusedImages(usedImageRefs))

app.whenReady().then(() => {
  setupAutoUpdater()

  // Register file protocol handler: origin-image://
  protocol.registerFileProtocol('origin-image', (request, callback) => {
    const filename = request.url.replace('origin-image://', '')
    const config = database.getConfig()
    const filepath = join(config.dataDirectory, 'images', filename)
    callback({ path: filepath })
  })

  startBackend()
  createWindow()

  if (mainWindow) {
    createTray(mainWindow)
    emitUpdaterState()
  }

  // Check and perform automatic backup.
  performAutoBackup()

  const cfg = database.getConfig()
  if (app.isPackaged && cfg.updateAutoCheck) {
    setTimeout(() => {
      autoUpdater.checkForUpdates().catch((error) => {
        emitUpdaterState({
          stage: 'error',
          message: error instanceof Error ? error.message : 'Failed to check for updates'
        })
      })
    }, 2500)
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    } else if (mainWindow) {
      mainWindow.show()
      mainWindow.focus()
    }
  })
})

async function performAutoBackup(): Promise<void> {
  const config = database.getConfig()
  if (!config.autoBackup) return

  const backups = database.getBackupList()
  const now = Date.now()
  const oneDayMs = 24 * 60 * 60 * 1000

  // Create a new backup if none exists or the latest is older than one day.
  if (backups.length === 0 || (now - backups[0].createdAt) > oneDayMs) {
    console.log('Performing auto backup...')
    const result = database.createBackup()
    if (result) {
      console.log('Auto backup created:', result.filename)
    }
  }
}

app.on('before-quit', () => {
  quitting = true
  if (backendProcess) {
    if (process.platform === 'win32') {
      try {
        const { execSync } = require('child_process')
        execSync(`taskkill /pid ${backendProcess.pid} /F /T`)
      } catch (_e) {
        // Ignore errors if process is already dead.
      }
    } else {
      backendProcess.kill()
    }
    backendProcess = null
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
