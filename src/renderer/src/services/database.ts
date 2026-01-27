// SQLite 数据库服务 - 通过 IPC 与主进程通信
// 替代原来的 IndexedDB (Dexie)

// 笔记类型
export interface Note {
    id: string
    title: string
    content: string
    plainText: string
    markdownSource: string | null
    categoryId: string | null
    isPinned: boolean | number
    isDeleted: boolean | number
    deletedAt: number | null
    createdAt: number
    updatedAt: number
}

// 分类类型
export interface Category {
    id: string
    name: string
    color: string
    order: number
}

// 将 SQLite 的 0/1 转换为布尔值
function convertNote(note: Note): Note {
    return {
        ...note,
        isPinned: Boolean(note.isPinned),
        isDeleted: Boolean(note.isDeleted)
    }
}

// ==================== 笔记操作 ====================

export async function getAllNotes(): Promise<Note[]> {
    const notes = await window.electronAPI.db.getAllNotes()
    return notes.map(convertNote)
}

export async function getDeletedNotes(): Promise<Note[]> {
    const notes = await window.electronAPI.db.getDeletedNotes()
    return notes.map(convertNote)
}

export async function getNotesByCategory(categoryId: string): Promise<Note[]> {
    const notes = await window.electronAPI.db.getNotesByCategory(categoryId)
    return notes.map(convertNote)
}

export async function getNoteById(id: string): Promise<Note | undefined> {
    const note = await window.electronAPI.db.getNoteById(id)
    return note ? convertNote(note) : undefined
}

export async function createNote(note: {
    id: string
    title?: string
    content?: string
    categoryId?: string | null
}): Promise<Note> {
    const created = await window.electronAPI.db.createNote(note)
    return convertNote(created)
}

export async function updateNote(
    id: string,
    updates: Partial<Note>
): Promise<Note | undefined> {
    const updated = await window.electronAPI.db.updateNote(id, updates as Record<string, unknown>)
    return updated ? convertNote(updated) : undefined
}

export async function deleteNote(id: string): Promise<void> {
    await window.electronAPI.db.deleteNote(id)
}

export async function restoreNote(id: string): Promise<void> {
    await window.electronAPI.db.restoreNote(id)
}

export async function permanentDeleteNote(id: string): Promise<void> {
    await window.electronAPI.db.permanentDeleteNote(id)
}

export async function cleanupOldDeleted(daysAgo?: number): Promise<void> {
    await window.electronAPI.db.cleanupOldDeleted(daysAgo)
}

export async function searchNotes(query: string): Promise<Note[]> {
    const notes = await window.electronAPI.db.searchNotes(query)
    return notes.map(convertNote)
}

// ==================== 分类操作 ====================

export async function getAllCategories(): Promise<Category[]> {
    return await window.electronAPI.db.getAllCategories()
}

export async function getCategoryById(id: string): Promise<Category | undefined> {
    return await window.electronAPI.db.getCategoryById(id)
}

export async function createCategory(category: Category): Promise<Category> {
    return await window.electronAPI.db.createCategory(category)
}

export async function updateCategory(
    id: string,
    updates: Partial<Category>
): Promise<Category | undefined> {
    return await window.electronAPI.db.updateCategory(id, updates as Record<string, unknown>)
}

export async function deleteCategory(id: string): Promise<void> {
    await window.electronAPI.db.deleteCategory(id)
}

// ==================== 导入导出 ====================

export async function exportAllData(): Promise<{ notes: Note[]; categories: Category[] }> {
    return await window.electronAPI.db.exportAllData()
}

export async function importData(data: { notes: Note[]; categories: Category[] }): Promise<void> {
    await window.electronAPI.db.importData(data)
}

// ==================== 工具函数 ====================

export async function getDbPath(): Promise<string> {
    return await window.electronAPI.db.getPath()
}

// 生成唯一 ID
export function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}
