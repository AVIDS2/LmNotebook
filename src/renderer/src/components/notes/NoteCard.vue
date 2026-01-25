<template>
  <div
    class="note-card"
    :class="{
      'note-card--active': isActive,
      'note-card--pinned': note.isPinned
    }"
  >
    <!-- 置顶标识 -->
    <div v-if="note.isPinned" class="note-card__pin">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M6 1L7 4L10 4.5L7.5 7L8 11L6 9.5L4 11L4.5 7L2 4.5L5 4L6 1Z" fill="currentColor"/>
      </svg>
    </div>

    <!-- 标题 -->
    <h3 class="note-card__title">
      {{ displayTitle }}
    </h3>

    <!-- 预览内容 -->
    <p class="note-card__preview">
      {{ displayPreview }}
    </p>

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
import type { Note } from '@/types/note'
import { useCategoryStore } from '@/stores/categoryStore'

const props = defineProps<{
  note: Note
  isActive: boolean
}>()

const categoryStore = useCategoryStore()

const displayTitle = computed(() => {
  return props.note.title || '无标题笔记'
})

const displayPreview = computed(() => {
  const text = props.note.plainText.trim()
  if (!text) return '暂无内容...'
  return text.length > 60 ? text.slice(0, 60) + '...' : text
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
  background: $color-bg-card;
  border: 1.5px solid transparent;
  border-radius: $radius-lg;
  margin-bottom: $spacing-sm;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
  }

  &--active {
    border-color: $color-border-dark;
    background: $color-bg-card;

    .note-card__title {
      color: $color-text-primary;
    }
  }

  &--pinned {
    border-left: 3px solid $color-accent;
  }
}

.note-card__pin {
  position: absolute;
  top: $spacing-sm;
  right: $spacing-sm;
  color: $color-accent;
}

.note-card__title {
  font-size: $font-size-md;
  font-weight: 500;
  margin-bottom: $spacing-xs;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 20px;
  color: $color-text-primary;
}

.note-card__preview {
  font-size: $font-size-sm;
  color: $color-text-secondary;
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
  color: $color-text-muted;
}

.note-card__category {
  font-size: $font-size-xs;
  padding: 2px 8px;
  border-radius: $radius-sm;
  color: white;
}
</style>
