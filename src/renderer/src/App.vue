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
    <main class="main-content" :class="{ 'main-content--resizing': isResizing }">
      <!-- 侧边栏 -->
      <div 
        class="panel panel--sidebar"
        :style="{ width: uiStore.sidebarCollapsed ? '56px' : `${uiStore.sidebarWidth}px` }"
      >
        <TheSidebar :collapsed="uiStore.sidebarCollapsed" @toggle="uiStore.toggleSidebar" />
        <!-- 侧边栏拖拽条 -->
        <div 
          v-if="!uiStore.sidebarCollapsed"
          class="resizer"
          @mousedown="startResize('sidebar', $event)"
        ></div>
      </div>
      
      <!-- 笔记列表 -->
      <div 
        class="panel panel--notelist"
        :style="{ width: `${uiStore.noteListWidth}px` }"
      >
        <NoteList />
        <!-- 笔记列表拖拽条 -->
        <div 
          class="resizer"
          @mousedown="startResize('notelist', $event)"
        ></div>
      </div>
      
      <!-- 编辑器 -->
      <div class="panel panel--editor">
        <NoteEditor :key="noteStore.currentNote?.id || 'empty'" />
      </div>
    </main>

    <!-- AI Agent 聊天气泡 -->
    <AgentBubble />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, provide } from 'vue'
import TheSidebar from '@/components/sidebar/TheSidebar.vue'
import NoteList from '@/components/notes/NoteList.vue'
import NoteEditor from '@/components/notes/NoteEditor.vue'
import AgentBubble from '@/components/agent/AgentBubble.vue'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { useUIStore } from '@/stores/uiStore'
import { noteRepository } from '@/database/noteRepository'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const uiStore = useUIStore()

// ========== 拖拽调整宽度 ==========
type ResizeTarget = 'sidebar' | 'notelist' | null
const isResizing = ref(false)
const resizeTarget = ref<ResizeTarget>(null)
const startX = ref(0)
const startWidth = ref(0)

// 使用 RAF 节流优化拖拽性能
let rafId: number | null = null

function startResize(target: 'sidebar' | 'notelist', e: MouseEvent): void {
  e.preventDefault()
  isResizing.value = true
  resizeTarget.value = target
  startX.value = e.clientX
  startWidth.value = target === 'sidebar' ? uiStore.sidebarWidth : uiStore.noteListWidth
  
  document.addEventListener('mousemove', handleResize, { passive: true })
  document.addEventListener('mouseup', stopResize)
}

function handleResize(e: MouseEvent): void {
  if (!isResizing.value || !resizeTarget.value) return
  
  // 使用 RAF 节流，避免过度渲染
  if (rafId) return
  
  rafId = requestAnimationFrame(() => {
    const delta = e.clientX - startX.value
    const newWidth = startWidth.value + delta
    
    if (resizeTarget.value === 'sidebar') {
      uiStore.setSidebarWidth(newWidth)
    } else {
      uiStore.setNoteListWidth(newWidth)
    }
    rafId = null
  })
}

function stopResize(): void {
  isResizing.value = false
  resizeTarget.value = null
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// Shared editor action bridge
const setEditorContentRef = { value: (_html: string) => {} }
provide('setEditorContent', (html: string) => {
  setEditorContentRef.value(html)
})
provide('registerEditorAction', (fn: (html: string) => void) => {
  setEditorContentRef.value = fn
})

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
  let retryCount = 0
  while (!window.electronAPI?.db && retryCount < 50) {
    await new Promise(resolve => setTimeout(resolve, 50))
    retryCount++
  }

  if (!window.electronAPI?.db) {
    console.error('数据库服务连接超时，请检查主进程状态')
    return
  }

  try {
    await categoryStore.loadCategories()
    await noteStore.initialize()
  } catch (err) {
    console.error('数据加载失败:', err)
  }

  noteRepository.cleanupOldDeleted().catch(console.error)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style lang="scss" scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-primary);
  transition: background-color 0.3s ease;
}

.titlebar {
  display: flex;
  align-items: center;
  height: $titlebar-height;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  position: relative;
  flex-shrink: 0;
  transition: background-color 0.3s ease;

  &__drag-region {
    position: absolute;
    top: 0;
    left: 0;
    right: 140px; // 3个按钮 * 46px + 2px 余量
    height: 100%;
    -webkit-app-region: drag;
  }

  &__title {
    margin-left: $spacing-md;
    font-size: $font-size-sm;
    font-weight: 500;
    color: var(--color-text-secondary);
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
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: background $transition-fast, color $transition-fast;

    &:hover {
      background: var(--color-bg-hover);
    }

    &--close:hover {
      background: var(--color-danger);
      color: white;
    }
  }
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;

  &--resizing {
    cursor: col-resize;
    user-select: none;
    
    .panel {
      pointer-events: none;
    }
    
    .resizer {
      pointer-events: auto;
    }
  }
}

// 面板容器
.panel {
  position: relative;
  display: flex;
  flex-shrink: 0;
  // 使用 GPU 加速的 transform 代替 width 过渡
  will-change: width;
  
  &--sidebar {
    z-index: 2;
  }
  
  &--notelist {
    z-index: 1;
  }
  
  &--editor {
    flex: 1;
    min-width: 300px;
  }
}

// 拖拽分隔条
.resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  cursor: col-resize;
  z-index: 100;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 1px;
    height: 100%;
    background: var(--color-border-light);
    transition: width 0.15s ease, background-color 0.15s ease;
  }
  
  &:hover::after {
    width: 3px;
    background: var(--color-accent);
  }
}

// 子组件填满容器
.panel :deep(> *:first-child) {
  width: 100%;
  height: 100%;
}
</style>
