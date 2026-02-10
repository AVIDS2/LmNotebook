import { v4 as uuidv4 } from 'uuid'
import * as db from '@/services/database'
import type { Note, Category } from '@/services/database'
import { createVectorSyncScheduler } from '@/utils/vectorSyncScheduler.mjs'
import { createVectorDeleteScheduler } from '@/utils/vectorDeleteScheduler.mjs'

function extractPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

const VECTOR_SYNC_ENDPOINT = 'http://127.0.0.1:8765/api/notes/vector/sync'
const VECTOR_DELETE_ENDPOINT = 'http://127.0.0.1:8765/api/notes'
const vectorSyncScheduler = createVectorSyncScheduler(async (payload: {
  noteId: string
  title: string
  content: string
}) => {
  await fetch(VECTOR_SYNC_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      note_id: payload.noteId,
      title: payload.title,
      content: payload.content
    })
  })
}, 1800)

const vectorDeleteScheduler = createVectorDeleteScheduler(async (noteId: string) => {
  await fetch(`${VECTOR_DELETE_ENDPOINT}/${noteId}/vector`, {
    method: 'DELETE'
  })
})

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
  markdownSource?: string | null
  categoryId?: string | null
  isPinned?: boolean
  isLocked?: boolean
  createdAt?: number
  updatedAt?: number
  order?: number
}

export interface BacklinkSummary {
  id: string
  title: string
  updatedAt: number
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
      // Rich-text editor saves HTML; old markdownSource can become stale and mislead agent reads.
      if (input.markdownSource === undefined) {
        updateData.markdownSource = null
      }
    }

    await db.updateNote(id, updateData)
    
    // 同步更新向量索引（标题或内容变化时）
    if (input.title !== undefined || input.content !== undefined) {
      try {
        const note = await db.getNoteById(id)
        if (note) {
          vectorSyncScheduler.schedule({
            noteId: id,
            title: note.title,
            content: note.plainText || ''
          })
        }
      } catch (e) {
        console.warn('Failed to sync vector index:', e)
      }
    }
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
    // Async cleanup avoids blocking note switching on empty-note auto deletion.
    vectorDeleteScheduler.schedule(id)
  },

  // 清空回收站
  async emptyTrash(): Promise<void> {
    const deleted = await db.getDeletedNotes()
    const noteIds = deleted.map(note => note.id)
    
    // 先删除数据库记录
    for (const note of deleted) {
      await db.permanentDeleteNote(note.id)
    }
    
    // 批量清理向量索引
    if (noteIds.length > 0) {
      try {
        await fetch('http://127.0.0.1:8765/api/notes/vectors/batch-delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ note_ids: noteIds })
        })
      } catch (e) {
        console.warn('Failed to batch remove vectors:', e)
      }
    }
  },

  // 清理超过30天的已删除笔记
  async cleanupOldDeleted(): Promise<void> {
    await db.cleanupOldDeleted(30)
  },

  // 统计非空笔记总数（排除已删除）
  async countNonEmpty(): Promise<number> {
    return await db.countNonEmptyNotes()
  },

  // 搜索笔记
  async search(keyword: string): Promise<Note[]> {
    if (!keyword.trim()) {
      return this.getAllSorted()
    }
    return await db.searchNotes(keyword)
  },

  async getBacklinks(noteId: string, noteTitle: string, limit: number = 50): Promise<BacklinkSummary[]> {
    const title = noteTitle.trim()
    if (!title) return []

    const strictToken = `[[${title}]]`
    const candidates = await db.getBacklinkNotes(noteId, title, limit)
    return candidates
      .filter((note) =>
        note.id !== noteId &&
        (
          (note.plainText || '').includes(strictToken) ||
          (note.markdownSource || '').includes(strictToken) ||
          (note.content || '').includes(strictToken)
        )
      )
      .map((note) => ({
        id: note.id,
        title: note.title?.trim() || 'Untitled',
        updatedAt: note.updatedAt
      }))
  }
}

export type { Note, Category }
