// 全局类型声明

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
    // 笔记操作
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

    // 分类操作
    getAllCategories: () => Promise<Category[]>
    getCategoryById: (id: string) => Promise<Category | undefined>
    createCategory: (category: Category) => Promise<Category>
    updateCategory: (id: string, updates: Record<string, unknown>) => Promise<Category | undefined>
    deleteCategory: (id: string) => Promise<void>

    // 导入导出
    exportAllData: () => Promise<{ notes: Note[]; categories: Category[] }>
    importData: (data: { notes: Note[]; categories: Category[] }) => Promise<void>

    // 获取数据库路径
    getPath: () => Promise<string>
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
}

declare global {
    interface Window {
        electronAPI: IElectronAPI
    }
}

export { }
