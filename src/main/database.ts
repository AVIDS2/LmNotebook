import Database from 'better-sqlite3'
import { app } from 'electron'
import { join } from 'path'
import { existsSync, mkdirSync } from 'fs'

// 数据库文件存储在用户文档目录，便于备份和迁移
const userDataPath = app.getPath('documents')
const appDataPath = join(userDataPath, 'OriginNotes')

// 确保目录存在
if (!existsSync(appDataPath)) {
    mkdirSync(appDataPath, { recursive: true })
}

const dbPath = join(appDataPath, 'notes.db')
console.log('Database path:', dbPath)

// 创建数据库连接
const db = new Database(dbPath)

// 启用外键约束
db.pragma('foreign_keys = ON')

// 初始化表结构
function initDatabase(): void {
    // 创建笔记表
    db.exec(`
    CREATE TABLE IF NOT EXISTS notes (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL DEFAULT '',
      content TEXT NOT NULL DEFAULT '',
      plainText TEXT NOT NULL DEFAULT '',
      markdownSource TEXT,
      categoryId TEXT,
      isPinned INTEGER NOT NULL DEFAULT 0,
      isDeleted INTEGER NOT NULL DEFAULT 0,
      deletedAt INTEGER,
      createdAt INTEGER NOT NULL,
      updatedAt INTEGER NOT NULL,
      "order" INTEGER NOT NULL DEFAULT 0
    )
  `)

    // 创建分类表
    db.exec(`
    CREATE TABLE IF NOT EXISTS categories (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      color TEXT NOT NULL DEFAULT '#8C9198',
      "order" INTEGER NOT NULL DEFAULT 0
    )
  `)

    // 为旧数据库添加 order 列
    try {
        db.exec('ALTER TABLE notes ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0')
    } catch (e) {
        // 列已经存在
    }

    // 创建索引
    db.exec(`
    CREATE INDEX IF NOT EXISTS idx_notes_categoryId ON notes(categoryId);
    CREATE INDEX IF NOT EXISTS idx_notes_isPinned ON notes(isPinned);
    CREATE INDEX IF NOT EXISTS idx_notes_isDeleted ON notes(isDeleted);
    CREATE INDEX IF NOT EXISTS idx_notes_updatedAt ON notes(updatedAt);
  `)

    // 初始化默认分类
    const categoryCount = db.prepare('SELECT COUNT(*) as count FROM categories').get() as { count: number }
    if (categoryCount.count === 0) {
        const insertCategory = db.prepare(
            'INSERT INTO categories (id, name, color, "order") VALUES (?, ?, ?, ?)'
        )
        insertCategory.run('work', '工作', '#8C9198', 0)
        insertCategory.run('life', '生活', '#8FA882', 1)
        insertCategory.run('study', '学习', '#C4A882', 2)
    }

    console.log('Database initialized successfully')
}

// 笔记类型定义
export interface Note {
    id: string
    title: string
    content: string
    plainText: string
    markdownSource: string | null
    categoryId: string | null
    isPinned: number  // SQLite 用 0/1 表示布尔
    isDeleted: number
    deletedAt: number | null
    createdAt: number
    updatedAt: number
    order: number
}

// 分类类型定义
export interface Category {
    id: string
    name: string
    color: string
    order: number
}

// ==================== 笔记操作 ====================

export function getAllNotes(): Note[] {
    return db.prepare('SELECT * FROM notes WHERE isDeleted = 0 ORDER BY isPinned DESC, "order" ASC, updatedAt DESC').all() as Note[]
}

export function getDeletedNotes(): Note[] {
    return db.prepare('SELECT * FROM notes WHERE isDeleted = 1 ORDER BY deletedAt DESC').all() as Note[]
}

export function getNotesByCategory(categoryId: string): Note[] {
    return db.prepare('SELECT * FROM notes WHERE categoryId = ? AND isDeleted = 0 ORDER BY isPinned DESC, "order" ASC, updatedAt DESC').all(categoryId) as Note[]
}

export function getNoteById(id: string): Note | undefined {
    return db.prepare('SELECT * FROM notes WHERE id = ?').get(id) as Note | undefined
}

export function createNote(note: Partial<Note> & { id: string }): Note {
    const now = Date.now()
    const maxOrder = (db.prepare('SELECT MAX("order") as maxOrder FROM notes').get() as { maxOrder: number | null }).maxOrder ?? -1
    const stmt = db.prepare(`
    INSERT INTO notes (id, title, content, plainText, markdownSource, categoryId, isPinned, isDeleted, createdAt, updatedAt, "order")
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `)
    stmt.run(
        note.id,
        note.title || '',
        note.content || '',
        note.plainText || '',
        note.markdownSource || null,
        note.categoryId || null,
        note.isPinned ? 1 : 0,
        0,
        now,
        now,
        maxOrder + 1
    )
    return getNoteById(note.id)!
}

export function updateNote(id: string, updates: Partial<Note>): Note | undefined {
    const current = getNoteById(id)
    if (!current) return undefined

    const fields: string[] = []
    const values: (string | number | null)[] = []

    if (updates.title !== undefined) {
        fields.push('title = ?')
        values.push(updates.title)
    }
    if (updates.content !== undefined) {
        fields.push('content = ?')
        values.push(updates.content)
    }
    if (updates.plainText !== undefined) {
        fields.push('plainText = ?')
        values.push(updates.plainText)
    }
    if (updates.markdownSource !== undefined) {
        fields.push('markdownSource = ?')
        values.push(updates.markdownSource)
    }
    if (updates.categoryId !== undefined) {
        fields.push('categoryId = ?')
        values.push(updates.categoryId)
    }
    if (updates.isPinned !== undefined) {
        fields.push('isPinned = ?')
        values.push(updates.isPinned ? 1 : 0)
    }
    if (updates.isDeleted !== undefined) {
        fields.push('isDeleted = ?')
        values.push(updates.isDeleted ? 1 : 0)
    }
    if (updates.deletedAt !== undefined) {
        fields.push('deletedAt = ?')
        values.push(updates.deletedAt)
    }
    if (updates.order !== undefined) {
        fields.push('"order" = ?')
        values.push(updates.order)
    }

    fields.push('updatedAt = ?')
    values.push(Date.now())
    values.push(id)

    const sql = `UPDATE notes SET ${fields.join(', ')} WHERE id = ?`
    db.prepare(sql).run(...values)

    return getNoteById(id)
}

export function deleteNote(id: string): void {
    updateNote(id, { isDeleted: 1, deletedAt: Date.now() })
}

export function restoreNote(id: string): void {
    updateNote(id, { isDeleted: 0, deletedAt: null })
}

export function permanentDeleteNote(id: string): void {
    db.prepare('DELETE FROM notes WHERE id = ?').run(id)
}

export function cleanupOldDeleted(daysAgo: number = 30): void {
    const threshold = Date.now() - daysAgo * 24 * 60 * 60 * 1000
    db.prepare('DELETE FROM notes WHERE isDeleted = 1 AND deletedAt < ?').run(threshold)
}

export function searchNotes(query: string): Note[] {
    const pattern = `%${query}%`
    return db.prepare(`
    SELECT * FROM notes 
    WHERE isDeleted = 0 AND (title LIKE ? OR plainText LIKE ?)
    ORDER BY isPinned DESC, "order" ASC, updatedAt DESC
  `).all(pattern, pattern) as Note[]
}

// ==================== 分类操作 ====================

export function getAllCategories(): Category[] {
    return db.prepare('SELECT * FROM categories ORDER BY "order" ASC').all() as Category[]
}

export function getCategoryById(id: string): Category | undefined {
    return db.prepare('SELECT * FROM categories WHERE id = ?').get(id) as Category | undefined
}

export function createCategory(category: Category): Category {
    const stmt = db.prepare(
        'INSERT INTO categories (id, name, color, "order") VALUES (?, ?, ?, ?)'
    )
    stmt.run(category.id, category.name, category.color, category.order)
    return getCategoryById(category.id)!
}

export function updateCategory(id: string, updates: Partial<Category>): Category | undefined {
    const current = getCategoryById(id)
    if (!current) return undefined

    const fields: string[] = []
    const values: (string | number)[] = []

    if (updates.name !== undefined) {
        fields.push('name = ?')
        values.push(updates.name)
    }
    if (updates.color !== undefined) {
        fields.push('color = ?')
        values.push(updates.color)
    }
    if (updates.order !== undefined) {
        fields.push('"order" = ?')
        values.push(updates.order)
    }

    if (fields.length === 0) return current

    values.push(id)
    const sql = `UPDATE categories SET ${fields.join(', ')} WHERE id = ?`
    db.prepare(sql).run(...values)

    return getCategoryById(id)
}

export function deleteCategory(id: string): void {
    // 先将该分类下的笔记设为无分类
    db.prepare('UPDATE notes SET categoryId = NULL WHERE categoryId = ?').run(id)
    // 删除分类
    db.prepare('DELETE FROM categories WHERE id = ?').run(id)
}

// ==================== 导入导出 ====================

export function exportAllData(): { notes: Note[]; categories: Category[] } {
    return {
        notes: db.prepare('SELECT * FROM notes').all() as Note[],
        categories: db.prepare('SELECT * FROM categories').all() as Category[]
    }
}

export function importData(data: { notes: Note[]; categories: Category[] }): void {
    const transaction = db.transaction(() => {
        // 清空现有数据
        db.prepare('DELETE FROM notes').run()
        db.prepare('DELETE FROM categories').run()

        // 导入分类
        const insertCategory = db.prepare(
            'INSERT INTO categories (id, name, color, "order") VALUES (?, ?, ?, ?)'
        )
        for (const cat of data.categories) {
            insertCategory.run(cat.id, cat.name, cat.color, cat.order)
        }

        // 导入笔记
        const insertNote = db.prepare(`
      INSERT INTO notes (id, title, content, plainText, markdownSource, categoryId, isPinned, isDeleted, deletedAt, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
        for (const note of data.notes) {
            insertNote.run(
                note.id,
                note.title,
                note.content,
                note.plainText,
                note.markdownSource,
                note.categoryId,
                note.isPinned,
                note.isDeleted,
                note.deletedAt,
                note.createdAt,
                note.updatedAt
            )
        }
    })

    transaction()
}

// 初始化数据库
initDatabase()

// 导出数据库路径（用于显示给用户）
export { dbPath }
