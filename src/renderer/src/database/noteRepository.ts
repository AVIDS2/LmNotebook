import { db } from './index'
import { v4 as uuidv4 } from 'uuid'
import type { Note, CreateNoteInput, UpdateNoteInput } from '@/types/note'

// 提取纯文本
function extractPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

// 笔记仓库
export const noteRepository = {
  // 获取所有未删除的笔记
  async getAll(): Promise<Note[]> {
    return await db.notes
      .where('isDeleted')
      .equals(0)
      .reverse()
      .sortBy('updatedAt')
  },

  // 获取所有笔记（按置顶和更新时间排序）
  async getAllSorted(): Promise<Note[]> {
    const notes = await db.notes
      .filter(note => !note.isDeleted)
      .toArray()

    // 置顶笔记在前，然后按更新时间倒序
    return notes.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1
      }
      return b.updatedAt - a.updatedAt
    })
  },

  // 获取置顶笔记
  async getPinned(): Promise<Note[]> {
    const notes = await db.notes
      .filter(note => note.isPinned && !note.isDeleted)
      .toArray()

    return notes.sort((a, b) => b.updatedAt - a.updatedAt)
  },

  // 按分类获取笔记
  async getByCategory(categoryId: string): Promise<Note[]> {
    const notes = await db.notes
      .filter(note => note.categoryId === categoryId && !note.isDeleted)
      .toArray()

    return notes.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1
      }
      return b.updatedAt - a.updatedAt
    })
  },

  // 获取回收站笔记
  async getDeleted(): Promise<Note[]> {
    const notes = await db.notes
      .filter(note => note.isDeleted)
      .toArray()

    return notes.sort((a, b) => (b.deletedAt || 0) - (a.deletedAt || 0))
  },

  // 根据 ID 获取笔记
  async getById(id: string): Promise<Note | undefined> {
    return await db.notes.get(id)
  },

  // 创建笔记
  async create(input: CreateNoteInput = {}): Promise<Note> {
    const now = Date.now()
    const note: Note = {
      id: uuidv4(),
      title: input.title || '',
      content: input.content || '',
      plainText: input.content ? extractPlainText(input.content) : '',
      categoryId: input.categoryId || null,
      isPinned: false,
      isDeleted: false,
      deletedAt: null,
      createdAt: now,
      updatedAt: now
    }

    await db.notes.add(note)
    return note
  },

  // 更新笔记
  async update(id: string, input: UpdateNoteInput): Promise<void> {
    const updateData: Partial<Note> = {
      ...input,
      updatedAt: Date.now()
    }

    if (input.content !== undefined) {
      updateData.plainText = extractPlainText(input.content)
    }

    await db.notes.update(id, updateData)
  },

  // 切换置顶状态
  async togglePin(id: string): Promise<void> {
    const note = await db.notes.get(id)
    if (note) {
      await db.notes.update(id, {
        isPinned: !note.isPinned,
        updatedAt: Date.now()
      })
    }
  },

  // 软删除（移到回收站）
  async softDelete(id: string): Promise<void> {
    await db.notes.update(id, {
      isDeleted: true,
      deletedAt: Date.now()
    })
  },

  // 恢复笔记
  async restore(id: string): Promise<void> {
    await db.notes.update(id, {
      isDeleted: false,
      deletedAt: null,
      updatedAt: Date.now()
    })
  },

  // 永久删除
  async permanentDelete(id: string): Promise<void> {
    await db.notes.delete(id)
  },

  // 清空回收站
  async emptyTrash(): Promise<void> {
    await db.notes.filter(note => note.isDeleted).delete()
  },

  // 清理超过30天的已删除笔记
  async cleanupOldDeleted(): Promise<void> {
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
    await db.notes
      .filter(note => note.isDeleted && note.deletedAt !== null && note.deletedAt < thirtyDaysAgo)
      .delete()
  },

  // 搜索笔记
  async search(keyword: string): Promise<Note[]> {
    if (!keyword.trim()) {
      return this.getAllSorted()
    }

    const lowerKeyword = keyword.toLowerCase()
    const notes = await db.notes
      .filter(note => {
        if (note.isDeleted) return false
        const titleMatch = note.title.toLowerCase().includes(lowerKeyword)
        const contentMatch = note.plainText.toLowerCase().includes(lowerKeyword)
        return titleMatch || contentMatch
      })
      .toArray()

    return notes.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1
      }
      return b.updatedAt - a.updatedAt
    })
  }
}
