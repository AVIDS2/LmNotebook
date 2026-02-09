import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { noteRepository, type Note, type CreateNoteInput, type UpdateNoteInput } from '@/database/noteRepository'
import { createDeferredEmptyNoteCleanup } from '@/utils/deferredNoteCleanup.mjs'

export type ViewType = 'all' | 'pinned' | 'category' | 'trash'

// 娴犲骸鍞寸€瑰湱鏁撻幋鎰垼妫版﹫绱欓崣鏍у30娑擃亜鐡х粭锔肩礆
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
  const totalNotesCount = ref(0) // 閸忋劑鍎寸粭鏃囶唶閹粯鏆熼敍鍫滅瑝閸栧懏瀚鎻掑灩闂勩倧绱?
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

  // 閸掑洦宕茬憴鍡楁禈閿涘牅绱板〒鍛倞缁岃櫣鐟拋甯礆
  async function setView(view: ViewType, categoryId?: string): Promise<void> {
    // 閸掑洦宕查崜宥嗩梾閺屻儱缍嬮崜宥囩應鐠佺増妲搁崥锔胯礋缁岀尨绱濇俊鍌涚亯閺勵垰鍨崚鐘绘珟
    await cleanupEmptyCurrentNote()

    currentView.value = view
    currentCategoryId.value = categoryId || null
    searchKeyword.value = ''
    
    // 娣囨繂鐡ㄨぐ鎾冲鐟欏棗娴樻担宥囩枂閿?localStorage
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
    // Cleanup possible empty draft before creating a new note.
    await cleanupEmptyCurrentNote()

    const note = await noteRepository.create(input)
    await loadNotes({ updateTotalCount: false })
    await updateTotalCount()
    currentNote.value = note
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

  // 閹垹顦茬粭鏃囶唶
  async function restoreNote(id: string): Promise<void> {
    await noteRepository.restore(id)
    const updated = await noteRepository.getById(id)
    if (updated) {
      applyNoteUpdate(updated)
    }
  }

  // 濮橀晲绠欓崚鐘绘珟
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
    
    // 濞撳懐鈹栭崶鐐存暪缁旀瑱绱欐导姘倱濮濄儲绔婚悶鍡楁倻闁插繒鍌ㄥ鏇礆
    await noteRepository.emptyTrash()
    notes.value = []
    currentNote.value = null
    
    // 濞撳懐鎮婇張顏冨▏閻劎娈戦崶鍓у
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

  // ========== 閹靛綊鍣洪幙宥勭稊 ==========
  
  // 鏉╂稑鍙?闁偓閸戞椽鈧瀚ㄥΟ鈥崇础
  function toggleSelectionMode(): void {
    isSelectionMode.value = !isSelectionMode.value
    if (!isSelectionMode.value) {
      selectedNoteIds.value.clear()
    }
  }

  // 闁偓閸戞椽鈧瀚ㄥΟ鈥崇础
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
    for (const id of ids) {
      await noteRepository.softDelete(id)
    }
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
    for (const id of ids) {
      await noteRepository.permanentDelete(id)
    }
    await loadNotes()
    selectedNoteIds.value.clear()
    
    if (currentNote.value && ids.includes(currentNote.value.id)) {
      currentNote.value = notes.value[0] || null
    }
  }

  // 閹靛綊鍣洪幁銏狀槻
  async function batchRestore(): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    for (const id of ids) {
      await noteRepository.restore(id)
    }
    await loadNotes()
    selectedNoteIds.value.clear()
  }

  // Batch move selected notes to category.
  async function batchMoveToCategory(categoryId: string | null): Promise<void> {
    const ids = Array.from(selectedNoteIds.value)
    for (const id of ids) {
      await noteRepository.update(id, { categoryId })
    }
    await loadNotes()
    selectedNoteIds.value.clear()
  }

  // 闁插秵鏌婇幒鎺戠碍閿涘牊瀚嬮幏鏂ょ礆
  async function reorderNotes(draggedId: string, targetId: string): Promise<void> {
    const draggedIndex = notes.value.findIndex(n => n.id === draggedId)
    const targetIndex = notes.value.findIndex(n => n.id === targetId)

    if (draggedIndex === -1 || targetIndex === -1) return

    // 婵″倹鐏夊☉澶婂挤缂冾噣銆婇悩鑸碘偓浣风瑝閸氬矉绱濇稉宥咁槱閻炲棙澧滈崝銊﹀笓鎼村骏绱欑純顕€銆婃慨瀣矒閸︺劑銆婇柈顭掔礆
    if (notes.value[draggedIndex].isPinned !== notes.value[targetIndex].isPinned) return

    const [draggedNote] = notes.value.splice(draggedIndex, 1)
    notes.value.splice(targetIndex, 0, draggedNote)

    // Persist reordered order values.
    for (let i = 0; i < notes.value.length; i++) {
      if (notes.value[i].order !== i) {
        await noteRepository.update(notes.value[i].id, { order: i })
        notes.value[i].order = i
      }
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
    // 閻樿鎷?    notes,
    currentNote,
    currentView,
    currentCategoryId,
    searchKeyword,
    isLoading,
    totalNotesCount,
    isSelectionMode,
    selectedNoteIds,

    // 鐠侊紕鐣荤仦鐑囨嫹?    noteCount,
    pinnedNotes,
    selectedCount,
    isAllSelected,

    // 閺傝纭?    loadNotes,
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
    
    // 閹靛綊鍣洪幙宥勭稊
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


