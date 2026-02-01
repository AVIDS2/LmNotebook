<template>
  <div class="note-list">
    <!-- 搜索栏 -->
    <SearchBar />

    <!-- 列表头部 -->
    <div class="note-list__header">
      <span class="note-list__title">{{ headerTitle }}</span>
      <span class="note-list__count">{{ noteStore.notes.length }} 篇</span>
    </div>

    <!-- 笔记列表 -->
    <div class="note-list__content">
      <TransitionGroup name="list">
        <NoteCard
          v-for="note in noteStore.notes"
          :key="note.id"
          :note="note"
          :is-active="noteStore.currentNote?.id === note.id"
          :is-dragging="draggedNoteId === note.id"
          :is-dragover="dragOverNoteId === note.id"
          @click="noteStore.selectNote(note)"
          @dragstart="handleDragStart"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          @dragend="handleDragEnd"
        />
      </TransitionGroup>

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
import { ref, computed } from 'vue'
import { useNoteStore } from '@/stores/noteStore'
import NoteCard from './NoteCard.vue'
import SearchBar from '@/components/search/SearchBar.vue'

const noteStore = useNoteStore()

// 拖拽相关状态
const draggedNoteId = ref<string | null>(null)
const dragOverNoteId = ref<string | null>(null)

function handleDragStart(id: string) {
  draggedNoteId.value = id
}

function handleDragOver(id: string) {
  if (draggedNoteId.value === id) return
  dragOverNoteId.value = id
}

function handleDragLeave() {
  dragOverNoteId.value = null
}

async function handleDrop(targetId: string) {
  if (draggedNoteId.value && draggedNoteId.value !== targetId) {
    await noteStore.reorderNotes(draggedNoteId.value, targetId)
  }
}

function handleDragEnd() {
  draggedNoteId.value = null
  dragOverNoteId.value = null
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
  width: $notelist-width;
  background: $color-bg-primary;
  border-right: 1px solid $color-border-light;
}

.note-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid $color-border-light;
}

.note-list__title {
  font-size: $font-size-sm;
  font-weight: 500;
  color: $color-text-primary;
}

.note-list__count {
  font-size: $font-size-xs;
  color: $color-text-muted;
}

.note-list__content {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-sm;
}

.note-list__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
  color: $color-text-muted;
  text-align: center;

  svg {
    margin-bottom: $spacing-md;
    opacity: 0.5;
  }

  p {
    font-size: $font-size-sm;
  }
}
</style>
