import { app, BrowserWindow, ipcMain, shell, dialog, Menu, Tray, protocol } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { createWriteStream } from 'fs'
import { is } from '@electron-toolkit/utils'
import * as database from './database'
import * as imageStore from './imageStore'

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let quitting = false
let backendProcess: ChildProcess | null = null

// 注册自定义协议为特权协议（需要在 app ready 之前）
protocol.registerSchemesAsPrivileged([
  { scheme: 'origin-image', privileges: { bypassCSP: true, stream: true, supportFetchAPI: true } }
])

function startBackend(): void {
  // Only auto-start backend in production to avoid conflicts during dev
  if (!app.isPackaged) return

  const backendDir = join(process.resourcesPath, 'backend_src')
  const logPath = join(app.getPath('userData'), 'backend_error.log')
  const logStream = createWriteStream(logPath, { flags: 'a' })

  logStream.write(`\n[${new Date().toISOString()}] Attempting to start backend from ${backendDir}\n`)

  let backendExec: string
  let execArgs: string[] = []
  let cwd: string

  if (app.isPackaged) {
    // Production: Run the compiled executable
    // Path: resources/backend/origin_backend.exe
    backendExec = join(process.resourcesPath, 'backend', 'origin_backend.exe')
    cwd = join(process.resourcesPath, 'backend')

    // Validate
    if (!require('fs').existsSync(backendExec)) {
      logStream.write(`[FATAL] Backend executable not found at: ${backendExec}\n`)
    } else {
      logStream.write(`[Production] Starting compiled backend: ${backendExec}\n`)
    }
  } else {
    // Development: Run python script from source using local env
    // Path: backend_env/Scripts/python.exe
    const pythonExe = join(process.cwd(), 'backend_env', 'Scripts', 'python.exe')
    backendExec = pythonExe
    execArgs = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8765']
    cwd = join(process.cwd(), 'src', 'backend')

    logStream.write(`[Development] Starting backend from source using: ${backendExec}\n`)
  }

  // Spawn the process
  // Note: For compiled exe, no args needed as main.py handles uvicorn.run
  backendProcess = spawn(backendExec, execArgs, {
    cwd: cwd,
    shell: false, // Shell not needed for direct exe execution
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'] // Capture stdout/stderr but ignore stdin
  })

  // Log STDOUT (Important for uvicorn logs)
  backendProcess.stdout?.on('data', (data) => {
    logStream.write(`[stdout] ${data}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    logStream.write(`[${new Date().toISOString()}] STDERR: ${data}\n`)
  })

  backendProcess.on('error', (err) => {
    dialog.showErrorBox(
      'AI 服务启动失败',
      `无法启动后台大脑 (Python)。\n错误: ${err.message}\n\n请确保您的系统已安装 Python 并在 PATH 中。\n详细日志已保存至: ${logPath}`
    )
  })

  // Watch for early exit (e.g. missing modules)
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
      sandbox: false
    },
    show: false
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  // 🛡️ Enterprise-Grade Security: Intercept navigation to prevent app from jumping to external sites
  if (mainWindow) {
    mainWindow.webContents.on('will-navigate', (event, url) => {
      if (mainWindow && url !== mainWindow.webContents.getURL()) {
        event.preventDefault()
        require('electron').shell.openExternal(url)
      }
    })

    // Handle links specifically marked to open in new windows
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

  // 处理外部链接
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // 开发环境加载本地服务，生产环境加载打包文件
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// 窗口控制 IPC
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

// 导出文件对话框
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

// 导入文件对话框
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

// 导出 PDF
ipcMain.handle('export-pdf', async (_event, htmlContent: string) => {
  // 创建隐藏窗口用于渲染 HTML
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
    // 加载 HTML 内容
    await pdfWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`)
    
    // 等待页面渲染完成
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 生成 PDF
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

// ==================== SQLite 数据库 IPC ====================

// 笔记操作
ipcMain.handle('db-get-all-notes', () => {
  return database.getAllNotes()
})

ipcMain.handle('db-get-deleted-notes', () => {
  return database.getDeletedNotes()
})

ipcMain.handle('db-get-notes-by-category', (_event, categoryId: string) => {
  return database.getNotesByCategory(categoryId)
})

ipcMain.handle('db-get-note-by-id', (_event, id: string) => {
  return database.getNoteById(id)
})

ipcMain.handle('db-create-note', (_event, note: Partial<database.Note> & { id: string }) => {
  return database.createNote(note)
})

ipcMain.handle('db-update-note', (_event, id: string, updates: Partial<database.Note>) => {
  return database.updateNote(id, updates)
})

ipcMain.handle('db-delete-note', (_event, id: string) => {
  database.deleteNote(id)
})

ipcMain.handle('db-restore-note', (_event, id: string) => {
  database.restoreNote(id)
})

ipcMain.handle('db-permanent-delete-note', (_event, id: string) => {
  database.permanentDeleteNote(id)
})

ipcMain.handle('db-cleanup-old-deleted', (_event, daysAgo?: number) => {
  database.cleanupOldDeleted(daysAgo)
})

ipcMain.handle('db-search-notes', (_event, query: string) => {
  return database.searchNotes(query)
})

ipcMain.handle('db-get-backlink-notes', (_event, noteId: string, noteTitle: string, limit?: number) => {
  return database.getBacklinkNotes(noteId, noteTitle, limit)
})

// 分类操作
ipcMain.handle('db-get-all-categories', () => {
  return database.getAllCategories()
})

ipcMain.handle('db-get-category-by-id', (_event, id: string) => {
  return database.getCategoryById(id)
})

ipcMain.handle('db-create-category', (_event, category: database.Category) => {
  return database.createCategory(category)
})

ipcMain.handle('db-update-category', (_event, id: string, updates: Partial<database.Category>) => {
  return database.updateCategory(id, updates)
})

ipcMain.handle('db-delete-category', (_event, id: string) => {
  database.deleteCategory(id)
})

// 导入导出
ipcMain.handle('db-export-all-data', () => {
  return database.exportAllData()
})

ipcMain.handle('db-import-data', (_event, data: { notes: database.Note[]; categories: database.Category[] }) => {
  database.importData(data)
})

// 获取数据库路径
ipcMain.handle('db-get-path', () => {
  return database.dbPath
})

// ==================== 配置和备份 IPC ====================

// 获取应用配置
ipcMain.handle('config-get', () => {
  return database.getConfig()
})

// 保存应用配置
ipcMain.handle('config-save', (_event, config: Parameters<typeof database.saveConfig>[0]) => {
  return database.saveConfig(config)
})

// 创建备份
ipcMain.handle('backup-create', (_event, customPath?: string) => {
  return database.createBackup(customPath)
})

// 获取备份列表
ipcMain.handle('backup-list', () => {
  return database.getBackupList()
})

// 从备份恢复
ipcMain.handle('backup-restore', async (_event, backupPath: string) => {
  const result = database.restoreFromBackup(backupPath)
  if (result) {
    // 恢复成功后需要重启应用
    dialog.showMessageBox(mainWindow!, {
      type: 'info',
      title: '恢复成功',
      message: '数据已恢复，应用将重启以应用更改。',
      buttons: ['确定']
    }).then(() => {
      app.relaunch()
      app.exit(0)
    })
  }
  return result
})

// 迁移数据目录
ipcMain.handle('data-migrate', async (_event, newPath: string) => {
  const result = database.migrateDataDirectory(newPath)
  if (result.success) {
    // 迁移成功后需要重启应用
    const response = await dialog.showMessageBox(mainWindow!, {
      type: 'info',
      title: '迁移成功',
      message: '数据目录已迁移，应用将重启以应用更改。',
      buttons: ['确定']
    })
    if (response.response === 0) {
      app.relaunch()
      app.exit(0)
    }
  }
  return result
})

// 选择目录对话框
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

// 获取数据库统计
ipcMain.handle('db-get-stats', () => {
  return database.getDatabaseStats()
})

// 获取数据目录路径
ipcMain.handle('db-get-data-path', () => {
  return database.appDataPath
})

// 获取默认数据目录
ipcMain.handle('db-get-default-data-path', () => {
  return database.getDefaultDataDirectory()
})

// 在文件管理器中打开路径
ipcMain.handle('shell-open-path', async (_event, path: string) => {
  return shell.openPath(path)
})

// ==================== 图片存储 IPC ====================

// 存储图片（大图片分离存储，小图片返回原始 base64）
ipcMain.handle('image-store', (_event, base64DataUrl: string) => {
  return imageStore.storeImage(base64DataUrl)
})

// 加载图片（将 origin-image:// 引用转换为 base64）
ipcMain.handle('image-load', (_event, imageRef: string) => {
  return imageStore.loadImage(imageRef)
})

// 删除图片
ipcMain.handle('image-delete', (_event, imageRef: string) => {
  return imageStore.deleteImage(imageRef)
})

// 获取图片统计
ipcMain.handle('image-stats', () => {
  return imageStore.getImageStats()
})

// 清理未使用的图片
ipcMain.handle('image-cleanup', (_event, usedImageRefs: string[]) => {
  return imageStore.cleanupUnusedImages(usedImageRefs)
})

app.whenReady().then(() => {
  // 注册自定义协议处理 origin-image://
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
  }

  // 自动备份检查
  performAutoBackup()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    } else if (mainWindow) {
      mainWindow.show()
      mainWindow.focus()
    }
  })
})

// 自动备份功能
async function performAutoBackup(): Promise<void> {
  const config = database.getConfig()
  if (!config.autoBackup) return

  const backups = database.getBackupList()
  const now = Date.now()
  const oneDayMs = 24 * 60 * 60 * 1000

  // 如果没有备份或最近一次备份超过24小时，则创建新备份
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
      } catch (e) {
        // Ignore errors if process is already dead
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
