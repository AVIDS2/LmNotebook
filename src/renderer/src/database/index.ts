import Dexie, { type Table } from 'dexie'
import type { Note, Category } from '@/types/note'

export class NotesDatabase extends Dexie {
  notes!: Table<Note>
  categories!: Table<Category>

  constructor() {
    super('OriginNotesDB')

    this.version(1).stores({
      notes: 'id, categoryId, isPinned, isDeleted, deletedAt, createdAt, updatedAt',
      categories: 'id, order'
    })
  }
}

export const db = new NotesDatabase()

// 初始化默认分类
export async function initializeDatabase(): Promise<void> {
  const categoryCount = await db.categories.count()

  if (categoryCount === 0) {
    const defaultCategories: Category[] = [
      { id: 'work', name: '工作', color: '#8C9198', order: 0 },
      { id: 'life', name: '生活', color: '#8FA882', order: 1 },
      { id: 'study', name: '学习', color: '#C4A882', order: 2 }
    ]

    await db.categories.bulkAdd(defaultCategories)
  }
}
