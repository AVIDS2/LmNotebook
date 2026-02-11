<template>
  <div class="note-list" :class="{ 'note-list--collapsed': collapsed }">
    <SearchBar v-if="!collapsed" />

    <div class="note-list__header">
      <div v-if="!collapsed" class="note-list__header-left">
        <label v-if="noteStore.isSelectionMode" class="note-list__checkbox-wrapper">
          <input
            ref="selectAllCheckbox"
            type="checkbox"
            :checked="noteStore.isAllSelected"
            @change="noteStore.toggleSelectAll"
            class="note-list__checkbox"
          />
        </label>
        <span class="note-list__title">{{ shortHeaderTitle }}</span>
        <span class="note-list__count">{{ noteCount }}</span>
      </div>

      <div class="note-list__header-actions">
        <button
          v-if="!collapsed && noteCount > 0"
          class="note-list__action-btn"
          :class="{ 'note-list__action-btn--active': uiStore.noteListLayerMode === 'category' }"
          :title="uiStore.noteListLayerMode === 'category' ? t('noteList.switchLayerOff') : t('noteList.switchLayerOn')"
          @click="uiStore.toggleNoteListLayerMode"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2.5" width="12" height="3" rx="1" stroke="currentColor" stroke-width="1.2"/>
            <rect x="2" y="7.5" width="12" height="3" rx="1" stroke="currentColor" stroke-width="1.2"/>
            <rect x="2" y="12.5" width="12" height="1" rx="0.5" fill="currentColor"/>
          </svg>
        </button>

        <button
          class="note-list__action-btn"
          :title="collapsed ? t('noteList.expandList') : t('noteList.collapseList')"
          @click="$emit('toggle-collapse')"
        >
          <svg v-if="collapsed" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 3L10 8L6 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 3L6 8L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <button
          v-if="!collapsed && noteCount > 0"
          class="note-list__action-btn"
          :class="{ 'note-list__action-btn--active': noteStore.isSelectionMode }"
          @click="noteStore.toggleSelectionMode"
          :title="noteStore.isSelectionMode ? t('noteList.exitBatchManage') : t('noteList.batchManage')"
        >
          <svg v-if="!noteStore.isSelectionMode" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 8L7 11L12 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <Transition name="toolbar-slide">
      <div v-if="!collapsed && noteStore.isSelectionMode && noteStore.selectedCount > 0" class="note-list__toolbar">
        <span class="note-list__toolbar-count">{{ t('noteList.selectedCount', { count: noteStore.selectedCount }) }}</span>
        <div class="note-list__toolbar-actions">
          <template v-if="noteStore.currentView === 'trash'">
            <button class="note-list__toolbar-btn note-list__toolbar-btn--restore" @click="handleBatchRestore">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7C2 4.23858 4.23858 2 7 2C8.85652 2 10.4869 3.00442 11.3912 4.5M12 7C12 9.76142 9.76142 12 7 12C5.14348 12 3.51314 10.9956 2.60876 9.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                <path d="M11 2V5H8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ t('common.restore') }}
            </button>
            <button class="note-list__toolbar-btn note-list__toolbar-btn--danger" @click="handleBatchPermanentDelete">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 4H12M5 4V3C5 2.44772 5.44772 2 6 2H8C8.55228 2 9 2.44772 9 3V4M11 4V11C11 11.5523 10.5523 12 10 12H4C3.44772 12 3 11.5523 3 11V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              {{ t('noteList.permanentDelete') }}
            </button>
          </template>

          <template v-else>
            <button class="note-list__toolbar-btn note-list__toolbar-btn--danger" @click="handleBatchDelete">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 4H12M5 4V3C5 2.44772 5.44772 2 6 2H8C8.55228 2 9 2.44772 9 3V4M11 4V11C11 11.5523 10.5523 12 10 12H4C3.44772 12 3 11.5523 3 11V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              {{ t('common.delete') }}
            </button>
          </template>
        </div>
      </div>
    </Transition>

    <div v-if="!collapsed" class="note-list__content" ref="listContainerRef" @scroll="handleScroll">
      <div v-if="isLayeredByCategory" class="note-list__layers">
        <div v-for="layer in noteLayers" :key="layer.id" class="note-list__layer">
          <button class="note-list__layer-header" @click="toggleLayerCollapsed(layer.id)">
            <span class="note-list__layer-title">{{ layer.title }}</span>
            <span class="note-list__layer-count">{{ layer.notes.length }}</span>
            <svg
              class="note-list__layer-chevron"
              :class="{ 'note-list__layer-chevron--collapsed': isLayerCollapsed(layer.id) }"
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
            >
              <path d="M4 5.5L7 8.5L10 5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <Transition name="layer-body">
            <div v-show="!isLayerCollapsed(layer.id)" class="note-list__layer-body">
              <NoteCard
                v-for="note in layer.notes"
                :key="note.id"
                :note="note"
                :view-mode="'compact'"
                :is-active="noteStore.currentNote?.id === note.id"
                :is-dragging="draggedNoteId === note.id"
                :is-dragover="dragOverNoteId === note.id"
                :is-selection-mode="noteStore.isSelectionMode"
                :is-selected="noteStore.selectedNoteIds.has(note.id)"
                @click="handleNoteClick(note)"
                @contextmenu="handleNoteContextMenu(note, $event)"
                @toggle-select="noteStore.toggleNoteSelection(note.id)"
                @dragstart="handleDragStart"
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
                @dragend="handleDragEnd"
              />
            </div>
          </Transition>
        </div>
      </div>

      <template v-else>
        <div class="note-list__virtual-spacer" :style="{ height: virtualSpacerTop + 'px' }"></div>
        <TransitionGroup name="list" tag="div" :css="!isVirtualScrolling">
          <NoteCard
            v-for="note in visibleNotes"
            :key="note.id"
            :note="note"
            :view-mode="'compact'"
            :is-active="noteStore.currentNote?.id === note.id"
            :is-dragging="draggedNoteId === note.id"
            :is-dragover="dragOverNoteId === note.id"
            :is-selection-mode="noteStore.isSelectionMode"
            :is-selected="noteStore.selectedNoteIds.has(note.id)"
            @click="handleNoteClick(note)"
            @contextmenu="handleNoteContextMenu(note, $event)"
            @toggle-select="noteStore.toggleNoteSelection(note.id)"
            @dragstart="handleDragStart"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
            @dragend="handleDragEnd"
          />
        </TransitionGroup>
        <div class="note-list__virtual-spacer" :style="{ height: virtualSpacerBottom + 'px' }"></div>
      </template>

      <div v-if="noteCount === 0" class="note-list__empty">
        <svg width="44" height="44" viewBox="0 0 48 48" fill="none">
          <rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" stroke-width="2"/>
          <path d="M16 16H32M16 24H28M16 32H24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>{{ emptyText }}</p>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="noteContextMenu.visible"
        class="note-list__context-menu-overlay"
        @click="hideNoteContextMenu"
      ></div>
      <div
        v-if="noteContextMenu.visible && noteContextMenu.note"
        ref="noteContextMenuRef"
        class="note-list__context-menu"
        :style="noteContextMenuStyle"
        @click.stop
      >
        <button class="note-list__context-menu-item" @click="handleOpenFromContextMenu">
          {{ t('noteList.contextOpen') }}
        </button>
        <button
          v-if="noteStore.currentView !== 'trash'"
          class="note-list__context-menu-item"
          @click="handleTogglePinFromContextMenu"
        >
          {{ noteContextMenu.note.isPinned ? t('noteList.contextUnpin') : t('noteList.contextPin') }}
        </button>
        <button
          v-if="noteStore.currentView !== 'trash'"
          class="note-list__context-menu-item"
          @click="handleMoveToNoCategoryFromContextMenu"
        >
          {{ t('noteList.contextMoveToNoCategory') }}
        </button>
        <button
          v-for="category in categoryStore.categories"
          v-if="noteStore.currentView !== 'trash'"
          :key="category.id"
          class="note-list__context-menu-item"
          @click="handleMoveToCategoryFromContextMenu(category.id)"
        >
          {{ t('noteList.contextMoveToCategory', { name: category.name }) }}
        </button>
        <div class="note-list__context-menu-divider"></div>
        <button
          v-if="noteStore.currentView === 'trash'"
          class="note-list__context-menu-item"
          @click="handleRestoreFromContextMenu"
        >
          {{ t('common.restore') }}
        </button>
        <button
          v-if="noteStore.currentView === 'trash'"
          class="note-list__context-menu-item note-list__context-menu-item--danger"
          @click="handlePermanentDeleteFromContextMenu"
        >
          {{ t('noteList.permanentDelete') }}
        </button>
        <button
          v-if="noteStore.currentView !== 'trash'"
          class="note-list__context-menu-item note-list__context-menu-item--danger"
          @click="handleDeleteFromContextMenu"
        >
          {{ t('common.delete') }}
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, reactive, nextTick } from 'vue'
import { useNoteStore } from '@/stores/noteStore'
import type { Note } from '@/database/noteRepository'
import NoteCard from './NoteCard.vue'
import SearchBar from '@/components/search/SearchBar.vue'
import { useI18n } from '@/i18n'
import { useUIStore } from '@/stores/uiStore'
import { useCategoryStore } from '@/stores/categoryStore'

const noteStore = useNoteStore()
const uiStore = useUIStore()
const categoryStore = useCategoryStore()
const { t, locale } = useI18n()

defineProps<{ collapsed?: boolean }>()
defineEmits<{ (e: 'toggle-collapse'): void }>()

const selectAllCheckbox = ref<HTMLInputElement | null>(null)
const collapsedLayers = ref<Record<string, boolean>>({})
const allNotes = computed<Note[]>(() => noteStore.notes ?? [])
const noteCount = computed(() => allNotes.value.length)
const listContainerRef = ref<HTMLElement | null>(null)

const ITEM_HEIGHT = 62
const BUFFER_SIZE = 5
const VIRTUAL_THRESHOLD = 60
const scrollTop = ref(0)
const containerHeight = ref(400)

const isLayeredByCategory = computed(() => uiStore.noteListLayerMode === 'category' && !noteStore.isSelectionMode)
const isVirtualScrolling = computed(() => !isLayeredByCategory.value && noteCount.value > VIRTUAL_THRESHOLD)

type NoteLayer = {
  id: string
  title: string
  notes: Note[]
}

const noteLayers = computed<NoteLayer[]>(() => {
  if (!isLayeredByCategory.value) return []

  const ordered = new Map<string, NoteLayer>()
  for (const note of allNotes.value) {
    const key = note.categoryId || '__uncategorized__'
    if (!ordered.has(key)) {
      const category = note.categoryId ? categoryStore.getCategoryById(note.categoryId) : null
      ordered.set(key, {
        id: key,
        title: category?.name || t('noteList.layerUncategorized'),
        notes: []
      })
    }
    ordered.get(key)!.notes.push(note)
  }
  return Array.from(ordered.values())
})

function toggleLayerCollapsed(layerId: string): void {
  collapsedLayers.value[layerId] = !collapsedLayers.value[layerId]
}

function isLayerCollapsed(layerId: string): boolean {
  return collapsedLayers.value[layerId] ?? true
}

const visibleRange = computed(() => {
  if (!isVirtualScrolling.value) {
    return { start: 0, end: noteCount.value }
  }

  const start = Math.max(0, Math.floor(scrollTop.value / ITEM_HEIGHT) - BUFFER_SIZE)
  const visibleCount = Math.ceil(containerHeight.value / ITEM_HEIGHT) + BUFFER_SIZE * 2
  const end = Math.min(noteCount.value, start + visibleCount)

  return { start, end }
})

watch(
  noteLayers,
  (layers) => {
    const nextState: Record<string, boolean> = {}
    for (const layer of layers) {
      nextState[layer.id] = collapsedLayers.value[layer.id] ?? true
    }
    collapsedLayers.value = nextState
  },
  { immediate: true }
)

const visibleNotes = computed(() => {
  const { start, end } = visibleRange.value
  return allNotes.value.slice(start, end)
})

const virtualSpacerTop = computed(() => {
  if (!isVirtualScrolling.value) return 0
  return visibleRange.value.start * ITEM_HEIGHT
})

const virtualSpacerBottom = computed(() => {
  if (!isVirtualScrolling.value) return 0
  return (noteCount.value - visibleRange.value.end) * ITEM_HEIGHT
})

let scrollRAF: number | null = null
function handleScroll() {
  if (scrollRAF) return
  scrollRAF = requestAnimationFrame(() => {
    if (listContainerRef.value) {
      scrollTop.value = listContainerRef.value.scrollTop
    }
    scrollRAF = null
  })
}

let resizeObserver: ResizeObserver | null = null
onMounted(() => {
  if (listContainerRef.value) {
    containerHeight.value = listContainerRef.value.clientHeight

    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerHeight.value = entry.contentRect.height
      }
    })
    resizeObserver.observe(listContainerRef.value)
  }
  window.addEventListener('resize', updateContextMenuPosition)
  window.addEventListener('scroll', updateContextMenuPosition, true)
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (scrollRAF) {
    cancelAnimationFrame(scrollRAF)
  }
  window.removeEventListener('resize', updateContextMenuPosition)
  window.removeEventListener('scroll', updateContextMenuPosition, true)
})

const draggedNoteId = ref<string | null>(null)
const dragOverNoteId = ref<string | null>(null)
const noteContextMenuRef = ref<HTMLElement | null>(null)
const noteContextMenu = reactive<{
  visible: boolean
  x: number
  y: number
  note: Note | null
}>({
  visible: false,
  x: 0,
  y: 0,
  note: null
})

const noteContextMenuStyle = computed(() => ({
  left: `${noteContextMenu.x}px`,
  top: `${noteContextMenu.y}px`
}))

watch(
  () => noteStore.currentView,
  () => {
    hideNoteContextMenu()
  }
)

watch(
  () => [noteStore.selectedCount, noteStore.isAllSelected],
  () => {
    if (selectAllCheckbox.value) {
      selectAllCheckbox.value.indeterminate = noteStore.selectedCount > 0 && !noteStore.isAllSelected
    }
  },
  { flush: 'post' }
)

function handleNoteClick(note: Note) {
  if (noteStore.isSelectionMode) {
    noteStore.toggleNoteSelection(note.id)
  } else {
    noteStore.selectNote(note)
  }
}

function handleNoteContextMenu(note: Note, event: MouseEvent) {
  if (noteStore.isSelectionMode) return
  noteContextMenu.note = note
  noteContextMenu.visible = true
  noteContextMenu.x = event.clientX
  noteContextMenu.y = event.clientY
  nextTick(() => {
    updateContextMenuPosition()
    requestAnimationFrame(updateContextMenuPosition)
  })
}

function hideNoteContextMenu() {
  noteContextMenu.visible = false
  noteContextMenu.note = null
}

function updateContextMenuPosition() {
  if (!noteContextMenu.visible || !noteContextMenuRef.value) return
  const menuRect = noteContextMenuRef.value.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const padding = 8

  noteContextMenu.x = Math.max(
    padding,
    Math.min(noteContextMenu.x, viewportWidth - menuRect.width - padding)
  )
  noteContextMenu.y = Math.max(
    padding,
    Math.min(noteContextMenu.y, viewportHeight - menuRect.height - padding)
  )
}

async function handleOpenFromContextMenu() {
  if (!noteContextMenu.note) return
  handleNoteClick(noteContextMenu.note)
  hideNoteContextMenu()
}

async function handleTogglePinFromContextMenu() {
  const note = noteContextMenu.note
  if (!note) return
  await noteStore.togglePin(note.id)
  hideNoteContextMenu()
}

async function handleDeleteFromContextMenu() {
  const note = noteContextMenu.note
  if (!note) return
  await noteStore.deleteNote(note.id)
  hideNoteContextMenu()
}

async function handleRestoreFromContextMenu() {
  const note = noteContextMenu.note
  if (!note) return
  await noteStore.restoreNote(note.id)
  hideNoteContextMenu()
}

async function handlePermanentDeleteFromContextMenu() {
  const note = noteContextMenu.note
  if (!note) return
  if (!confirm(t('noteList.confirmBatchPermanentDelete', { count: 1 }))) return
  await noteStore.permanentDeleteNote(note.id)
  hideNoteContextMenu()
}

async function handleMoveToCategoryFromContextMenu(categoryId: string) {
  const note = noteContextMenu.note
  if (!note) return
  await noteStore.updateNote(note.id, { categoryId })
  hideNoteContextMenu()
}

async function handleMoveToNoCategoryFromContextMenu() {
  const note = noteContextMenu.note
  if (!note) return
  await noteStore.updateNote(note.id, { categoryId: null })
  hideNoteContextMenu()
}

function handleDragStart(id: string) {
  if (noteStore.isSelectionMode) return
  draggedNoteId.value = id
}

function handleDragOver(id: string) {
  if (noteStore.isSelectionMode) return
  if (draggedNoteId.value === id) return
  dragOverNoteId.value = id
}

function handleDragLeave() {
  dragOverNoteId.value = null
}

async function handleDrop(targetId: string) {
  if (noteStore.isSelectionMode) return
  if (draggedNoteId.value && draggedNoteId.value !== targetId) {
    await noteStore.reorderNotes(draggedNoteId.value, targetId)
  }
}

function handleDragEnd() {
  draggedNoteId.value = null
  dragOverNoteId.value = null
}

async function handleBatchDelete() {
  if (confirm(t('noteList.confirmBatchDelete', { count: noteStore.selectedCount }))) {
    await noteStore.batchDelete()
  }
}

async function handleBatchPermanentDelete() {
  if (confirm(t('noteList.confirmBatchPermanentDelete', { count: noteStore.selectedCount }))) {
    await noteStore.batchPermanentDelete()
  }
}

async function handleBatchRestore() {
  await noteStore.batchRestore()
}

const headerTitle = computed(() => {
  switch (noteStore.currentView) {
    case 'all':
      return t('noteList.all')
    case 'pinned':
      return t('noteList.pinned')
    case 'trash':
      return t('noteList.trash')
    case 'category':
      return t('noteList.category')
    default:
      return t('noteList.all')
  }
})

const shortHeaderTitle = computed(() => {
  const zh = locale.value === 'zh-CN'
  switch (noteStore.currentView) {
    case 'all':
      return zh ? '全部' : 'All'
    case 'pinned':
      return zh ? '置顶' : 'Pinned'
    case 'trash':
      return zh ? '回收' : 'Trash'
    case 'category':
      return zh ? '分类' : 'Category'
    default:
      return headerTitle.value
  }
})

const emptyText = computed(() => {
  if (noteStore.searchKeyword) {
    return t('noteList.emptySearch')
  }
  switch (noteStore.currentView) {
    case 'trash':
      return t('noteList.emptyTrash')
    case 'pinned':
      return t('noteList.emptyPinned')
    default:
      return t('noteList.emptyDefault')
  }
})
</script>

<style lang="scss" scoped>
.note-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--color-bg-secondary);
  border-right: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
}

.note-list--collapsed {
  .note-list__header {
    justify-content: center;
    padding: 8px 4px;
  }
}

.note-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 34px;
  padding: 6px 8px 4px;
}

.note-list__header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-list__header-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.note-list__checkbox-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.note-list__checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-accent);
}

.note-list__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.note-list__count {
  font-size: 11px;
  color: var(--color-text-muted);
}

.note-list__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.14s ease, border-color 0.14s ease, color 0.14s ease;

  &:hover {
    background: var(--color-bg-hover);
    border-color: color-mix(in srgb, var(--color-border) 64%, transparent);
    color: var(--color-text-primary);
  }

  &--active {
    background: color-mix(in srgb, var(--color-accent) 10%, transparent);
    border-color: color-mix(in srgb, var(--color-accent) 36%, transparent);
    color: color-mix(in srgb, var(--color-accent) 72%, var(--color-text-primary));
  }
}

.note-list__toolbar {
  margin: 4px 8px 6px;
  padding: 7px 8px;
  border: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-bg-primary) 94%, transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.note-list__toolbar-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.note-list__toolbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-list__toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  border-radius: 7px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;

  &--danger {
    color: #dc2626;
    border-color: color-mix(in srgb, #ef4444 34%, var(--color-border));
  }

  &--restore {
    color: #16a34a;
    border-color: color-mix(in srgb, #10b981 34%, var(--color-border));
  }
}

.toolbar-slide-enter-active,
.toolbar-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.toolbar-slide-enter-from,
.toolbar-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.note-list__content {
  flex: 1;
  overflow-y: auto;
  padding: 2px 8px 8px;
}

.note-list__virtual-spacer {
  flex-shrink: 0;
}

.note-list__layers {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.note-list__layer {
  border-radius: 8px;
}

.note-list__layer-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;

  &:hover {
    background: var(--color-bg-hover);
  }
}

.note-list__layer-title {
  font-size: 12px;
  font-weight: 600;
}

.note-list__layer-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--color-text-muted);
}

.note-list__layer-chevron {
  color: var(--color-text-muted);
  transition: transform 0.16s ease;
}

.note-list__layer-chevron--collapsed {
  transform: rotate(-90deg);
}

.note-list__layer-body {
  padding: 0;
}

.layer-body-enter-active,
.layer-body-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.layer-body-enter-from,
.layer-body-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.note-list__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 26px 12px;
  color: var(--color-text-muted);
  text-align: center;

  svg {
    margin-bottom: 10px;
    opacity: 0.52;
  }

  p {
    font-size: 12px;
  }
}

.note-list__context-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 13020;
}

.note-list__context-menu {
  position: fixed;
  min-width: 176px;
  max-width: min(320px, calc(100vw - 16px));
  max-height: min(60vh, 420px);
  overflow-y: auto;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--color-border) 62%, transparent);
  background: color-mix(in srgb, var(--color-bg-card) 94%, transparent);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 13021;
}

.note-list__context-menu-item {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 9px;
  padding: 8px 10px;
  text-align: left;
  font-size: 13px;
  color: var(--color-text-primary);
  cursor: pointer;

  &:hover {
    background: var(--color-bg-hover);
  }

  &--danger {
    color: var(--color-danger, #ef4444);

    &:hover {
      background: color-mix(in srgb, #ef4444 12%, transparent);
    }
  }
}

.note-list__context-menu-divider {
  height: 1px;
  background: color-mix(in srgb, var(--color-border) 70%, transparent);
  margin: 6px 2px;
}

.list-enter-active,
.list-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-6px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(6px);
}

.list-move {
  transition: transform 0.2s ease;
}

.list-leave-active {
  position: absolute;
  width: calc(100% - 16px);
}
</style>
