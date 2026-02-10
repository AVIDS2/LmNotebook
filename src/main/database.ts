import Database from 'better-sqlite3'
import { app } from 'electron'
import { join } from 'path'
import { existsSync, mkdirSync, copyFileSync, readdirSync, statSync, unlinkSync } from 'fs'
import { writeFileSync, readFileSync } from 'fs'


interface AppConfig {
    dataDirectory: string
    autoBackup: boolean
    backupDirectory: string
    maxBackups: number
}

const CONFIG_FILE = join(app.getPath('userData'), 'origin-notes-config.json')

function getDefaultConfig(): AppConfig {
    const defaultDataPath = join(app.getPath('documents'), 'OriginNotes')
    return {
        dataDirectory: defaultDataPath,
        autoBackup: true,
        backupDirectory: join(defaultDataPath, 'backups'),
        maxBackups: 10
    }
}

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

export function getConfig(): AppConfig {
    return loadConfig()
}

export function getDefaultDataDirectory(): string {
    return join(app.getPath('documents'), 'OriginNotes')
}


const config = loadConfig()
const appDataPath = config.dataDirectory

if (!existsSync(appDataPath)) {
    mkdirSync(appDataPath, { recursive: true })
}

const dbPath = join(appDataPath, 'notes.db')
console.log('Database path:', dbPath)

const db = new Database(dbPath)

db.pragma('foreign_keys = ON')
db.pragma('journal_mode = WAL')
db.pragma('synchronous = NORMAL')

function initDatabase(): void {
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

    db.exec(`
    CREATE TABLE IF NOT EXISTS categories (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      color TEXT NOT NULL DEFAULT '#8C9198',
      "order" INTEGER NOT NULL DEFAULT 0
    )
  `)

    try {
        db.exec('ALTER TABLE notes ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0')
    } catch (e) {
    }

    try {
        db.exec('ALTER TABLE notes ADD COLUMN isLocked INTEGER NOT NULL DEFAULT 0')
    } catch (e) {
    }

    db.exec(`
    CREATE INDEX IF NOT EXISTS idx_notes_categoryId ON notes(categoryId);
    CREATE INDEX IF NOT EXISTS idx_notes_isPinned ON notes(isPinned);
    CREATE INDEX IF NOT EXISTS idx_notes_isDeleted ON notes(isDeleted);
    CREATE INDEX IF NOT EXISTS idx_notes_updatedAt ON notes(updatedAt);
    CREATE INDEX IF NOT EXISTS idx_notes_createdAt ON notes(createdAt);
    CREATE INDEX IF NOT EXISTS idx_notes_order ON notes("order");
  `)

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

export interface Note {
    id: string
    title: string
    content: string
    plainText: string
    markdownSource: string | null
    categoryId: string | null
    isPinned: number
    isLocked: number
    isDeleted: number
    deletedAt: number | null
    createdAt: number
    updatedAt: number
    order: number
}

export interface Category {
    id: string
    name: string
    color: string
    order: number
}


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
    if (updates.isLocked !== undefined) {
        fields.push('isLocked = ?')
        values.push(updates.isLocked ? 1 : 0)
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

export function countNonEmptyNotes(): number {
    const row = db.prepare(`
    SELECT COUNT(*) as count
    FROM notes
    WHERE isDeleted = 0
      AND (
        length(trim(title)) > 0
        OR length(trim(plainText)) > 0
      )
  `).get() as { count: number }
    return row.count
}

function escapeLike(input: string): string {
    return input.replace(/[\\%_]/g, '\\$&')
}

export function getBacklinkNotes(noteId: string, noteTitle: string, limit: number = 50): Note[] {
    const title = noteTitle.trim()
    if (!title) return []
    const safeLimit = Math.max(1, Math.min(limit, 200))

    const strictPattern = `%[[${escapeLike(title)}]]%`
    return db.prepare(`
    SELECT * FROM notes
    WHERE isDeleted = 0
      AND id != ?
      AND (
        plainText LIKE ? ESCAPE '\\'
        OR markdownSource LIKE ? ESCAPE '\\'
        OR content LIKE ? ESCAPE '\\'
      )
    ORDER BY updatedAt DESC
    LIMIT ?
  `).all(noteId, strictPattern, strictPattern, strictPattern, safeLimit) as Note[]
}


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
    db.prepare('UPDATE notes SET categoryId = NULL WHERE categoryId = ?').run(id)
    db.prepare('DELETE FROM categories WHERE id = ?').run(id)
}


export function exportAllData(): { notes: Note[]; categories: Category[] } {
    return {
        notes: db.prepare('SELECT * FROM notes').all() as Note[],
        categories: db.prepare('SELECT * FROM categories').all() as Category[]
    }
}

export function importData(data: { notes: Note[]; categories: Category[] }): void {
    const transaction = db.transaction(() => {
        db.prepare('DELETE FROM notes').run()
        db.prepare('DELETE FROM categories').run()

        const insertCategory = db.prepare(
            'INSERT INTO categories (id, name, color, "order") VALUES (?, ?, ?, ?)'
        )
        for (const cat of data.categories) {
            insertCategory.run(cat.id, cat.name, cat.color, cat.order)
        }

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


export interface BackupInfo {
    filename: string
    path: string
    size: number
    createdAt: number
}

export function createBackup(customPath?: string): BackupInfo | null {
    const cfg = loadConfig()
    const backupDir = customPath || cfg.backupDirectory
    
    if (!existsSync(backupDir)) {
        mkdirSync(backupDir, { recursive: true })
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `notes-backup-${timestamp}.db`
    const backupPath = join(backupDir, filename)
    
    try {
        db.pragma('wal_checkpoint(TRUNCATE)')
        copyFileSync(dbPath, backupPath)
        
        const stats = statSync(backupPath)
        
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

export function restoreFromBackup(backupPath: string): boolean {
    if (!existsSync(backupPath)) {
        return false
    }
    
    try {
        db.close()
        
        copyFileSync(backupPath, dbPath)
        
        return true
    } catch (e) {
        console.error('Restore failed:', e)
        return false
    }
}

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
    const currentConfig = loadConfig()
    const oldPath = currentConfig.dataDirectory
    
    console.log('Migration: from', oldPath, 'to', newPath)
    
    if (oldPath === newPath) {
        return { success: true }
    }
    
    try {
        if (!existsSync(newPath)) {
            mkdirSync(newPath, { recursive: true })
        }
        
        const oldDbPath = join(oldPath, 'notes.db')
        const newDbPath = join(newPath, 'notes.db')
        console.log('Copying database:', oldDbPath, '->', newDbPath)
        if (existsSync(oldDbPath)) {
            db.pragma('wal_checkpoint(TRUNCATE)')
            copyFileSync(oldDbPath, newDbPath)
            console.log('Database copied successfully')
        } else {
            console.log('Source database not found:', oldDbPath)
        }
        
        const oldVectorsPath = join(oldPath, 'vectors')
        const newVectorsPath = join(newPath, 'vectors')
        console.log('Copying vectors:', oldVectorsPath, '->', newVectorsPath)
        if (existsSync(oldVectorsPath)) {
            copyDirectorySync(oldVectorsPath, newVectorsPath)
            console.log('Vectors copied successfully')
        } else {
            console.log('Source vectors not found:', oldVectorsPath)
        }
        
        const oldModelsPath = join(oldPath, 'models.json')
        const newModelsPath = join(newPath, 'models.json')
        console.log('Copying models.json:', oldModelsPath, '->', newModelsPath)
        if (existsSync(oldModelsPath)) {
            copyFileSync(oldModelsPath, newModelsPath)
            console.log('Models.json copied successfully')
        } else {
            console.log('Source models.json not found:', oldModelsPath)
        }
        
        const oldImagesPath = join(oldPath, 'images')
        const newImagesPath = join(newPath, 'images')
        console.log('Copying images:', oldImagesPath, '->', newImagesPath)
        if (existsSync(oldImagesPath)) {
            copyDirectorySync(oldImagesPath, newImagesPath)
            console.log('Images copied successfully')
        } else {
            console.log('Source images not found:', oldImagesPath)
        }
        
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

export function getDatabaseStats(): { noteCount: number; categoryCount: number; dbSize: number } {
    const noteCount = (db.prepare('SELECT COUNT(*) as count FROM notes WHERE isDeleted = 0').get() as { count: number }).count
    const categoryCount = (db.prepare('SELECT COUNT(*) as count FROM categories').get() as { count: number }).count
    
    let dbSize = 0
    try {
        dbSize = statSync(dbPath).size
    } catch (e) {
    }
    
    return { noteCount, categoryCount, dbSize }
}

initDatabase()

export { dbPath, appDataPath }
