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
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
