<template>
  <div class="app-container">
    <!-- 自定义标题栏 -->
    <header class="titlebar" @dblclick="handleMaximize">
      <div class="titlebar__drag-region"></div>
      <div class="titlebar__title">Origin Notes</div>
      <div class="titlebar__controls">
        <button class="titlebar__btn" @click="handleMinimize">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <rect x="1" y="5.5" width="10" height="1" fill="currentColor"/>
          </svg>
        </button>
        <button class="titlebar__btn" @click="handleMaximize">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <rect x="1.5" y="1.5" width="9" height="9" fill="none" stroke="currentColor" stroke-width="1"/>
          </svg>
        </button>
        <button class="titlebar__btn titlebar__btn--close" @click="handleClose">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" stroke-width="1.2"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <TheSidebar :collapsed="uiStore.sidebarCollapsed" @toggle="uiStore.toggleSidebar" />
      <NoteList />
      <NoteEditor />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import TheSidebar from '@/components/sidebar/TheSidebar.vue'
import NoteList from '@/components/notes/NoteList.vue'
import NoteEditor from '@/components/notes/NoteEditor.vue'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { useUIStore } from '@/stores/uiStore'
import { initializeDatabase } from '@/database'
import { noteRepository } from '@/database/noteRepository'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const uiStore = useUIStore()

// 窗口控制
function handleMinimize(): void {
  window.electronAPI?.minimizeWindow()
}

function handleMaximize(): void {
  window.electronAPI?.maximizeWindow()
}

function handleClose(): void {
  window.electronAPI?.closeWindow()
}

// 初始化
onMounted(async () => {
  await initializeDatabase()
  await categoryStore.loadCategories()
  await noteStore.initialize()

  // 清理过期的已删除笔记
  await noteRepository.cleanupOldDeleted()
})
</script>

<style lang="scss" scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $color-bg-primary;
}

.titlebar {
  display: flex;
  align-items: center;
  height: $titlebar-height;
  background: $color-bg-secondary;
  border-bottom: 1px solid $color-border-light;
  position: relative;

  &__drag-region {
    position: absolute;
    top: 0;
    left: 0;
    right: 100px;
    height: 100%;
    -webkit-app-region: drag;
  }

  &__title {
    margin-left: $spacing-md;
    font-size: $font-size-sm;
    font-weight: 500;
    color: $color-text-secondary;
    pointer-events: none;
  }

  &__controls {
    display: flex;
    margin-left: auto;
    -webkit-app-region: no-drag;
  }

  &__btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 46px;
    height: $titlebar-height;
    border: none;
    background: transparent;
    color: $color-text-secondary;
    cursor: pointer;
    transition: background $transition-fast;

    &:hover {
      background: $color-bg-hover;
    }

    &--close:hover {
      background: $color-danger;
      color: white;
    }
  }
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}
</style>
