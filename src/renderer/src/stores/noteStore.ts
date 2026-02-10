import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { noteRepository, type Note, type CreateNoteInput, type UpdateNoteInput } from '@/database/noteRepository'
import { createDeferredEmptyNoteCleanup } from '@/utils/deferredNoteCleanup.mjs'

export type ViewType = 'all' | 'pinned' | 'category' | 'trash'

// 濞寸姴楠搁崬瀵糕偓鐟版贡閺佹捇骞嬮幇顓犲灱濡増锕槐娆撳矗閺嵮冾枀30濞戞搩浜滈悺褏绮敂鑲╃
function generateTitleFromContent(content: string): string {
  const div = document.createElement('div')
  div.innerHTML = content
  const plainText = (div.textContent || div.innerText || '').trim()

  if (!plainText) return ''

  const maxLength = 30
  if (plainText.length <= maxLength) {
    return plainText
  }

  let truncated = plainText.slice(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')
  const lastPunctuation = Math.max(
    truncated.lastIndexOf('\uFF0C'),
    truncated.lastIndexOf('\u3002'),
    truncated.lastIndexOf('\u3001'),
    truncated.lastIndexOf(','),
    truncated.lastIndexOf('.')
  )

  if (lastPunctuation > maxLength * 0.6) {
    truncated = truncated.slice(0, lastPunctuation)
  } else if (lastSpace > maxLength * 0.6) {
    truncated = truncated.slice(0, lastSpace)
  }

  return `${truncated}...`
}
// Check whether a note has no title and no plain text.
function isNoteEmpty(note: Note): boolean {
  const hasTitle = note.title.trim().length > 0
  const hasContent = note.plainText.trim().length > 0
  return !hasTitle && !hasContent
}

export const useNoteStore = defineStore('notes', () => {
  // State
  const notes = ref<Note[]>([])
  const currentNote = ref<Note | null>(null)
  const currentView = ref<ViewType>('all')
  const currentCategoryId = ref<string | null>(null)
  const searchKeyword = ref('')
  const isLoading = ref(false)
  const totalNotesCount = ref(0) // 闁稿繈鍔戦崕瀵哥箔閺冨浂鍞堕柟顒傜帛閺嗙喖鏁嶉崼婊呯憹闁告牕鎳忕€氼厼顔忛幓鎺戠仼闂傚嫨鍊х槐?
  // Batch selection state
  const isSelectionMode = ref(false)
  const selectedNoteIds = ref<Set<string>>(new Set())

  // Computed values
  const noteCount = computed(() => notes.value.length)
  const pinnedNotes = computed(() => notes.value.filter(n => n.isPinned))
  const selectedCount = computed(() => selectedNoteIds.value.size)
  const isAllSelected = computed(() => 
    notes.value.length > 0 && selectedNoteIds.value.size === notes.value.length
  )

  function removeNoteFromLocalList(noteId: string): void {
    notes.value = notes.value.filter(note => note.id !== noteId)
  }

  const deferredEmptyCleanup = createDeferredEmptyNoteCleanup({
    getCurrentNoteId: () => currentNote.value?.id || null,
    getById: (noteId: string) => noteRepository.getById(noteId),
    isEmpty: (note: Note) => isNoteEmpty(note),
    removeById: async (noteId: string) => {
      await noteRepository.permanentDelete(noteId)
      removeNoteFromLocalList(noteId)
    }
  })

  // Update total non-empty note count.
  async function updateTotalCount(): Promise<void> {
    totalNotesCount.value = await noteRepository.countNonEmpty()
  }

  // Load notes for current view.
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
      if (a.order !== b.order) {
        return a.order - b.order
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
      shouldInclude = !Boolean(updated.isDeleted) && shouldMatchSearch
    } else if (currentView.value === 'trash') {
      shouldInclude = Boolean(updated.isDeleted)
    } else if (currentView.value === 'pinned') {
      shouldInclude = !Boolean(updated.isDeleted) && Boolean(updated.isPinned)
    } else if (currentView.value === 'category') {
      shouldInclude = !Boolean(updated.isDeleted) && updated.categoryId === currentCategoryId.value
    } else {
      shouldInclude = !Boolean(updated.isDeleted)
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
      const wasCounted = !Boolean(previous.isDeleted) && !isNoteEmpty(previous)
      const isCounted = !Boolean(updated.isDeleted) && !isNoteEmpty(updated)
      if (!wasCounted && isCounted) {
        totalNotesCount.value += 1
      } else if (wasCounted && !isCounted) {
        totalNotesCount.value = Math.max(0, totalNotesCount.value - 1)
      }
    }
  }

  // 闁告帒娲﹀畷鑼喆閸℃绂堥柨娑樼墔缁辨澘銆掗崨顖涘€炵紒宀冩閻燁亞鎷嬬敮顔剧
  async function setView(view: ViewType, categoryId?: string): Promise<void> {
    const previous = currentNote.value

    currentView.value = view
    currentCategoryId.value = categoryId || null
    searchKeyword.value = ''
    
    // 濞ｅ洦绻傞悺銊ㄣ亹閹惧啿顤呴悷娆忔濞存ɑ鎷呭鍥╂瀭闁?localStorage
    localStorage.setItem('lastView', view)
    if (categoryId) {
      localStorage.setItem('lastCategoryId', categoryId)
    } else {
      localStorage.removeItem('lastCategoryId')
    }
    
    await loadNotes()

    // Select first note in current list.
    if (notes.value.length > 0) {
      currentNote.value = notes.value[0]
    } else {
      currentNote.value = null
    }

    if (previous && !Boolean(previous.isDeleted)) {
      void deferredEmptyCleanup(previous).catch((error: unknown) => {
        console.warn('Deferred empty note cleanup failed in setView:', error)
      })
    }
  }

  // Cleanup current empty note synchronously for view-switch/create flows.
  async function cleanupEmptyCurrentNote(): Promise<boolean> {
    if (currentNote.value && !Boolean(currentNote.value.isDeleted)) {
      // Re-fetch latest state before deleting.
      const latest = await noteRepository.getById(currentNote.value.id)
      if (latest && isNoteEmpty(latest)) {
        await noteRepository.permanentDelete(latest.id)
        removeNoteFromLocalList(latest.id)
        return true
      }
    }
    return false
  }

  // Search notes.
  async function search(keyword: string): Promise<void> {
    searchKeyword.value = keyword
    await loadNotes({ updateTotalCount: false })
  }

  // Select note and defer empty-draft cleanup for responsiveness.
  async function selectNote(note: Note): Promise<void> {
    const previous = currentNote.value
    currentNote.value = note

    // Keep note switching instant and cleanup stale empty drafts in background.
    if (previous && previous.id !== note.id && !Boolean(previous.isDeleted)) {
      void deferredEmptyCleanup(previous).catch((error: unknown) => {
        console.warn('Deferred empty note cleanup failed:', error)
      })
    }
  }

  // Create note
  async function createNote(input: CreateNoteInput = {}): Promise<Note> {
    const previous = currentNote.value

    const note = await noteRepository.create(input)
    await loadNotes({ updateTotalCount: false })
    await updateTotalCount()
    currentNote.value = note

    if (previous && previous.id !== note.id && !Boolean(previous.isDeleted)) {
      void deferredEmptyCleanup(previous).catch((error: unknown) => {
        console.warn('Deferred empty note cleanup failed in createNote:', error)
      })
    }

    return note
  }

  // Update note.
  async function updateNote(id: string, input: UpdateNoteInput): Promise<void> {
    // Generate title from content when title is empty.
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

    // Refresh current note cache.
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
      if (currentNote.value?.id === id) {
        currentNote.value = updated
      }
    }
  }

  // Toggle pin state.
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

  // Move note to trash.
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

  // Restore note from trash.
  async function restoreNote(id: string): Promise<void> {
    await noteRepository.restore(id)
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
    }
  }

  // Permanently delete note.
  async function permanentDeleteNote(id: string): Promise<void> {
    const existing = await noteRepository.getById(id)
    await noteRepository.permanentDelete(id)
    notes.value = notes.value.filter(note => note.id !== id)

    if (existing) {
      const wasCounted = !Boolean(existing.isDeleted) && !isNoteEmpty(existing)
      if (wasCounted) {
        totalNotesCount.value = Math.max(0, totalNotesCount.value - 1)
      }
    }

    if (currentNote.value?.id === id) {
      currentNote.value = notes.value[0] || null
    }
  }

  // Empty trash.
  async function emptyTrash(): Promise<void> {
    // Get all deleted notes first to collect image references.
    const deletedNotes = await noteRepository.getDeleted()
    const imageRefs: string[] = []
    
    // Collect all origin-image:// refs.
    for (const note of deletedNotes) {
      const matches = note.content.match(/origin-image:\/\/[^"'\s]+/g)
      if (matches) {
        imageRefs.push(...matches)
      }
    }
    
    // 婵炴挸鎳愰埞鏍炊閻愬瓨鏆紒鏃€鐟辩槐娆愬濮橆剚鍊辨慨婵勫劜缁斿鎮堕崱妤佸€婚梺鎻掔箳閸屻劌顕ｉ弴顏嗙
    await noteRepository.emptyTrash()
    notes.value = []
    currentNote.value = null
    
    // Cleanup orphaned local images after emptying trash.
    if (imageRefs.length > 0 && window.electronAPI?.image?.cleanup) {
      try {
        // Gather currently used image refs from all notes.
        const allNotes = await noteRepository.getAll()
        const usedRefs: string[] = []
        for (const note of allNotes) {
          const matches = note.content.match(/origin-image:\/\/[^"'\s]+/g)
          if (matches) {
            usedRefs.push(...matches)
          }
        }
        await window.electronAPI.image.cleanup(usedRefs)
      } catch (e) {
        console.warn('Image cleanup failed:', e)
      }
    }
  }

  // ========== 闁归潧缍婇崳娲箼瀹ュ嫮绋?==========
  
  // 閺夆晜绋戦崣?闂侇偀鍋撻柛鎴炴そ閳ь剙顦扮€氥劌螣閳ュ磭纭€
  function toggleSelectionMode(): void {
    isSelectionMode.value = !isSelectionMode.value
    if (!isSelectionMode.value) {
      selectedNoteIds.value.clear()
    }
  }

  // 闂侇偀鍋撻柛鎴炴そ閳ь剙顦扮€氥劌螣閳ュ磭纭€
  function exitSelectionMode(): void {
    isSelectionMode.value = false
    selectedNoteIds.value.clear()
  }

  // Toggle single note selection in batch mode.
  function toggleNoteSelection(id: string): void {
    if (selectedNoteIds.value.has(id)) {
      selectedNoteIds.value.delete(id)
    } else {
      selectedNoteIds.value.add(id)
    }
    // Trigger reactive update.
    selectedNoteIds.value = new Set(selectedNoteIds.value)
  }

  // Select/Deselect all notes.
  function toggleSelectAll(): void {
    if (isAllSelected.value) {
      selectedNoteIds.value.clear()
    } else {
      selectedNoteIds.value = new Set(notes.value.map(n => n.id))
    }
  }

  // Batch move selected notes to trash.
  async function batchDelete(): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    await Promise.all(ids.map((id) => noteRepository.softDelete(id)))
    await loadNotes()
    selectedNoteIds.value.clear()
    
    // Update current note if it was deleted.
    if (currentNote.value && ids.includes(currentNote.value.id)) {
      currentNote.value = notes.value[0] || null
    }
  }

  // Batch permanent delete.
  async function batchPermanentDelete(): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    await Promise.all(ids.map((id) => noteRepository.permanentDelete(id)))
    await loadNotes()
    selectedNoteIds.value.clear()
    
    if (currentNote.value && ids.includes(currentNote.value.id)) {
      currentNote.value = notes.value[0] || null
    }
  }

  // Batch restore notes from trash.
  async function batchRestore(): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    await Promise.all(ids.map((id) => noteRepository.restore(id)))
    await loadNotes()
    selectedNoteIds.value.clear()
  }

  // Batch move selected notes to category.
  async function batchMoveToCategory(categoryId: string | null): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    await Promise.all(ids.map((id) => noteRepository.update(id, { categoryId })))
    await loadNotes()
    selectedNoteIds.value.clear()
  }

  // 闂佹彃绉甸弻濠囧箳閹烘垹纰嶉柨娑樼墛鐎氬骞忛弬銈囩
  async function reorderNotes(draggedId: string, targetId: string): Promise<void> {
    const draggedIndex = notes.value.findIndex(n => n.id === draggedId)
    const targetIndex = notes.value.findIndex(n => n.id === targetId)

    if (draggedIndex === -1 || targetIndex === -1) return

    // 濠碘€冲€归悘澶娾槈婢跺﹤鎸ょ紓鍐惧櫍閵嗗﹪鎮╅懜纰樺亾娴ｉ鐟濋柛姘焿缁辨繃绋夊鍜佹П闁荤偛妫欐晶婊堝礉閵婏箑绗撻幖鏉戦獜缁辨瑧绱旈鈧妴濠冩叏鐎ｎ剛鐭掗柛锔哄姂閵嗗﹪鏌堥…鎺旂
    if (notes.value[draggedIndex].isPinned !== notes.value[targetIndex].isPinned) return

    const [draggedNote] = notes.value.splice(draggedIndex, 1)
    notes.value.splice(targetIndex, 0, draggedNote)

    // Persist reordered order values in parallel.
    const updates: Promise<void>[] = []
    for (let i = 0; i < notes.value.length; i++) {
      if (notes.value[i].order !== i) {
        updates.push(noteRepository.update(notes.value[i].id, { order: i }))
        notes.value[i].order = i
      }
    }
    if (updates.length > 0) {
      await Promise.all(updates)
    }
  }

  // Initialize store data and last-view state.
  async function initialize(): Promise<void> {
    // Restore last view state from localStorage.
    const lastView = localStorage.getItem('lastView') as ViewType | null
    const lastCategoryId = localStorage.getItem('lastCategoryId')
    
    if (lastView) {
      currentView.value = lastView
      if (lastView === 'category' && lastCategoryId) {
        currentCategoryId.value = lastCategoryId
      }
    }
    
    await loadNotes()
    if (notes.value.length > 0) {
      currentNote.value = notes.value[0]
    }
  }

  return {
    // state
    notes,
    currentNote,
    currentView,
    currentCategoryId,
    searchKeyword,
    isLoading,
    totalNotesCount,
    isSelectionMode,
    selectedNoteIds,

    // computed
    noteCount,
    pinnedNotes,
    selectedCount,
    isAllSelected,

    // actions
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
    cleanupEmptyCurrentNote,
    reorderNotes,

    // batch actions
    toggleSelectionMode,
    exitSelectionMode,
    toggleNoteSelection,
    toggleSelectAll,
    batchDelete,
    batchPermanentDelete,
    batchRestore,
    batchMoveToCategory
  }
})


