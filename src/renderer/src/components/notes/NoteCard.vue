<template>
  <div
    class="note-card"
    :class="{
      'note-card--active': isActive && !isSelectionMode,
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
    <!-- 选择复选框 -->
    <div v-if="isSelectionMode" class="note-card__checkbox" @click.stop="emit('toggle-select')">
      <div class="note-card__checkbox-inner" :class="{ 'note-card__checkbox-inner--checked': isSelected }">
        <svg v-if="isSelected" width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2.5 6L5 8.5L9.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <!-- 状态标识 -->
    <div v-if="!isSelectionMode" class="note-card__status">
      <div v-if="note.isLocked" class="note-card__lock" title="已加锁">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <rect x="2.5" y="5.5" width="7" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/>
          <path d="M4 5.5V4.2C4 3 4.9 2 6 2C7.1 2 8 3 8 4.2V5.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      </div>
      <div v-if="note.isPinned" class="note-card__pin" title="已置顶">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1L7 4L10 4.5L7.5 7L8 11L6 9.5L4 11L4.5 7L2 4.5L5 4L6 1Z" fill="currentColor"/>
        </svg>
      </div>
    </div>

    <!-- 标题 -->
    <h3 class="note-card__title" v-html="highlightedTitle"></h3>

    <!-- 预览内容 -->
    <p class="note-card__preview" v-html="highlightedPreview"></p>

    <!-- 底部信息 -->
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

const props = defineProps<{
  note: Note
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

function handleDragOver(e: DragEvent) {
  if (props.isSelectionMode) return
  emit('dragover', props.note.id)
}

function handleDragLeave() {
  emit('dragleave')
}

function handleDrop(e: DragEvent) {
  if (props.isSelectionMode) return
  emit('drop', props.note.id)
}

function handleDragEnd() {
  ;(window as any)._draggedNoteId = null
  emit('dragend')
}

const categoryStore = useCategoryStore()
const noteStore = useNoteStore()

// 转义 HTML 特殊字符
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 高亮搜索关键词
function highlightText(text: string, keyword: string): string {
  if (!keyword || !text) return escapeHtml(text)
  
  const escaped = escapeHtml(text)
  const escapedKeyword = escapeHtml(keyword)
  
  // 创建不区分大小写的正则
  const regex = new RegExp(`(${escapedKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const displayTitle = computed(() => {
  return props.note.title || '无标题笔记'
})

const displayPreview = computed(() => {
  const text = props.note.plainText.trim()
  if (!text) return '暂无内容...'
  return text.length > 60 ? text.slice(0, 60) + '...' : text
})

// 高亮后的标题
const highlightedTitle = computed(() => {
  return highlightText(displayTitle.value, noteStore.searchKeyword)
})

// 高亮后的预览
const highlightedPreview = computed(() => {
  return highlightText(displayPreview.value, noteStore.searchKeyword)
})

const category = computed(() => {
  return categoryStore.getCategoryById(props.note.categoryId)
})

const categoryName = computed(() => category.value?.name)
const categoryColor = computed(() => category.value?.color)

function formatDate(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  }

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style lang="scss" scoped>
.note-card {
  position: relative;
  padding: $spacing-md;
  background: var(--color-bg-card);
  border: 1.5px solid transparent;
  border-radius: $radius-lg;
  margin-bottom: $spacing-sm;
  cursor: pointer;
  
  // 性能优化：使用 GPU 加速的属性 + 苹果风格曲线
  transition: background-color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1), 
              border-color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1), 
              transform 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
              box-shadow 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  
  // 启用硬件加速和内容可见性优化
  content-visibility: auto;
  contain: layout style paint;
  contain-intrinsic-size: 0 90px;
  will-change: transform;
  backface-visibility: hidden;
  -webkit-font-smoothing: antialiased;

  &:hover {
    background: var(--color-bg-hover);
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  
  &:active {
    transform: scale(0.98);
    transition-duration: 0.1s;
  }

  &--active {
    border-color: var(--color-border-dark);
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

  // 选择模式样式
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
}

// 复选框
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

// 搜索高亮样式
:deep(.search-highlight) {
  background: #fef08a;
  color: #854d0e;
  padding: 0 2px;
  border-radius: 2px;
}
</style>
