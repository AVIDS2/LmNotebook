import type { Note, Category } from '@/services/database'

interface FileFilter {
  name: string
  extensions: string[]
}

interface ExportOptions {
  defaultName: string
  filters: FileFilter[]
  content: string
}

interface ImportOptions {
  filters: FileFilter[]
}

interface ExportResult {
  success: boolean
  filePath?: string
}

interface ImportResult {
  success: boolean
  content?: string
  filePath?: string
}

interface DatabaseAPI {
  getAllNotes: () => Promise<Note[]>
  getDeletedNotes: () => Promise<Note[]>
  getNotesByCategory: (categoryId: string) => Promise<Note[]>
  getNoteById: (id: string) => Promise<Note | undefined>
  createNote: (note: { id: string; title?: string; content?: string; categoryId?: string | null }) => Promise<Note>
  updateNote: (id: string, updates: Record<string, unknown>) => Promise<Note | undefined>
  deleteNote: (id: string) => Promise<void>
  restoreNote: (id: string) => Promise<void>
  permanentDeleteNote: (id: string) => Promise<void>
  cleanupOldDeleted: (daysAgo?: number) => Promise<void>
  searchNotes: (query: string) => Promise<Note[]>
  getBacklinkNotes: (noteId: string, noteTitle: string, limit?: number) => Promise<Note[]>
  getAllCategories: () => Promise<Category[]>
  getCategoryById: (id: string) => Promise<Category | undefined>
  createCategory: (category: Category) => Promise<Category>
  updateCategory: (id: string, updates: Record<string, unknown>) => Promise<Category | undefined>
  deleteCategory: (id: string) => Promise<void>
  exportAllData: () => Promise<{ notes: Note[]; categories: Category[] }>
  importData: (data: { notes: Note[]; categories: Category[] }) => Promise<void>
  getPath: () => Promise<string>
  getDataPath: () => Promise<string>
  getDefaultDataPath: () => Promise<string>
  getStats: () => Promise<{ noteCount: number; categoryCount: number; dbSize: number }>
}

interface AppConfig {
  dataDirectory: string
  autoBackup: boolean
  backupDirectory: string
  maxBackups: number
}

interface BackupInfo {
  filename: string
  path: string
  size: number
  createdAt: number
}

interface ConfigAPI {
  get: () => Promise<AppConfig>
  save: (config: Partial<AppConfig>) => Promise<AppConfig>
}

interface BackupAPI {
  create: (customPath?: string) => Promise<BackupInfo | null>
  list: () => Promise<BackupInfo[]>
  restore: (backupPath: string) => Promise<boolean>
}

interface DataAPI {
  migrate: (newPath: string) => Promise<{ success: boolean; error?: string }>
}

interface DialogAPI {
  selectDirectory: (options?: { title?: string; defaultPath?: string }) => Promise<{ success: boolean; path?: string }>
}

interface ShellAPI {
  openPath: (path: string) => Promise<string>
}

interface ImageAPI {
  store: (base64DataUrl: string) => Promise<string>
  load: (imageRef: string) => Promise<string | null>
  delete: (imageRef: string) => Promise<boolean>
  getStats: () => Promise<{ count: number; totalSize: number }>
  cleanup: (usedImageRefs: string[]) => Promise<number>
}

interface IElectronAPI {
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

export {}
