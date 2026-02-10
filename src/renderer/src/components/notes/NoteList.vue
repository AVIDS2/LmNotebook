<template>
  <div class="note-list" :class="{ 'note-list--collapsed': collapsed }">
    <!-- 鍒楄〃澶撮儴 -->
    <div class="note-list__header">
      <div v-if="!collapsed" class="note-list__header-left">
        <!-- 閫夋嫨妯″紡涓嬬殑鍏ㄩ€夊閫夋 -->
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
        <!-- 鎵归噺绠＄悊鎸夐挳 -->
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

    <!-- 鎼滅储鏍?-->
    <SearchBar v-if="!collapsed" />

    <!-- 鎵归噺鎿嶄綔宸ュ叿鏍?-->
    <Transition name="toolbar-slide">
      <div v-if="!collapsed && noteStore.isSelectionMode && noteStore.selectedCount > 0" class="note-list__toolbar">
        <span class="note-list__toolbar-count">{{ t('noteList.selectedCount', { count: noteStore.selectedCount }) }}</span>
        <div class="note-list__toolbar-actions">
          <!-- 鍥炴敹绔欒鍥撅細鎭㈠鍜屾案涔呭垹闄?-->
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
          <!-- 鏅€氳鍥撅細鍒犻櫎 -->
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

    <!-- 绗旇鍒楄〃 -->
    <div v-if="!collapsed" class="note-list__content" ref="listContainerRef" @scroll="handleScroll">
      <div v-if="isLayeredByCategory" class="note-list__layers">
        <div
          v-for="layer in noteLayers"
          :key="layer.id"
          class="note-list__layer"
        >
          <button class="note-list__layer-header" @click="toggleLayerCollapsed(layer.id)">
            <span class="note-list__layer-title">
              {{ layer.title }}
            </span>
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

      <!-- 绌虹姸鎬?-->
      <div v-if="noteCount === 0" class="note-list__empty">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" stroke-width="2"/>
          <path d="M16 16H32M16 24H28M16 32H24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>{{ emptyText }}</p>
      </div>
    </div>

    <div v-if="!collapsed" class="note-list__mini-footer">
      <span class="note-list__mini-label">{{ t('noteList.footerLabel') }}</span>
      <div class="note-list__mini-actions">
        <button class="note-list__mini-btn" :title="t('sidebar.newNote')" @click="handleQuickNewNote">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2V12M2 7H12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="note-list__mini-btn" :title="t('sidebar.allNotes')" @click="noteStore.setView('all')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="2" y="2" width="10" height="10" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
            <path d="M4 5H10M4 8H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="note-list__mini-btn" :title="t('sidebar.pinnedNotes')" @click="noteStore.setView('pinned')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2L8 4.8L11 5.2L8.8 7.1L9.5 10.4L7 8.8L4.5 10.4L5.2 7.1L3 5.2L6 4.8L7 2Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
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
defineProps<{
  collapsed?: boolean
}>()
defineEmits<{
  (e: 'toggle-collapse'): void
}>()

// 鍏ㄩ€夊閫夋 ref
const selectAllCheckbox = ref<HTMLInputElement | null>(null)
const collapsedLayers = ref<Record<string, boolean>>({})
const allNotes = computed<Note[]>(() => noteStore.notes ?? [])
const noteCount = computed(() => allNotes.value.length)

// 铏氭嫙婊氬姩鐩稿叧
const listContainerRef = ref<HTMLElement | null>(null)
const ITEM_HEIGHT = 98
const BUFFER_SIZE = 5
const VIRTUAL_THRESHOLD = 50
const scrollTop = ref(0)
const containerHeight = ref(400)

// 鏄惁鍚敤铏氭嫙婊氬姩
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
  return Boolean(collapsedLayers.value[layerId])
}

// 璁＄畻鍙鑼冨洿
const visibleRange = computed(() => {
  if (!isVirtualScrolling.value) {
    return { start: 0, end: noteCount.value }
  }
  
  const start = Math.max(0, Math.floor(scrollTop.value / ITEM_HEIGHT) - BUFFER_SIZE)
  const visibleCount = Math.ceil(containerHeight.value / ITEM_HEIGHT) + BUFFER_SIZE * 2
  const end = Math.min(noteCount.value, start + visibleCount)
  
  return { start, end }
})

const visibleNotes = computed(() => {
  const { start, end } = visibleRange.value
  return allNotes.value.slice(start, end)
})

// 铏氭嫙婊氬姩鍗犱綅楂樺害
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

// 鐩戝惉瀹瑰櫒澶у皬鍙樺寲
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
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (scrollRAF) {
    cancelAnimationFrame(scrollRAF)
  }
})

watch(
  () => [noteStore.selectedCount, noteStore.isAllSelected],
  () => {
    if (selectAllCheckbox.value) {
      selectAllCheckbox.value.indeterminate = 
        noteStore.selectedCount > 0 && !noteStore.isAllSelected
    }
  },
  { flush: 'post' }
)

const draggedNoteId = ref<string | null>(null)
const dragOverNoteId = ref<string | null>(null)

function handleNoteClick(note: Note) {
  if (noteStore.isSelectionMode) {
    noteStore.toggleNoteSelection(note.id)
  } else {
    noteStore.selectNote(note)
  }
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

// 鎵归噺鎿嶄綔澶勭悊
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

async function handleQuickNewNote(): Promise<void> {
  await noteStore.createNote()
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
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border-light);
  transition: background-color 0.2s ease;
}

.note-list--collapsed {
  .note-list__header {
    justify-content: center;
    padding: $spacing-sm 4px;
  }
}

.note-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-bottom: 1px solid var(--color-border-light);
}

.note-list__header-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.note-list__header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-list__checkbox-wrapper {
  display: flex;
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

.note-list__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid color-mix(in srgb, var(--color-border) 52%, transparent);
  border-radius: 9px;
  background: color-mix(in srgb, var(--color-bg-primary) 95%, transparent);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.16s ease, color 0.16s ease, border-color 0.16s ease, transform 0.12s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
    border-color: var(--color-border);
    transform: translateY(-1px);
  }

  &--active {
    background: color-mix(in srgb, var(--color-accent) 12%, var(--color-bg-primary));
    color: color-mix(in srgb, var(--color-accent) 70%, var(--color-text-primary));
    border-color: color-mix(in srgb, var(--color-accent) 36%, var(--color-border));

    &:hover {
      background: color-mix(in srgb, var(--color-accent) 16%, var(--color-bg-primary));
      color: color-mix(in srgb, var(--color-accent) 78%, var(--color-text-primary));
    }
  }
}

.note-list__title {
  font-size: $font-size-sm;
  font-weight: 500;
  color: var(--color-text-primary);
}

.note-list__count {
  font-size: $font-size-xs;
  color: var(--color-text-muted);
}

.note-list__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  background: color-mix(in srgb, var(--color-bg-secondary) 90%, var(--color-bg-primary));
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
}

.note-list__toolbar-count {
  font-size: $font-size-xs;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.note-list__toolbar-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.note-list__toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid color-mix(in srgb, var(--color-border) 52%, transparent);
  border-radius: 9px;
  font-size: $font-size-xs;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.16s ease, transform 0.12s ease, border-color 0.16s ease;

  &:active {
    transform: scale(0.97);
  }

  &--danger {
    background: color-mix(in srgb, #ef4444 12%, var(--color-bg-primary));
    color: #DC2626;
    border-color: color-mix(in srgb, #ef4444 38%, var(--color-border));

    &:hover {
      background: color-mix(in srgb, #ef4444 16%, var(--color-bg-primary));
    }
  }

  &--restore {
    background: color-mix(in srgb, #10b981 14%, var(--color-bg-primary));
    color: #16A34A;
    border-color: color-mix(in srgb, #10b981 34%, var(--color-border));

    &:hover {
      background: color-mix(in srgb, #10b981 20%, var(--color-bg-primary));
    }
  }
}

.toolbar-slide-enter-active,
.toolbar-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.toolbar-slide-enter-from,
.toolbar-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.note-list__content {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-sm;
}

.note-list__mini-footer {
  height: 42px;
  border-top: 1px solid var(--color-border-light);
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 0 10px;
  flex-shrink: 0;
}

.note-list__mini-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.note-list__mini-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.note-list__mini-btn {
  width: 26px;
  height: 26px;
  border: 1px solid color-mix(in srgb, var(--color-border) 50%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-bg-primary) 94%, transparent);
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
    border-color: var(--color-border);
  }
}

.note-list__virtual-spacer {
  flex-shrink: 0;
}

.note-list__layers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-list__layer {
  border: 1px solid color-mix(in srgb, var(--color-border) 52%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, var(--color-bg-secondary) 84%, transparent);
  overflow: hidden;
}

.note-list__layer-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background-color 0.16s ease;

  &:hover {
    background: color-mix(in srgb, var(--color-bg-hover) 80%, transparent);
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
  transition: transform 0.18s ease;
}

.note-list__layer-chevron--collapsed {
  transform: rotate(-90deg);
}

.note-list__layer-body {
  padding: 0 6px 6px;
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
  padding: $spacing-xl;
  color: var(--color-text-muted);
  text-align: center;

  svg {
    margin-bottom: $spacing-md;
    opacity: 0.5;
  }

  p {
    font-size: $font-size-sm;
  }
}

// 鍒楄〃鍔ㄧ敾 - 鑻规灉椋庢牸涓濇粦杩囨浮
.list-enter-active,
.list-leave-active {
  transition: opacity 0.2s cubic-bezier(0.25, 0.1, 0.25, 1), 
              transform 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-8px) scale(0.98);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(8px) scale(0.98);
}

// 绉诲姩鍔ㄧ敾 - 浣跨敤 transform 鑰岄潪 top/left
.list-move {
  transition: transform 0.25s cubic-bezier(0.25, 0.1, 0.25, 1);
}

// 绂诲紑鏃朵笉鍗犱綅锛岄伩鍏嶅竷灞€鎶栧姩
.list-leave-active {
  position: absolute;
  width: calc(100% - #{$spacing-sm * 2});
}
</style>


