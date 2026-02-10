<template>
  <div
    class="note-card"
    :class="{
      'note-card--active': isActive && !isSelectionMode,
      'note-card--compact': viewMode === 'compact',
      'note-card--pinned': note.isPinned,
      'note-card--dragging': isDragging,
      'note-card--dragover': isDragOver,
      'note-card--selected': isSelected,
      'note-card--selection-mode': isSelectionMode
    }"
    :draggable="!isSelectionMode"
    :data-id="note.id"
    @click="handleClick"
    @dragstart="handleDragStart"
    @dragover.prevent="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
    @dragend="handleDragEnd"
  >
    <div v-if="isSelectionMode" class="note-card__checkbox" @click.stop="emit('toggle-select')">
      <div class="note-card__checkbox-inner" :class="{ 'note-card__checkbox-inner--checked': isSelected }">
        <svg v-if="isSelected" width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2.5 6L5 8.5L9.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <div v-if="!isSelectionMode" class="note-card__status">
      <div v-if="note.isLocked" class="note-card__lock" :title="locale === 'zh-CN' ? '已加锁' : 'Locked'">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <rect x="2.5" y="5.5" width="7" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/>
          <path d="M4 5.5V4.2C4 3 4.9 2 6 2C7.1 2 8 3 8 4.2V5.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      </div>
      <div v-if="note.isPinned" class="note-card__pin" :title="locale === 'zh-CN' ? '已置顶' : 'Pinned'">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1L7 4L10 4.5L7.5 7L8 11L6 9.5L4 11L4.5 7L2 4.5L5 4L6 1Z" fill="currentColor"/>
        </svg>
      </div>
    </div>

    <h3 class="note-card__title" v-html="highlightedTitle"></h3>
    <p class="note-card__preview" v-html="highlightedPreview"></p>

    <div class="note-card__footer">
      <span class="note-card__date">{{ formatDate(note.updatedAt) }}</span>
      <span v-if="categoryName" class="note-card__category" :style="{ background: categoryColor }">
        {{ categoryName }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Note } from '@/services/database'
import { useCategoryStore } from '@/stores/categoryStore'
import { useNoteStore } from '@/stores/noteStore'
import { useI18n } from '@/i18n'

const props = defineProps<{
  note: Note
  viewMode?: 'card' | 'compact'
  isActive: boolean
  isDragging?: boolean
  isDragOver?: boolean
  isSelectionMode?: boolean
  isSelected?: boolean
}>()

const emit = defineEmits<{
  click: []
  'toggle-select': []
  dragstart: [id: string]
  dragover: [id: string]
  dragleave: []
  drop: [id: string]
  dragend: []
}>()

const categoryStore = useCategoryStore()
const noteStore = useNoteStore()
const { t, locale } = useI18n()

function handleClick() {
  emit('click')
}

function handleDragStart(e: DragEvent) {
  if (props.isSelectionMode) {
    e.preventDefault()
    return
  }
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', props.note.id)
    e.dataTransfer.setData('source/type', 'note')
    ;(window as any)._draggedNoteId = props.note.id
  }
  emit('dragstart', props.note.id)
}

function handleDragOver() {
  if (props.isSelectionMode) return
  emit('dragover', props.note.id)
}

function handleDragLeave() {
  emit('dragleave')
}

function handleDrop() {
  if (props.isSelectionMode) return
  emit('drop', props.note.id)
}

function handleDragEnd() {
  ;(window as any)._draggedNoteId = null
  emit('dragend')
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function highlightText(text: string, keyword: string): string {
  if (!keyword || !text) return escapeHtml(text)
  const escaped = escapeHtml(text)
  const escapedKeyword = escapeHtml(keyword)
  const regex = new RegExp(`(${escapedKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const displayTitle = computed(() => props.note.title || t('common.untitled'))

const displayPreview = computed(() => {
  const text = props.note.plainText.trim()
  if (!text) return locale.value === 'zh-CN' ? '暂无内容...' : 'No content yet...'
  return text.length > 60 ? `${text.slice(0, 60)}...` : text
})

const highlightedTitle = computed(() => highlightText(displayTitle.value, noteStore.searchKeyword))
const highlightedPreview = computed(() => highlightText(displayPreview.value, noteStore.searchKeyword))

const category = computed(() => categoryStore.getCategoryById(props.note.categoryId))
const categoryName = computed(() => category.value?.name)
const categoryColor = computed(() => category.value?.color)

function formatDate(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString(locale.value, { hour: '2-digit', minute: '2-digit' })
  }

  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return locale.value === 'zh-CN' ? '昨天' : 'Yesterday'
  }

  return date.toLocaleDateString(locale.value, { month: 'short', day: 'numeric' })
}
</script>
<style lang="scss" scoped>
.note-card {
  position: relative;
  padding: $spacing-md;
  background: var(--color-bg-card);
  border: 1px solid color-mix(in srgb, var(--color-border) 42%, transparent);
  border-radius: $radius-lg;
  margin-bottom: $spacing-sm;
  cursor: pointer;
  
  // Performance-oriented transitions with light motion.
  transition: background-color 0.16s ease,
              border-color 0.16s ease,
              transform 0.16s ease,
              box-shadow 0.16s ease;
  
  // Keep paint and layout work constrained for smoother scrolling.
  content-visibility: auto;
  contain: layout style paint;
  contain-intrinsic-size: 0 90px;
  will-change: transform;
  backface-visibility: hidden;
  -webkit-font-smoothing: antialiased;

  &:hover {
    background: var(--color-bg-hover);
    border-color: color-mix(in srgb, var(--color-border) 76%, transparent);
    transform: translateY(-1px);
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  }
  
  &:active {
    transform: translateY(0);
    transition-duration: 0.08s;
  }

  &--active {
    border-color: color-mix(in srgb, var(--color-accent) 36%, var(--color-border-dark));
    background: var(--color-bg-card);

    .note-card__title {
      color: var(--color-text-primary);
    }
  }

  &--pinned {
    border-left: 3px solid var(--color-accent);
  }

  &--dragging {
    opacity: 0.5;
    background: var(--color-bg-hover);
  }

  &--dragover {
    border-top: 2px solid var(--color-accent);
    background: var(--color-bg-active);
  }

  // Selection mode.
  &--selection-mode {
    padding-left: $spacing-md + 28px;
    cursor: pointer;

    &:hover {
      background: var(--color-bg-hover);
    }
  }

  &--selected {
    background: color-mix(in srgb, var(--color-accent) 10%, transparent);
    border-color: color-mix(in srgb, var(--color-accent) 30%, transparent);

    &:hover {
      background: color-mix(in srgb, var(--color-accent) 15%, transparent);
    }
  }

  &--compact {
    padding: 8px 10px;
    border-radius: $radius-md;
    margin-bottom: 4px;
    border-width: 1px;
    contain-intrinsic-size: 0 44px;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    }

    .note-card__status {
      top: 9px;
      right: 8px;
      gap: 4px;
    }

    .note-card__title {
      margin-bottom: 2px;
      padding-right: 26px;
      font-size: $font-size-sm;
      font-weight: 500;
    }

    .note-card__preview {
      margin-bottom: 0;
      -webkit-line-clamp: 1;
      font-size: 12px;
      color: var(--color-text-muted);
    }

    .note-card__footer {
      margin-top: 4px;
    }

    .note-card__category {
      padding: 1px 6px;
      font-size: 11px;
    }
  }
}

// Selection checkbox.
.note-card__checkbox {
  position: absolute;
  left: $spacing-md;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1;
}

.note-card__checkbox-inner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border-dark);
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  transition: background-color 0.1s ease, 
              border-color 0.1s ease;

  &:hover {
    border-color: var(--color-accent);
  }

  &--checked {
    background: var(--color-accent);
    border-color: var(--color-accent);
    color: white;
  }
}

.note-card__status {
  position: absolute;
  top: $spacing-sm;
  right: $spacing-sm;
  display: flex;
  gap: 6px;
  align-items: center;
}

.note-card__lock {
  color: var(--color-text-muted);
}

.note-card__pin {
  color: var(--color-accent);
}

.note-card__title {
  font-size: $font-size-md;
  font-weight: 500;
  margin-bottom: $spacing-xs;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 32px;
  color: var(--color-text-primary);
}

.note-card__preview {
  font-size: $font-size-sm;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: $spacing-sm;
}

.note-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.note-card__date {
  font-size: $font-size-xs;
  color: var(--color-text-muted);
}

.note-card__category {
  font-size: $font-size-xs;
  padding: 2px 8px;
  border-radius: $radius-sm;
  color: white;
}

// Search highlight style.
:deep(.search-highlight) {
  background: #fef08a;
  color: #854d0e;
  padding: 0 2px;
  border-radius: 2px;
}
</style>

