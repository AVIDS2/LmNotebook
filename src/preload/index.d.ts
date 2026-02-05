export interface FileFilter {
  name: string
  extensions: string[]
}

export interface ExportOptions {
  defaultName: string
  filters: FileFilter[]
  content: string
}

export interface ImportOptions {
  filters: FileFilter[]
}

export interface ExportResult {
  success: boolean
  filePath?: string
}

export interface ImportResult {
  success: boolean
  content?: string
  filePath?: string
}

// SQLite 数据库类型
export interface Note {
  id: string
  title: string
  content: string
  plainText: string
  markdownSource: string | null
  categoryId: string | null
  isPinned: number
  isDeleted: number
  deletedAt: number | null
  createdAt: number
  updatedAt: number
}

export interface Category {
  id: string
  name: string
  color: string
  order: number
}

export interface DatabaseAPI {
  // 笔记操作
  getAllNotes: () => Promise<Note[]>
  getDeletedNotes: () => Promise<Note[]>
  getNotesByCategory: (categoryId: string) => Promise<Note[]>
  getNoteById: (id: string) => Promise<Note | undefined>
  createNote: (note: { id: string; title?: string; content?: string; categoryId?: string | null }) => Promise<Note>
  updateNote: (id: string, updates: Partial<Note>) => Promise<Note | undefined>
  deleteNote: (id: string) => Promise<void>
  restoreNote: (id: string) => Promise<void>
  permanentDeleteNote: (id: string) => Promise<void>
  cleanupOldDeleted: (daysAgo?: number) => Promise<void>
  searchNotes: (query: string) => Promise<Note[]>

  // 分类操作
  getAllCategories: () => Promise<Category[]>
  getCategoryById: (id: string) => Promise<Category | undefined>
  createCategory: (category: Category) => Promise<Category>
  updateCategory: (id: string, updates: Partial<Category>) => Promise<Category | undefined>
  deleteCategory: (id: string) => Promise<void>

  // 导入导出
  exportAllData: () => Promise<{ notes: Note[]; categories: Category[] }>
  importData: (data: { notes: Note[]; categories: Category[] }) => Promise<void>

  // 获取数据库路径
  getPath: () => Promise<string>
  
  // 获取数据目录路径
  getDataPath: () => Promise<string>
  
  // 获取默认数据目录
  getDefaultDataPath: () => Promise<string>
  
  // 获取数据库统计
  getStats: () => Promise<{ noteCount: number; categoryCount: number; dbSize: number }>
}

// 配置类型
export interface AppConfig {
  dataDirectory: string
  autoBackup: boolean
  backupDirectory: string
  maxBackups: number
}

// 备份信息类型
export interface BackupInfo {
  filename: string
  path: string
  size: number
  createdAt: number
}

export interface ConfigAPI {
  get: () => Promise<AppConfig>
  save: (config: Partial<AppConfig>) => Promise<AppConfig>
}

export interface BackupAPI {
  create: (customPath?: string) => Promise<BackupInfo | null>
  list: () => Promise<BackupInfo[]>
  restore: (backupPath: string) => Promise<boolean>
}

export interface DataAPI {
  migrate: (newPath: string) => Promise<{ success: boolean; error?: string }>
}

export interface DialogAPI {
  selectDirectory: (options?: { title?: string; defaultPath?: string }) => Promise<{ success: boolean; path?: string }>
}

export interface ShellAPI {
  openPath: (path: string) => Promise<string>
}

export interface ImageAPI {
  store: (base64DataUrl: string) => Promise<string>
  load: (imageRef: string) => Promise<string | null>
  delete: (imageRef: string) => Promise<boolean>
  getStats: () => Promise<{ count: number; totalSize: number }>
  cleanup: (usedImageRefs: string[]) => Promise<number>
}

export interface IElectronAPI {
  minimizeWindow: () => void
  maximizeWindow: () => void
  closeWindow: () => void
  isMaximized: () => Promise<boolean>
  exportFile: (options: ExportOptions) => Promise<ExportResult>
  importFile: (options: ImportOptions) => Promise<ImportResult>
  platform: string
  db: DatabaseAPI
  config: ConfigAPI
  backup: BackupAPI
  data: DataAPI
  dialog: DialogAPI
  shell: ShellAPI
  image: ImageAPI
  exportPdf: (htmlContent: string) => Promise<Uint8Array | null>
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
