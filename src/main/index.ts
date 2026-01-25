import { app, BrowserWindow, ipcMain, shell, dialog } from 'electron'
import { writeFile, readFile } from 'fs/promises'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'

let mainWindow: BrowserWindow | null = null

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

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
