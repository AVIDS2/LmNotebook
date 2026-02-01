import { v4 as uuidv4 } from 'uuid'
import * as db from '@/services/database'
import type { Note, Category } from '@/services/database'

// 提取纯文本
function extractPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

// 创建笔记参数
export interface CreateNoteInput {
  title?: string
  content?: string
  categoryId?: string | null
}

// 更新笔记参数
export interface UpdateNoteInput {
  title?: string
  content?: string
  plainText?: string
  categoryId?: string | null
  isPinned?: boolean
  createdAt?: number
  updatedAt?: number
  order?: number
}

// 笔记仓库 - 使用 SQLite
export const noteRepository = {
  // 获取所有未删除的笔记
  async getAll(): Promise<Note[]> {
    return await db.getAllNotes()
  },

  // 获取所有笔记（按置顶和更新时间排序）
  async getAllSorted(): Promise<Note[]> {
    return await db.getAllNotes()
  },

  // 获取置顶笔记
  async getPinned(): Promise<Note[]> {
    const notes = await db.getAllNotes()
    return notes.filter(note => note.isPinned)
  },

  // 按分类获取笔记
  async getByCategory(categoryId: string): Promise<Note[]> {
    return await db.getNotesByCategory(categoryId)
  },

  // 获取回收站笔记
  async getDeleted(): Promise<Note[]> {
    return await db.getDeletedNotes()
  },

  // 根据 ID 获取笔记
  async getById(id: string): Promise<Note | undefined> {
    return await db.getNoteById(id)
  },

  // 创建笔记
  async create(input: CreateNoteInput = {}): Promise<Note> {
    return await db.createNote({
      id: uuidv4(),
      title: input.title || '',
      content: input.content || '',
      categoryId: input.categoryId || null
    })
  },

  // 更新笔记
  async update(id: string, input: UpdateNoteInput): Promise<void> {
    const updateData: Partial<Note> = {
      ...input
    }

    if (input.content !== undefined) {
      updateData.plainText = extractPlainText(input.content)
    }

    await db.updateNote(id, updateData)
  },

  // 切换置顶状态
  async togglePin(id: string): Promise<void> {
    const note = await db.getNoteById(id)
    if (note) {
      await db.updateNote(id, {
        isPinned: note.isPinned ? 0 : 1
      })
    }
  },

  // 软删除（移到回收站）
  async softDelete(id: string): Promise<void> {
    await db.deleteNote(id)
  },

  // 恢复笔记
  async restore(id: string): Promise<void> {
    await db.restoreNote(id)
  },

  // 永久删除
  async permanentDelete(id: string): Promise<void> {
    await db.permanentDeleteNote(id)
  },

  // 清空回收站
  async emptyTrash(): Promise<void> {
    const deleted = await db.getDeletedNotes()
    for (const note of deleted) {
      await db.permanentDeleteNote(note.id)
    }
  },

  // 清理超过30天的已删除笔记
  async cleanupOldDeleted(): Promise<void> {
    await db.cleanupOldDeleted(30)
  },

  // 统计非空笔记总数（排除已删除）
  async countNonEmpty(): Promise<number> {
    const notes = await db.getAllNotes()
    return notes.filter(note => {
      return note.title.trim().length > 0 || note.plainText.trim().length > 0
    }).length
  },

  // 搜索笔记
  async search(keyword: string): Promise<Note[]> {
    if (!keyword.trim()) {
      return this.getAllSorted()
    }
    return await db.searchNotes(keyword)
  }
}

export type { Note, Category }
