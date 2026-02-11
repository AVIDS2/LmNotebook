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
    @contextmenu.prevent="handleContextMenu"
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

    <div class="note-card__content">
      <div class="note-card__row">
        <h3 class="note-card__title" v-html="highlightedTitle"></h3>
        <span v-if="categoryName" class="note-card__category">
          {{ categoryName }}
        </span>
      </div>

      <p v-if="!isCompact" class="note-card__preview" v-html="highlightedPreview"></p>

      <div class="note-card__meta">
        <span class="note-card__date">{{ formatDate(note.updatedAt) }}</span>
        <span class="note-card__meta-spacer"></span>
        <span v-if="note.isPinned" class="note-card__meta-badge">
          {{ locale === 'zh-CN' ? '置顶' : 'Pinned' }}
        </span>
        <span v-if="note.isLocked" class="note-card__meta-badge">
          {{ locale === 'zh-CN' ? '锁定' : 'Locked' }}
        </span>
      </div>
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
  contextmenu: [event: MouseEvent]
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
const isCompact = computed(() => props.viewMode === 'compact')

function handleClick() {
  emit('click')
}

function handleContextMenu(event: MouseEvent) {
  emit('contextmenu', event)
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
  padding: 6px 8px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 7px;
  margin-bottom: 1px;
  cursor: pointer;
  transition: background-color 0.14s ease, border-color 0.14s ease;
  content-visibility: auto;
  contain: layout style paint;
  contain-intrinsic-size: 0 58px;

  &:hover {
    background: color-mix(in srgb, var(--color-bg-hover) 88%, transparent);
    border-color: transparent;
  }

  &--active {
    border-color: color-mix(in srgb, var(--color-border) 64%, transparent);
    background: color-mix(in srgb, var(--color-bg-hover) 96%, transparent);
  }

  &--pinned {
    border-left: 1px solid color-mix(in srgb, var(--color-border-dark) 70%, transparent);
  }

  &--dragging {
    opacity: 0.5;
    background: var(--color-bg-hover);
  }

  &--dragover {
    border-top: 2px solid var(--color-accent);
    background: var(--color-bg-active);
  }

  &--selection-mode {
    padding-left: $spacing-md + 28px;
  }

  &--selected {
    background: color-mix(in srgb, var(--color-accent) 10%, transparent);
    border-color: color-mix(in srgb, var(--color-accent) 30%, transparent);

    &:hover {
      background: color-mix(in srgb, var(--color-accent) 15%, transparent);
    }
  }

  &--compact {
    contain-intrinsic-size: 0 56px;
  }
}

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
  transition: background-color 0.1s ease, border-color 0.1s ease;

  &:hover {
    border-color: var(--color-accent);
  }

  &--checked {
    background: var(--color-accent);
    border-color: var(--color-accent);
    color: #fff;
  }
}

.note-card__content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.note-card__row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.note-card__title {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 460;
  margin-bottom: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.note-card__preview {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0;
}

.note-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 16px;
}

.note-card__date {
  font-size: 11px;
  color: var(--color-text-muted);
}

.note-card__meta-spacer {
  flex: 1;
}

.note-card__meta-badge {
  font-size: 10px;
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.note-card__category {
  font-size: 10px;
  line-height: 1;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  opacity: 0.82;
}

:deep(.search-highlight) {
  background: color-mix(in srgb, var(--color-accent) 26%, transparent);
  color: var(--color-text-primary);
  padding: 0 2px;
  border-radius: 2px;
}
</style>
