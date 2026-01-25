// 笔记数据类型
export interface Note {
  id: string
  title: string
  content: string       // 富文本 HTML
  plainText: string     // 纯文本 (搜索用)
  categoryId: string | null
  isPinned: boolean
  isDeleted: boolean
  deletedAt: number | null
  createdAt: number
  updatedAt: number
}

// 分类数据类型
export interface Category {
  id: string
  name: string
  color: string
  order: number
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
}
