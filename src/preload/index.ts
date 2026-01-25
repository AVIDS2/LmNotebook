import { contextBridge, ipcRenderer } from 'electron'

// 暴露给渲染进程的 API
contextBridge.exposeInMainWorld('electronAPI', {
  // 窗口控制
  minimizeWindow: () => ipcRenderer.send('window-minimize'),
  maximizeWindow: () => ipcRenderer.send('window-maximize'),
  closeWindow: () => ipcRenderer.send('window-close'),
  isMaximized: () => ipcRenderer.invoke('window-is-maximized'),

  // 文件导出/导入
  exportFile: (options: { defaultName: string; filters: { name: string; extensions: string[] }[]; content: string }) =>
    ipcRenderer.invoke('export-file', options),
  importFile: (options: { filters: { name: string; extensions: string[] }[] }) =>
    ipcRenderer.invoke('import-file', options),

  // 平台信息
  platform: process.platform
})
