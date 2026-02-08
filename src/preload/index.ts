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
  platform: process.platform,

  // ==================== SQLite 数据�?API ====================
  db: {
    // 笔记操作
    getAllNotes: () => ipcRenderer.invoke('db-get-all-notes'),
    getDeletedNotes: () => ipcRenderer.invoke('db-get-deleted-notes'),
    getNotesByCategory: (categoryId: string) => ipcRenderer.invoke('db-get-notes-by-category', categoryId),
    getNoteById: (id: string) => ipcRenderer.invoke('db-get-note-by-id', id),
    createNote: (note: { id: string; title?: string; content?: string; categoryId?: string | null }) =>
      ipcRenderer.invoke('db-create-note', note),
    updateNote: (id: string, updates: Record<string, unknown>) =>
      ipcRenderer.invoke('db-update-note', id, updates),
    deleteNote: (id: string) => ipcRenderer.invoke('db-delete-note', id),
    restoreNote: (id: string) => ipcRenderer.invoke('db-restore-note', id),
    permanentDeleteNote: (id: string) => ipcRenderer.invoke('db-permanent-delete-note', id),
    cleanupOldDeleted: (daysAgo?: number) => ipcRenderer.invoke('db-cleanup-old-deleted', daysAgo),
    searchNotes: (query: string) => ipcRenderer.invoke('db-search-notes', query),
    getBacklinkNotes: (noteId: string, noteTitle: string, limit?: number) =>
      ipcRenderer.invoke('db-get-backlink-notes', noteId, noteTitle, limit),

    // 分类操作
    getAllCategories: () => ipcRenderer.invoke('db-get-all-categories'),
    getCategoryById: (id: string) => ipcRenderer.invoke('db-get-category-by-id', id),
    createCategory: (category: { id: string; name: string; color: string; order: number }) =>
      ipcRenderer.invoke('db-create-category', category),
    updateCategory: (id: string, updates: Record<string, unknown>) =>
      ipcRenderer.invoke('db-update-category', id, updates),
    deleteCategory: (id: string) => ipcRenderer.invoke('db-delete-category', id),

    // 导入导出
    exportAllData: () => ipcRenderer.invoke('db-export-all-data'),
    importData: (data: { notes: unknown[]; categories: unknown[] }) =>
      ipcRenderer.invoke('db-import-data', data),

    // 获取数据库路�?    getPath: () => ipcRenderer.invoke('db-get-path'),
    
    // 获取数据目录路径
    getDataPath: () => ipcRenderer.invoke('db-get-data-path'),
    
    // 获取默认数据目录
    getDefaultDataPath: () => ipcRenderer.invoke('db-get-default-data-path'),
    
    // 获取数据库统�?    getStats: () => ipcRenderer.invoke('db-get-stats')
  },

  // ==================== 配置和备�?API ====================
  config: {
    get: () => ipcRenderer.invoke('config-get'),
    save: (config: Record<string, unknown>) => ipcRenderer.invoke('config-save', config)
  },

  backup: {
    create: (customPath?: string) => ipcRenderer.invoke('backup-create', customPath),
    list: () => ipcRenderer.invoke('backup-list'),
    restore: (backupPath: string) => ipcRenderer.invoke('backup-restore', backupPath)
  },

  data: {
    migrate: (newPath: string) => ipcRenderer.invoke('data-migrate', newPath)
  },

  dialog: {
    selectDirectory: (options?: { title?: string; defaultPath?: string }) => 
      ipcRenderer.invoke('dialog-select-directory', options)
  },

  shell: {
    openPath: (path: string) => ipcRenderer.invoke('shell-open-path', path)
  },

  // ==================== 图片存储 API ====================
  image: {
    store: (base64DataUrl: string) => ipcRenderer.invoke('image-store', base64DataUrl),
    load: (imageRef: string) => ipcRenderer.invoke('image-load', imageRef),
    delete: (imageRef: string) => ipcRenderer.invoke('image-delete', imageRef),
    getStats: () => ipcRenderer.invoke('image-stats'),
    cleanup: (usedImageRefs: string[]) => ipcRenderer.invoke('image-cleanup', usedImageRefs)
  },

  // ==================== 导出 API ====================
  exportPdf: (htmlContent: string) => ipcRenderer.invoke('export-pdf', htmlContent)
})
