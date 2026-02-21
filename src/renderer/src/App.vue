<template>
  <div class="app-container" :style="{ '--agent-sidebar-width': `${uiStore.agentSidebarWidth}px` }">
    <!-- 自定义标题栏 -->
    <header class="titlebar" @dblclick="handleMaximize">
      <div class="titlebar__drag-region"></div>
      <div class="titlebar__title">{{ t('app.brand') }}</div>
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

    <main
      v-if="showStartupPage"
      class="startup-shell"
    >
      <StartupPage
        :note-count="noteStore.totalNotesCount"
        :category-count="categoryStore.categories.length"
        @create-first-note="handleCreateFirstNote"
        @import-backup="handleImportBackup"
        @open-data-directory="handleOpenDataDirectory"
      />
    </main>

    <main
      v-else
      class="main-content"
      :class="{
        'main-content--resizing': isResizing,
        'main-content--agent-sidebar': isAgentSidebarMode
      }"
    >
      <div
        class="panel panel--sidebar"
        :style="{ width: '56px' }"
      >
        <TheSidebar />
      </div>

      <div
        class="panel panel--notelist"
        :style="{ width: uiStore.noteListCollapsed ? '38px' : `${uiStore.noteListWidth}px` }"
      >
        <NoteList :collapsed="uiStore.noteListCollapsed" @toggle-collapse="uiStore.toggleNoteListCollapsed" />
        <div
          class="resizer"
          @mousedown="startResizeWithAutoExpand('notelist', $event)"
        ></div>
      </div>

      <div class="panel panel--editor">
        <NoteEditor />
      </div>
    </main>

    <div
      v-if="isAgentSidebarMode && !showStartupPage"
      class="agent-sidebar-resizer"
      @mousedown="startResize('agent', $event)"
    ></div>

    <AgentBubble v-if="!showStartupPage" />
    <ToastHost />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, provide, watch } from 'vue'
import TheSidebar from '@/components/sidebar/TheSidebar.vue'
import NoteList from '@/components/notes/NoteList.vue'
import NoteEditor from '@/components/notes/NoteEditor.vue'
import AgentBubble from '@/components/agent/AgentBubble.vue'
import ToastHost from '@/components/common/ToastHost.vue'
import StartupPage from '@/components/common/StartupPage.vue'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { useUIStore } from '@/stores/uiStore'
import { noteRepository } from '@/database/noteRepository'
import { exportService } from '@/services/exportService'
import { shouldShowStartupPage } from '@/utils/startupVisibility'
import { useI18n } from '@/i18n'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const uiStore = useUIStore()
const { t } = useI18n()
const isAgentSidebarMode = ref(localStorage.getItem('origin_agent_sidebar_mode') === '1')
const isBootstrapped = ref(false)
const showStartupPage = computed(() =>
  shouldShowStartupPage({
    isBootstrapped: isBootstrapped.value,
    totalNotesCount: noteStore.totalNotesCount,
    hasCurrentNote: !!noteStore.currentNote
  })
)
const syncAgentSidebarMode = () => {
  isAgentSidebarMode.value = localStorage.getItem('origin_agent_sidebar_mode') === '1'
}
const applyAdaptiveLayout = () => {
  uiStore.adaptLayoutForViewport(window.innerWidth, isAgentSidebarMode.value)
}
type ResizeTarget = 'sidebar' | 'notelist' | 'agent' | null
const isResizing = ref(false)
const resizeTarget = ref<ResizeTarget>(null)
const startX = ref(0)
const startWidth = ref(0)

let rafId: number | null = null
let resizeFailsafeTimer: ReturnType<typeof setTimeout> | null = null

function startResize(target: 'sidebar' | 'notelist' | 'agent', e: MouseEvent): void {
  e.preventDefault()
  isResizing.value = true
  resizeTarget.value = target
  startX.value = e.clientX

  if (target === 'sidebar') {
    startWidth.value = uiStore.sidebarWidth
  } else if (target === 'notelist') {
    startWidth.value = uiStore.noteListWidth
  } else {
    startWidth.value = uiStore.agentSidebarWidth
  }

  document.addEventListener('mousemove', handleResize, { passive: true })
  document.addEventListener('mouseup', stopResize)
  window.addEventListener('blur', stopResize)
  document.addEventListener('visibilitychange', handleVisibilityStop)
  document.addEventListener('keydown', handleResizeEscape)
  if (resizeFailsafeTimer) clearTimeout(resizeFailsafeTimer)
  resizeFailsafeTimer = setTimeout(() => {
    if (isResizing.value) stopResize()
  }, 4000)
}

function startResizeWithAutoExpand(target: 'notelist', e: MouseEvent): void {
  if (target === 'notelist' && uiStore.noteListCollapsed) {
    uiStore.setNoteListCollapsed(false)
  }
  startResize(target, e)
}

function handleResize(e: MouseEvent): void {
  if (!isResizing.value || !resizeTarget.value) return
  if (rafId) return

  rafId = requestAnimationFrame(() => {
    const delta = e.clientX - startX.value

    if (resizeTarget.value === 'sidebar') {
      uiStore.setSidebarWidth(startWidth.value + delta)
    } else if (resizeTarget.value === 'notelist') {
      uiStore.setNoteListWidth(startWidth.value + delta)
    } else {
      uiStore.setAgentSidebarWidth(startWidth.value - delta)
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
  if (resizeFailsafeTimer) {
    clearTimeout(resizeFailsafeTimer)
    resizeFailsafeTimer = null
  }
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  window.removeEventListener('blur', stopResize)
  document.removeEventListener('visibilitychange', handleVisibilityStop)
  document.removeEventListener('keydown', handleResizeEscape)
}

function handleVisibilityStop(): void {
  if (document.hidden) stopResize()
}

function handleResizeEscape(e: KeyboardEvent): void {
  if (e.key === 'Escape' && isResizing.value) {
    stopResize()
  }
}

const setEditorContentRef = { value: (_html: string) => {} }
provide('setEditorContent', (html: string) => {
  setEditorContentRef.value(html)
})
provide('registerEditorAction', (fn: (html: string) => void) => {
  setEditorContentRef.value = fn
})

function handleMinimize(): void {
  window.electronAPI?.minimizeWindow()
}

function handleMaximize(): void {
  window.electronAPI?.maximizeWindow()
}

function handleClose(): void {
  window.electronAPI?.closeWindow()
}

async function handleCreateFirstNote(): Promise<void> {
  await noteStore.createNote()
}

async function handleImportBackup(): Promise<void> {
  const result = await exportService.importBackup()
  if (result.success) {
    await categoryStore.loadCategories()
    await noteStore.initialize()
  }
}

async function handleOpenDataDirectory(): Promise<void> {
  const currentPath = await window.electronAPI.db.getDataPath()
  await window.electronAPI.shell.openPath(currentPath)
}

onMounted(async () => {
  let retryCount = 0
  while (!window.electronAPI?.db && retryCount < 50) {
    await new Promise(resolve => setTimeout(resolve, 50))
    retryCount++
  }

  if (!window.electronAPI?.db) {
    console.error('数据库服务连接超时，请检查主进程状态')
    isBootstrapped.value = true
    return
  }

  try {
    await categoryStore.loadCategories()
    await noteStore.initialize()
    isBootstrapped.value = true
  } catch (err) {
    console.error('数据加载失败:', err)
    isBootstrapped.value = true
  }

  noteRepository.cleanupOldDeleted().catch(console.error)

  window.addEventListener('origin-agent-sidebar-mode-changed', syncAgentSidebarMode as EventListener)
  window.addEventListener('storage', syncAgentSidebarMode)
  window.addEventListener('resize', applyAdaptiveLayout)
  syncAgentSidebarMode()
  if (uiStore.layoutPreset !== 'custom') {
    uiStore.applyLayoutPreset(uiStore.layoutPreset, {
      viewportWidth: window.innerWidth,
      hasAgentSidebar: isAgentSidebarMode.value
    })
  }
  applyAdaptiveLayout()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  window.removeEventListener('blur', stopResize)
  document.removeEventListener('visibilitychange', handleVisibilityStop)
  document.removeEventListener('keydown', handleResizeEscape)
  if (resizeFailsafeTimer) {
    clearTimeout(resizeFailsafeTimer)
    resizeFailsafeTimer = null
  }
  window.removeEventListener('origin-agent-sidebar-mode-changed', syncAgentSidebarMode as EventListener)
  window.removeEventListener('storage', syncAgentSidebarMode)
  window.removeEventListener('resize', applyAdaptiveLayout)
})

watch(isAgentSidebarMode, () => {
  if (uiStore.layoutPreset !== 'custom') {
    uiStore.applyLayoutPreset(uiStore.layoutPreset, {
      viewportWidth: window.innerWidth,
      hasAgentSidebar: isAgentSidebarMode.value
    })
    return
  }
  applyAdaptiveLayout()
})
</script>

<style lang="scss" scoped>
.app-container {
  --agent-sidebar-width: 460px;
  --app-titlebar-height: #{$titlebar-height};
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  background: var(--color-bg-primary);
  transition: background-color 0.3s ease;
}

.titlebar {
  display: flex;
  align-items: center;
  height: $titlebar-height;
  background: var(--color-bg-primary);
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  position: relative;
  flex-shrink: 0;
  transition: background-color 0.3s ease;

  &__drag-region {
    position: absolute;
    top: 0;
    left: 0;
    right: 126px;
    height: 100%;
    -webkit-app-region: drag;
  }

  &__title {
    margin-left: 10px;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-secondary);
    pointer-events: none;
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: 0;
    margin-left: auto;
    -webkit-app-region: no-drag;
  }

  &__utility-btn {
    width: 34px;
    height: 24px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease, transform 0.12s ease;

    &:hover {
      background: var(--color-bg-hover);
      border-color: color-mix(in srgb, var(--color-border) 54%, transparent);
      color: var(--color-text-primary);
      transform: translateY(-0.5px);
    }

    &:active {
      transform: translateY(0);
    }

    &--active {
      border-color: color-mix(in srgb, var(--color-accent) 34%, var(--color-border-light));
      color: var(--color-accent);
      background: color-mix(in srgb, var(--color-accent) 10%, transparent);
    }
  }

  &__locale-btn {
    width: 36px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  &__layout-btn {
    width: 30px;
    font-size: 11px;
    font-weight: 700;
  }

  &__btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: $titlebar-height;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    border-radius: 0;
    transition: background $transition-fast, color $transition-fast, transform 0.12s ease;

    &:hover {
      background: var(--color-bg-hover);
      transform: translateY(-0.5px);
    }

    &:active {
      transform: translateY(0);
    }

    &--close:hover {
      background: var(--color-danger);
      color: white;
    }
  }
}

.main-content {
  position: relative;
  display: flex;
  padding: 10px;
  gap: 10px;
  flex: 1;
  overflow: hidden;
  background: var(--color-bg-primary);
  transition: padding-right 0.2s ease;

  &--agent-sidebar {
    padding-right: calc(var(--agent-sidebar-width) + 10px);
  }

  &--resizing {
    cursor: col-resize;
    user-select: none;
  }
}

.startup-shell {
  flex: 1;
  overflow: hidden;
  display: flex;
  background: var(--color-bg-primary);
}

.panel {
  position: relative;
  display: flex;
  flex-shrink: 0;
  will-change: width;
  overflow: hidden;
  background: color-mix(in srgb, var(--color-bg-card) 92%, var(--color-bg-primary));
  border: 1px solid color-mix(in srgb, var(--color-border) 68%, transparent);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);

  &--sidebar {
    z-index: 2;
    width: 56px;
  }

  &--notelist {
    z-index: 1;
  }

  &--editor {
    flex: 1;
    min-width: 300px;
    box-shadow: var(--shadow-md);
  }
}

.resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 5px;
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
    background: transparent;
    transition: width 0.14s ease, background-color 0.14s ease;
  }

  &:hover::after {
    width: 1px;
    background: color-mix(in srgb, var(--color-border-dark) 72%, transparent);
  }
}

.panel :deep(> *:first-child) {
  width: 100%;
  height: 100%;
}

.agent-sidebar-resizer {
  position: fixed;
  top: var(--app-titlebar-height);
  bottom: 10px;
  right: var(--agent-sidebar-width);
  width: 6px;
  cursor: col-resize;
  z-index: 30;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 2px;
    width: 1px;
    height: 100%;
    background: transparent;
    transition: width 0.14s ease, background-color 0.14s ease;
  }

  &:hover::after {
    width: 1px;
    background: color-mix(in srgb, var(--color-border-dark) 72%, transparent);
  }
}

/* Workspace shadcn pass */
.app-container {
  :deep(.sidebar-rail) {
    padding: 10px 6px;
    border-right: none;
    background: linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-bg-secondary) 86%, white 14%),
      color-mix(in srgb, var(--color-bg-secondary) 96%, transparent)
    );
  }

  :deep(.rail-btn) {
    width: 36px;
    height: 36px;
    border-radius: 11px;
    border-color: transparent;
    color: var(--color-text-secondary);
  }

  :deep(.rail-btn:hover),
  :deep(.rail-btn--active) {
    background: color-mix(in srgb, var(--color-bg-hover) 90%, transparent);
    border-color: color-mix(in srgb, var(--color-border) 72%, transparent);
    color: var(--color-text-primary);
  }

  :deep(.rail-btn--primary) {
    border-color: color-mix(in srgb, var(--color-border-dark) 72%, transparent);
    background: color-mix(in srgb, var(--color-bg-card) 92%, transparent);
  }

  :deep(.note-list) {
    border-right: none;
    background: transparent;
  }

  :deep(.search-bar) {
    margin: 6px 8px 10px;
    height: 38px;
    border-radius: 10px;
    background: color-mix(in srgb, var(--color-bg-card) 96%, transparent);
    border: 1px solid color-mix(in srgb, var(--color-border) 66%, transparent);
    box-shadow: var(--shadow-sm);
  }

  :deep(.note-list__header) {
    min-height: 40px;
    padding: 10px 10px 6px;
  }

  :deep(.note-list__content) {
    padding: 4px 8px 10px;
  }

  :deep(.note-list__folder-filter-trigger) {
    height: 28px;
    border-radius: 9px;
    background: color-mix(in srgb, var(--color-bg-card) 94%, transparent);
  }

  :deep(.note-card) {
    margin-bottom: 4px;
    border-radius: 11px;
    border: 1px solid transparent;
    background: transparent;
  }

  :deep(.note-card:hover) {
    border-color: color-mix(in srgb, var(--color-border) 70%, transparent);
    background: color-mix(in srgb, var(--color-bg-hover) 82%, transparent);
  }

  :deep(.note-card--active) {
    border-color: color-mix(in srgb, var(--color-border-dark) 86%, transparent);
    background: color-mix(in srgb, var(--color-bg-card) 94%, transparent);
    box-shadow: var(--shadow-sm);
  }

  :deep(.note-editor) {
    background: transparent;
  }

  :deep(.note-editor__toolbar) {
    margin: 10px 10px 0;
    border: 1px solid color-mix(in srgb, var(--color-border) 66%, transparent);
    border-radius: 12px;
    background: color-mix(in srgb, var(--color-bg-card) 96%, transparent);
    box-shadow: var(--shadow-sm);
  }

  :deep(.note-editor__title-wrapper) {
    margin: 8px 14px 0;
    border-bottom: 1px dashed color-mix(in srgb, var(--color-border) 74%, transparent);
  }

  :deep(.note-editor__title) {
    font-size: clamp(24px, 2.2vw, 34px);
    font-weight: 640;
    letter-spacing: -0.02em;
    padding: 12px 6px 12px;
  }

  :deep(.note-editor__content) {
    padding: 0 16px 16px;
  }

  :deep(.note-editor .ProseMirror) {
    max-width: 920px;
    margin: 0 auto;
    padding: 14px 10px 68px;
    line-height: 1.82;
  }

  :deep(.note-editor__outline) {
    border-radius: 12px;
    border-color: color-mix(in srgb, var(--color-border) 72%, transparent);
    box-shadow: var(--shadow-md);
  }

  :deep(.agent-chat.sidebar-mode) {
    border-radius: 14px !important;
    border: 1px solid color-mix(in srgb, var(--color-border) 68%, transparent) !important;
    box-shadow: var(--shadow-md) !important;
    background: color-mix(in srgb, var(--color-bg-card) 96%, transparent) !important;
  }

  :deep(.agent-chat.sidebar-mode .agent-chat__header) {
    background: color-mix(in srgb, var(--color-bg-primary) 95%, transparent) !important;
    border-bottom: 1px solid color-mix(in srgb, var(--color-border) 62%, transparent) !important;
  }

  :deep(.agent-chat.sidebar-mode .agent-chat__messages) {
    background: transparent !important;
    padding: 12px 12px 10px !important;
  }

  :deep(.agent-chat.sidebar-mode .message--assistant .message) {
    border: none !important;
    background: transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
  }

  :deep(.agent-chat.sidebar-mode .message--assistant .message__text) {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
  }

  :deep(.agent-chat.sidebar-mode .status-update) {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
  }

  :deep(.agent-chat.sidebar-mode .message--user .message) {
    border: 1px solid color-mix(in srgb, var(--color-border-dark) 78%, transparent) !important;
    background: color-mix(in srgb, var(--color-bg-hover) 92%, transparent) !important;
    border-radius: 12px !important;
  }
}
</style>
