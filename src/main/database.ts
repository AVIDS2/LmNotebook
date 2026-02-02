import Database from 'better-sqlite3'
import { app } from 'electron'
import { join } from 'path'
import { existsSync, mkdirSync, copyFileSync, readdirSync, statSync, unlinkSync } from 'fs'
import { writeFileSync, readFileSync } from 'fs'

// ==================== 配置管理 ====================

interface AppConfig {
    dataDirectory: string
    autoBackup: boolean
    backupDirectory: string
    maxBackups: number
}

const CONFIG_FILE = join(app.getPath('userData'), 'origin-notes-config.json')

// 默认配置
function getDefaultConfig(): AppConfig {
    const defaultDataPath = join(app.getPath('documents'), 'OriginNotes')
    return {
        dataDirectory: defaultDataPath,
        autoBackup: true,
        backupDirectory: join(defaultDataPath, 'backups'),
        maxBackups: 10
    }
}

// 加载配置
function loadConfig(): AppConfig {
    try {
        if (existsSync(CONFIG_FILE)) {
            const content = readFileSync(CONFIG_FILE, 'utf-8')
            const saved = JSON.parse(content) as Partial<AppConfig>
            return { ...getDefaultConfig(), ...saved }
        }
    } catch (e) {
        console.error('Failed to load config:', e)
    }
    return getDefaultConfig()
}

// 保存配置
export function saveConfig(config: Partial<AppConfig>): AppConfig {
    const current = loadConfig()
    const updated = { ...current, ...config }
    try {
        writeFileSync(CONFIG_FILE, JSON.stringify(updated, null, 2), 'utf-8')
    } catch (e) {
        console.error('Failed to save config:', e)
    }
    return updated
}

// 获取当前配置
export function getConfig(): AppConfig {
    return loadConfig()
}

// 获取默认数据目录
export function getDefaultDataDirectory(): string {
    return join(app.getPath('documents'), 'OriginNotes')
}

// ==================== 数据库初始化 ====================

const config = loadConfig()
const appDataPath = config.dataDirectory

// 确保目录存在
if (!existsSync(appDataPath)) {
    mkdirSync(appDataPath, { recursive: true })
}

const dbPath = join(appDataPath, 'notes.db')
console.log('Database path:', dbPath)

// 创建数据库连接
const db = new Database(dbPath)

// 启用外键约束和性能优化
db.pragma('foreign_keys = ON')
db.pragma('journal_mode = WAL')  // 写入性能优化
db.pragma('synchronous = NORMAL')  // 平衡安全和性能

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

    // 创建索引（优化查询性能）
    db.exec(`
    CREATE INDEX IF NOT EXISTS idx_notes_categoryId ON notes(categoryId);
    CREATE INDEX IF NOT EXISTS idx_notes_isPinned ON notes(isPinned);
    CREATE INDEX IF NOT EXISTS idx_notes_isDeleted ON notes(isDeleted);
    CREATE INDEX IF NOT EXISTS idx_notes_updatedAt ON notes(updatedAt);
    CREATE INDEX IF NOT EXISTS idx_notes_createdAt ON notes(createdAt);
    CREATE INDEX IF NOT EXISTS idx_notes_order ON notes("order");
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

// ==================== 备份功能 ====================

export interface BackupInfo {
    filename: string
    path: string
    size: number
    createdAt: number
}

// 创建备份
export function createBackup(customPath?: string): BackupInfo | null {
    const cfg = loadConfig()
    const backupDir = customPath || cfg.backupDirectory
    
    // 确保备份目录存在
    if (!existsSync(backupDir)) {
        mkdirSync(backupDir, { recursive: true })
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `notes-backup-${timestamp}.db`
    const backupPath = join(backupDir, filename)
    
    try {
        // 使用 copyFileSync 复制数据库文件（同步方式）
        // 先执行 checkpoint 确保 WAL 数据写入主文件
        db.pragma('wal_checkpoint(TRUNCATE)')
        copyFileSync(dbPath, backupPath)
        
        const stats = statSync(backupPath)
        
        // 清理旧备份
        cleanupOldBackups(backupDir, cfg.maxBackups)
        
        return {
            filename,
            path: backupPath,
            size: stats.size,
            createdAt: Date.now()
        }
    } catch (e) {
        console.error('Backup failed:', e)
        return null
    }
}

// 获取备份列表
export function getBackupList(): BackupInfo[] {
    const cfg = loadConfig()
    const backupDir = cfg.backupDirectory
    
    if (!existsSync(backupDir)) {
        return []
    }
    
    try {
        const files = readdirSync(backupDir)
            .filter(f => f.startsWith('notes-backup-') && f.endsWith('.db'))
            .map(filename => {
                const filePath = join(backupDir, filename)
                const stats = statSync(filePath)
                return {
                    filename,
                    path: filePath,
                    size: stats.size,
                    createdAt: stats.mtimeMs
                }
            })
            .sort((a, b) => b.createdAt - a.createdAt)
        
        return files
    } catch (e) {
        console.error('Failed to list backups:', e)
        return []
    }
}

// 从备份恢复
export function restoreFromBackup(backupPath: string): boolean {
    if (!existsSync(backupPath)) {
        return false
    }
    
    try {
        // 先关闭当前数据库连接
        db.close()
        
        // 复制备份文件覆盖当前数据库
        copyFileSync(backupPath, dbPath)
        
        // 重新打开数据库（需要重启应用）
        return true
    } catch (e) {
        console.error('Restore failed:', e)
        return false
    }
}

// 清理旧备份
function cleanupOldBackups(backupDir: string, maxBackups: number): void {
    try {
        const files = readdirSync(backupDir)
            .filter(f => f.startsWith('notes-backup-') && f.endsWith('.db'))
            .map(filename => ({
                filename,
                path: join(backupDir, filename),
                mtime: statSync(join(backupDir, filename)).mtimeMs
            }))
            .sort((a, b) => b.mtime - a.mtime)
        
        // 删除超出数量限制的旧备份
        if (files.length > maxBackups) {
            for (let i = maxBackups; i < files.length; i++) {
                unlinkSync(files[i].path)
                console.log('Deleted old backup:', files[i].filename)
            }
        }
    } catch (e) {
        console.error('Failed to cleanup old backups:', e)
    }
}

// ==================== 数据目录迁移 ====================

// 递归复制目录
function copyDirectorySync(src: string, dest: string): void {
    if (!existsSync(src)) return
    
    if (!existsSync(dest)) {
        mkdirSync(dest, { recursive: true })
    }
    
    const entries = readdirSync(src, { withFileTypes: true })
    for (const entry of entries) {
        const srcPath = join(src, entry.name)
        const destPath = join(dest, entry.name)
        
        if (entry.isDirectory()) {
            copyDirectorySync(srcPath, destPath)
        } else {
            copyFileSync(srcPath, destPath)
        }
    }
}

export function migrateDataDirectory(newPath: string): { success: boolean; error?: string } {
    // 重新读取当前配置，获取实际的源目录
    const currentConfig = loadConfig()
    const oldPath = currentConfig.dataDirectory
    
    console.log('Migration: from', oldPath, 'to', newPath)
    
    if (oldPath === newPath) {
        return { success: true }
    }
    
    try {
        // 确保新目录存在
        if (!existsSync(newPath)) {
            mkdirSync(newPath, { recursive: true })
        }
        
        // 1. 迁移数据库文件
        const oldDbPath = join(oldPath, 'notes.db')
        const newDbPath = join(newPath, 'notes.db')
        console.log('Copying database:', oldDbPath, '->', newDbPath)
        if (existsSync(oldDbPath)) {
            // 先执行 checkpoint 确保数据完整
            db.pragma('wal_checkpoint(TRUNCATE)')
            copyFileSync(oldDbPath, newDbPath)
            console.log('Database copied successfully')
        } else {
            console.log('Source database not found:', oldDbPath)
        }
        
        // 2. 迁移向量目录 (RAG 索引)
        const oldVectorsPath = join(oldPath, 'vectors')
        const newVectorsPath = join(newPath, 'vectors')
        console.log('Copying vectors:', oldVectorsPath, '->', newVectorsPath)
        if (existsSync(oldVectorsPath)) {
            copyDirectorySync(oldVectorsPath, newVectorsPath)
            console.log('Vectors copied successfully')
        } else {
            console.log('Source vectors not found:', oldVectorsPath)
        }
        
        // 3. 迁移模型配置
        const oldModelsPath = join(oldPath, 'models.json')
        const newModelsPath = join(newPath, 'models.json')
        console.log('Copying models.json:', oldModelsPath, '->', newModelsPath)
        if (existsSync(oldModelsPath)) {
            copyFileSync(oldModelsPath, newModelsPath)
            console.log('Models.json copied successfully')
        } else {
            console.log('Source models.json not found:', oldModelsPath)
        }
        
        // 4. 迁移图片目录
        const oldImagesPath = join(oldPath, 'images')
        const newImagesPath = join(newPath, 'images')
        console.log('Copying images:', oldImagesPath, '->', newImagesPath)
        if (existsSync(oldImagesPath)) {
            copyDirectorySync(oldImagesPath, newImagesPath)
            console.log('Images copied successfully')
        } else {
            console.log('Source images not found:', oldImagesPath)
        }
        
        // 更新配置
        saveConfig({ 
            dataDirectory: newPath,
            backupDirectory: join(newPath, 'backups')
        })
        
        console.log('Migration completed successfully')
        return { success: true }
    } catch (e) {
        const error = e instanceof Error ? e.message : 'Unknown error'
        console.error('Migration failed:', error)
        return { success: false, error }
    }
}

// 获取数据库统计信息
export function getDatabaseStats(): { noteCount: number; categoryCount: number; dbSize: number } {
    const noteCount = (db.prepare('SELECT COUNT(*) as count FROM notes WHERE isDeleted = 0').get() as { count: number }).count
    const categoryCount = (db.prepare('SELECT COUNT(*) as count FROM categories').get() as { count: number }).count
    
    let dbSize = 0
    try {
        dbSize = statSync(dbPath).size
    } catch (e) {
        // ignore
    }
    
    return { noteCount, categoryCount, dbSize }
}

// 初始化数据库
initDatabase()

// 导出数据库路径（用于显示给用户）
export { dbPath, appDataPath }
