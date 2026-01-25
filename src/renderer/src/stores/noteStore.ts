import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Note, CreateNoteInput, UpdateNoteInput } from '@/types/note'
import { noteRepository } from '@/database/noteRepository'

export type ViewType = 'all' | 'pinned' | 'category' | 'trash'

// 从内容生成标题（取前30个字符）
function generateTitleFromContent(content: string): string {
  // 移除 HTML 标签
  const div = document.createElement('div')
  div.innerHTML = content
  const plainText = (div.textContent || div.innerText || '').trim()

  if (!plainText) return ''

  // 取前30个字符，如果超过则加省略号
  const maxLength = 30
  if (plainText.length <= maxLength) {
    return plainText
  }

  // 尝试在单词/标点处截断
  let truncated = plainText.slice(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')
  const lastPunctuation = Math.max(
    truncated.lastIndexOf('，'),
    truncated.lastIndexOf('。'),
    truncated.lastIndexOf('、'),
    truncated.lastIndexOf(','),
    truncated.lastIndexOf('.')
  )

  if (lastPunctuation > maxLength * 0.6) {
    truncated = truncated.slice(0, lastPunctuation)
  } else if (lastSpace > maxLength * 0.6) {
    truncated = truncated.slice(0, lastSpace)
  }

  return truncated + '...'
}

// 检查笔记是否为空
function isNoteEmpty(note: Note): boolean {
  const hasTitle = note.title.trim().length > 0
  const hasContent = note.plainText.trim().length > 0
  return !hasTitle && !hasContent
}

export const useNoteStore = defineStore('notes', () => {
  // 状态
  const notes = ref<Note[]>([])
  const currentNote = ref<Note | null>(null)
  const currentView = ref<ViewType>('all')
  const currentCategoryId = ref<string | null>(null)
  const searchKeyword = ref('')
  const isLoading = ref(false)
  const totalNotesCount = ref(0) // 全部笔记总数（不包括已删除）

  // 计算属性
  const noteCount = computed(() => notes.value.length)
  const pinnedNotes = computed(() => notes.value.filter(n => n.isPinned))

  // 更新全部笔记总数（排除空笔记）
  async function updateTotalCount(): Promise<void> {
    totalNotesCount.value = await noteRepository.countNonEmpty()
  }

  // 加载笔记列表
  async function loadNotes(options: { updateTotalCount?: boolean } = {}): Promise<void> {
    isLoading.value = true
    try {
      if (searchKeyword.value) {
        notes.value = await noteRepository.search(searchKeyword.value)
      } else if (currentView.value === 'all') {
        notes.value = await noteRepository.getAllSorted()
      } else if (currentView.value === 'pinned') {
        notes.value = await noteRepository.getPinned()
      } else if (currentView.value === 'category' && currentCategoryId.value) {
        notes.value = await noteRepository.getByCategory(currentCategoryId.value)
      } else if (currentView.value === 'trash') {
        notes.value = await noteRepository.getDeleted()
      }
      if (options.updateTotalCount !== false) {
        await updateTotalCount()
      }
    } finally {
      isLoading.value = false
    }
  }

  function sortNotesForCurrentView(list: Note[]): void {
    if (searchKeyword.value.trim()) {
      list.sort((a, b) => {
        if (a.isPinned !== b.isPinned) {
          return a.isPinned ? -1 : 1
        }
        return b.updatedAt - a.updatedAt
      })
      return
    }

    if (currentView.value === 'trash') {
      list.sort((a, b) => (b.deletedAt || 0) - (a.deletedAt || 0))
      return
    }

    if (currentView.value === 'pinned') {
      list.sort((a, b) => b.updatedAt - a.updatedAt)
      return
    }

    list.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1
      }
      return b.updatedAt - a.updatedAt
    })
  }

  function matchesSearch(note: Note, keyword: string): boolean {
    const lowerKeyword = keyword.toLowerCase()
    return (
      note.title.toLowerCase().includes(lowerKeyword) ||
      note.plainText.toLowerCase().includes(lowerKeyword)
    )
  }

  function applyNoteUpdate(updated: Note): void {
    const keyword = searchKeyword.value.trim()
    const isSearchActive = keyword.length > 0
    const shouldMatchSearch = !isSearchActive || matchesSearch(updated, keyword)

    let shouldInclude = true
    if (isSearchActive) {
      shouldInclude = !updated.isDeleted && shouldMatchSearch
    } else if (currentView.value === 'trash') {
      shouldInclude = updated.isDeleted
    } else if (currentView.value === 'pinned') {
      shouldInclude = !updated.isDeleted && updated.isPinned
    } else if (currentView.value === 'category') {
      shouldInclude = !updated.isDeleted && updated.categoryId === currentCategoryId.value
    } else {
      shouldInclude = !updated.isDeleted
    }

    const previous = currentNote.value?.id === updated.id
      ? currentNote.value
      : notes.value.find(note => note.id === updated.id)

    if (currentNote.value?.id === updated.id) {
      currentNote.value = updated
    }

    const index = notes.value.findIndex(note => note.id === updated.id)
    if (shouldInclude) {
      if (index === -1) {
        notes.value.push(updated)
      } else {
        notes.value[index] = updated
      }
      sortNotesForCurrentView(notes.value)
    } else if (index !== -1) {
      notes.value.splice(index, 1)
    }

    if (previous) {
      const wasCounted = !previous.isDeleted && !isNoteEmpty(previous)
      const isCounted = !updated.isDeleted && !isNoteEmpty(updated)
      if (!wasCounted && isCounted) {
        totalNotesCount.value += 1
      } else if (wasCounted && !isCounted) {
        totalNotesCount.value = Math.max(0, totalNotesCount.value - 1)
      }
    }
  }

  // 切换视图（会清理空笔记）
  async function setView(view: ViewType, categoryId?: string): Promise<void> {
    // 切换前检查当前笔记是否为空，如果是则删除
    await cleanupEmptyCurrentNote()

    currentView.value = view
    currentCategoryId.value = categoryId || null
    searchKeyword.value = ''
    await loadNotes()

    // 选中第一个笔记
    if (notes.value.length > 0) {
      currentNote.value = notes.value[0]
    } else {
      currentNote.value = null
    }
  }

  // 清理空笔记
  async function cleanupEmptyCurrentNote(): Promise<void> {
    if (currentNote.value && !currentNote.value.isDeleted) {
      // 重新获取最新状态
      const latest = await noteRepository.getById(currentNote.value.id)
      if (latest && isNoteEmpty(latest)) {
        await noteRepository.permanentDelete(latest.id)
      }
    }
  }

  // 搜索
  async function search(keyword: string): Promise<void> {
    searchKeyword.value = keyword
    await loadNotes({ updateTotalCount: false })
  }

  // 选择笔记（切换时检查空笔记）
  async function selectNote(note: Note): Promise<void> {
    // 如果切换到不同的笔记，检查当前笔记是否为空
    if (currentNote.value && currentNote.value.id !== note.id) {
      await cleanupEmptyCurrentNote()
      await loadNotes({ updateTotalCount: false })
    }

    currentNote.value = note
  }

  // 创建新笔记
  async function createNote(input: CreateNoteInput = {}): Promise<Note> {
    // 创建前先清理可能存在的空笔记
    await cleanupEmptyCurrentNote()

    const note = await noteRepository.create(input)
    await loadNotes({ updateTotalCount: false })
    await updateTotalCount()
    currentNote.value = note
    return note
  }

  // 更新笔记（支持自动生成标题）
  async function updateNote(id: string, input: UpdateNoteInput): Promise<void> {
    // 如果更新了内容且没有标题，自动生成标题
    if (input.content !== undefined) {
      const note = await noteRepository.getById(id)
      if (note && !note.title.trim()) {
        const autoTitle = generateTitleFromContent(input.content)
        if (autoTitle) {
          input.title = autoTitle
        }
      }
    }

    await noteRepository.update(id, input)

    // 更新当前笔记
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
      if (currentNote.value?.id === id) {
        currentNote.value = updated
      }
    }
  }

  // 切换置顶
  async function togglePin(id: string): Promise<void> {
    await noteRepository.togglePin(id)
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
      if (currentNote.value?.id === id) {
        currentNote.value = updated
      }
    }
  }

  // 删除笔记（移到回收站）
  async function deleteNote(id: string): Promise<void> {
    await noteRepository.softDelete(id)
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
    } else {
      notes.value = notes.value.filter(note => note.id !== id)
    }

    if (currentNote.value?.id === id) {
      currentNote.value = notes.value[0] || null
    }
  }

  // 恢复笔记
  async function restoreNote(id: string): Promise<void> {
    await noteRepository.restore(id)
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
    }
  }

  // 永久删除
  async function permanentDeleteNote(id: string): Promise<void> {
    const existing = await noteRepository.getById(id)
    await noteRepository.permanentDelete(id)
    notes.value = notes.value.filter(note => note.id !== id)

    if (existing) {
      const wasCounted = !existing.isDeleted && !isNoteEmpty(existing)
      if (wasCounted) {
        totalNotesCount.value = Math.max(0, totalNotesCount.value - 1)
      }
    }

    if (currentNote.value?.id === id) {
      currentNote.value = notes.value[0] || null
    }
  }

  // 清空回收站
  async function emptyTrash(): Promise<void> {
    await noteRepository.emptyTrash()
    notes.value = []
    currentNote.value = null
  }

  // 初始化
  async function initialize(): Promise<void> {
    await loadNotes()
    if (notes.value.length > 0) {
      currentNote.value = notes.value[0]
    }
  }

  return {
    // 状态
    notes,
    currentNote,
    currentView,
    currentCategoryId,
    searchKeyword,
    isLoading,
    totalNotesCount,

    // 计算属性
    noteCount,
    pinnedNotes,

    // 方法
    loadNotes,
    setView,
    search,
    selectNote,
    createNote,
    updateNote,
    togglePin,
    deleteNote,
    restoreNote,
    permanentDeleteNote,
    emptyTrash,
    initialize,
    cleanupEmptyCurrentNote
  }
})
