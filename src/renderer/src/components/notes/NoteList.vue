<template>
  <div class="note-list">
    <!-- 搜索栏 -->
    <SearchBar />

    <!-- 列表头部 -->
    <div class="note-list__header">
      <div class="note-list__header-left">
        <!-- 选择模式下的全选复选框 -->
        <label v-if="noteStore.isSelectionMode" class="note-list__checkbox-wrapper">
          <input 
            ref="selectAllCheckbox"
            type="checkbox" 
            :checked="noteStore.isAllSelected"
            @change="noteStore.toggleSelectAll"
            class="note-list__checkbox"
          />
        </label>
        <span class="note-list__title">{{ headerTitle }}</span>
        <span class="note-list__count">{{ noteStore.notes.length }} 篇</span>
      </div>
      
      <div class="note-list__header-actions">
        <!-- 批量管理按钮 -->
        <button 
          v-if="noteStore.notes.length > 0"
          class="note-list__action-btn"
          :class="{ 'note-list__action-btn--active': noteStore.isSelectionMode }"
          @click="noteStore.toggleSelectionMode"
          :title="noteStore.isSelectionMode ? '退出管理' : '批量管理'"
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

    <!-- 批量操作工具栏 -->
    <Transition name="toolbar-slide">
      <div v-if="noteStore.isSelectionMode && noteStore.selectedCount > 0" class="note-list__toolbar">
        <span class="note-list__toolbar-count">已选 {{ noteStore.selectedCount }} 项</span>
        <div class="note-list__toolbar-actions">
          <!-- 回收站视图：恢复和永久删除 -->
          <template v-if="noteStore.currentView === 'trash'">
            <button class="note-list__toolbar-btn note-list__toolbar-btn--restore" @click="handleBatchRestore">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7C2 4.23858 4.23858 2 7 2C8.85652 2 10.4869 3.00442 11.3912 4.5M12 7C12 9.76142 9.76142 12 7 12C5.14348 12 3.51314 10.9956 2.60876 9.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                <path d="M11 2V5H8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              恢复
            </button>
            <button class="note-list__toolbar-btn note-list__toolbar-btn--danger" @click="handleBatchPermanentDelete">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 4H12M5 4V3C5 2.44772 5.44772 2 6 2H8C8.55228 2 9 2.44772 9 3V4M11 4V11C11 11.5523 10.5523 12 10 12H4C3.44772 12 3 11.5523 3 11V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              永久删除
            </button>
          </template>
          <!-- 普通视图：删除 -->
          <template v-else>
            <button class="note-list__toolbar-btn note-list__toolbar-btn--danger" @click="handleBatchDelete">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 4H12M5 4V3C5 2.44772 5.44772 2 6 2H8C8.55228 2 9 2.44772 9 3V4M11 4V11C11 11.5523 10.5523 12 10 12H4C3.44772 12 3 11.5523 3 11V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              删除
            </button>
          </template>
        </div>
      </div>
    </Transition>

    <!-- 笔记列表 -->
    <div class="note-list__content" ref="listContainerRef" @scroll="handleScroll">
      <!-- 虚拟滚动：只渲染可见区域的笔记 -->
      <div class="note-list__virtual-spacer" :style="{ height: virtualSpacerTop + 'px' }"></div>
      <TransitionGroup name="list" tag="div" :css="!isVirtualScrolling">
        <NoteCard
          v-for="note in visibleNotes"
          :key="note.id"
          :note="note"
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

      <!-- 空状态 -->
      <div v-if="noteStore.notes.length === 0" class="note-list__empty">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" stroke-width="2"/>
          <path d="M16 16H32M16 24H28M16 32H24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>{{ emptyText }}</p>
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

const noteStore = useNoteStore()

// 全选复选框 ref
const selectAllCheckbox = ref<HTMLInputElement | null>(null)

// 虚拟滚动相关
const listContainerRef = ref<HTMLElement | null>(null)
const ITEM_HEIGHT = 98 // 预估每个笔记卡片高度（包含 margin）
const BUFFER_SIZE = 5 // 上下缓冲区大小
const VIRTUAL_THRESHOLD = 50 // 超过这个数量才启用虚拟滚动

const scrollTop = ref(0)
const containerHeight = ref(400)

// 是否启用虚拟滚动
const isVirtualScrolling = computed(() => noteStore.notes.length > VIRTUAL_THRESHOLD)

// 计算可见范围
const visibleRange = computed(() => {
  if (!isVirtualScrolling.value) {
    return { start: 0, end: noteStore.notes.length }
  }
  
  const start = Math.max(0, Math.floor(scrollTop.value / ITEM_HEIGHT) - BUFFER_SIZE)
  const visibleCount = Math.ceil(containerHeight.value / ITEM_HEIGHT) + BUFFER_SIZE * 2
  const end = Math.min(noteStore.notes.length, start + visibleCount)
  
  return { start, end }
})

// 可见的笔记
const visibleNotes = computed(() => {
  const { start, end } = visibleRange.value
  return noteStore.notes.slice(start, end)
})

// 虚拟滚动占位高度
const virtualSpacerTop = computed(() => {
  if (!isVirtualScrolling.value) return 0
  return visibleRange.value.start * ITEM_HEIGHT
})

const virtualSpacerBottom = computed(() => {
  if (!isVirtualScrolling.value) return 0
  return (noteStore.notes.length - visibleRange.value.end) * ITEM_HEIGHT
})

// 滚动处理（使用 RAF 节流）
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

// 监听容器大小变化
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

// 处理 indeterminate 状态
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

// 拖拽相关状态
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

// 批量操作处理
async function handleBatchDelete() {
  if (confirm(`确定要删除选中的 ${noteStore.selectedCount} 篇笔记吗？`)) {
    await noteStore.batchDelete()
  }
}

async function handleBatchPermanentDelete() {
  if (confirm(`确定要永久删除选中的 ${noteStore.selectedCount} 篇笔记吗？此操作不可恢复！`)) {
    await noteStore.batchPermanentDelete()
  }
}

async function handleBatchRestore() {
  await noteStore.batchRestore()
}

const headerTitle = computed(() => {
  switch (noteStore.currentView) {
    case 'all':
      return '全部笔记'
    case 'pinned':
      return '置顶笔记'
    case 'trash':
      return '回收站'
    case 'category':
      return '分类笔记'
    default:
      return '笔记'
  }
})

const emptyText = computed(() => {
  if (noteStore.searchKeyword) {
    return '没有找到匹配的笔记'
  }
  switch (noteStore.currentView) {
    case 'trash':
      return '回收站是空的'
    case 'pinned':
      return '没有置顶笔记'
    default:
      return '点击上方按钮创建第一篇笔记'
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

.note-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
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
  gap: $spacing-xs;
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
  width: 28px;
  height: 28px;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }

  &--active {
    background: var(--color-accent);
    color: white;

    &:hover {
      background: var(--color-accent);
      opacity: 0.9;
      color: white;
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

// 批量操作工具栏
.note-list__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
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
  border: none;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.15s ease;

  &:active {
    transform: scale(0.97);
  }

  &--danger {
    background: #FEE2E2;
    color: #DC2626;

    &:hover {
      background: #FECACA;
    }
  }

  &--restore {
    background: #DCFCE7;
    color: #16A34A;

    &:hover {
      background: #BBF7D0;
    }
  }
}

// 工具栏滑入动画
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

.note-list__virtual-spacer {
  flex-shrink: 0;
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

// 列表动画 - 苹果风格丝滑过渡
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

// 移动动画 - 使用 transform 而非 top/left
.list-move {
  transition: transform 0.25s cubic-bezier(0.25, 0.1, 0.25, 1);
}

// 离开时不占位，避免布局抖动
.list-leave-active {
  position: absolute;
  width: calc(100% - #{$spacing-sm * 2});
}
</style>
