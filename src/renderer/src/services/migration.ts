import Dexie, { type Table } from 'dexie'
import * as sqliteDb from '@/services/database'

// 旧的 IndexedDB 类型定义
interface OldNote {
    id: string
    title: string
    content: string
    plainText: string
    categoryId: string | null
    isPinned: boolean
    isDeleted: boolean
    deletedAt: number | null
    createdAt: number
    updatedAt: number
}

interface OldCategory {
    id: string
    name: string
    color: string
    order: number
}

// 旧的 Dexie 数据库
class OldNotesDatabase extends Dexie {
    notes!: Table<OldNote>
    categories!: Table<OldCategory>

    constructor() {
        super('OriginNotesDB')

        this.version(1).stores({
            notes: 'id, categoryId, isPinned, isDeleted, deletedAt, createdAt, updatedAt',
            categories: 'id, order'
        })
    }
}

const oldDb = new OldNotesDatabase()

// 迁移数据从 IndexedDB 到 SQLite
export async function migrateToSQLite(): Promise<{ success: boolean; message: string }> {
    try {
        // 检查 IndexedDB 是否有数据
        const oldNotes = await oldDb.notes.toArray()
        const oldCategories = await oldDb.categories.toArray()

        if (oldNotes.length === 0 && oldCategories.length === 0) {
            return { success: true, message: '没有发现需要迁移的旧数据。' }
        }

        console.log(`发现 ${oldNotes.length} 条笔记和 ${oldCategories.length} 个分类需要迁移...`)

        // 迁移分类
        const existingCategories = await sqliteDb.getAllCategories()
        const existingCategoryIds = new Set(existingCategories.map(c => c.id))

        let categoryMigrated = 0
        for (const cat of oldCategories) {
            if (!existingCategoryIds.has(cat.id)) {
                await sqliteDb.createCategory({
                    id: cat.id,
                    name: cat.name,
                    color: cat.color,
                    order: cat.order
                })
                categoryMigrated++
            }
        }

        // 迁移笔记
        let noteMigrated = 0
        for (const note of oldNotes) {
            const existing = await sqliteDb.getNoteById(note.id)
            if (!existing) {
                // 创建笔记
                await window.electronAPI.db.createNote({
                    id: note.id,
                    title: note.title,
                    content: note.content,
                    categoryId: note.categoryId
                })

                // 更新其他字段
                await sqliteDb.updateNote(note.id, {
                    plainText: note.plainText,
                    isPinned: note.isPinned ? 1 : 0,
                    isDeleted: note.isDeleted ? 1 : 0,
                    deletedAt: note.deletedAt,
                    createdAt: note.createdAt,
                    updatedAt: note.updatedAt
                })
                noteMigrated++
            }
        }

        return {
            success: true,
            message: `迁移完成！\n\n成功迁移：\n• ${noteMigrated} 条笔记\n• ${categoryMigrated} 个分类\n\n跳过（已存在）：\n• ${oldNotes.length - noteMigrated} 条笔记\n• ${oldCategories.length - categoryMigrated} 个分类`
        }
    } catch (error) {
        console.error('迁移失败:', error)
        return {
            success: false,
            message: `迁移失败: ${error instanceof Error ? error.message : '未知错误'}`
        }
    }
}

// 检查是否有旧数据需要迁移
export async function checkOldData(): Promise<{ hasData: boolean; noteCount: number; categoryCount: number }> {
    try {
        const noteCount = await oldDb.notes.count()
        const categoryCount = await oldDb.categories.count()
        return {
            hasData: noteCount > 0 || categoryCount > 0,
            noteCount,
            categoryCount
        }
    } catch {
        return { hasData: false, noteCount: 0, categoryCount: 0 }
    }
}

export { oldDb }
