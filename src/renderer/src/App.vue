<template>
  <div class="app-container" :style="{ '--agent-sidebar-width': `${uiStore.agentSidebarWidth}px` }">
    <!-- 自定义标题栏 -->
    <header class="titlebar" @dblclick="handleMaximize">
      <div class="titlebar__drag-region"></div>
      <div class="titlebar__title">Origin Notes</div>
      <div class="titlebar__controls">
        <button
          class="titlebar__utility-btn"
          @click.stop="forceShowStartup = !forceShowStartup"
          :title="forceShowStartup ? t('app.exitStartupPreview') : t('app.previewStartup')"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </button>
        <button
          class="titlebar__utility-btn titlebar__layout-btn"
          @click.stop="handleCycleLayoutPreset"
          :title="t('app.layout.cycleTitle')"
        >
          {{ layoutPresetLabel }}
        </button>
        <button
          class="titlebar__utility-btn titlebar__locale-btn"
          @click.stop="toggleLocale"
          :title="t('language.toggleTitle')"
        >
          {{ locale === 'zh-CN' ? 'EN' : '中' }}
        </button>
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
        :style="{ width: uiStore.sidebarCollapsed ? '56px' : `${uiStore.sidebarWidth}px` }"
      >
        <TheSidebar :collapsed="uiStore.sidebarCollapsed" @toggle="uiStore.toggleSidebar" />
        <div
          v-if="!uiStore.sidebarCollapsed"
          class="resizer"
          @mousedown="startResize('sidebar', $event)"
        ></div>
      </div>

      <div
        class="panel panel--notelist"
        :style="{ width: uiStore.noteListCollapsed ? '44px' : `${uiStore.noteListWidth}px` }"
      >
        <NoteList :collapsed="uiStore.noteListCollapsed" @toggle-collapse="uiStore.toggleNoteListCollapsed" />
        <div
          v-if="!uiStore.noteListCollapsed"
          class="resizer"
          @mousedown="startResize('notelist', $event)"
        ></div>
      </div>

      <div class="panel panel--editor">
        <NoteEditor :key="noteStore.currentNote?.id || 'empty'" />
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
import { useI18n } from '@/i18n'
import { shouldShowStartupPage } from '@/utils/startupVisibility'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const uiStore = useUIStore()
const { t, locale, toggleLocale } = useI18n()
const layoutPresetLabel = computed(() => {
  if (locale.value === 'zh-CN') {
    if (uiStore.layoutPreset === 'writing') return '写'
    if (uiStore.layoutPreset === 'balanced') return '衡'
    if (uiStore.layoutPreset === 'research') return '研'
    return '自'
  }
  if (uiStore.layoutPreset === 'writing') return 'W'
  if (uiStore.layoutPreset === 'balanced') return 'B'
  if (uiStore.layoutPreset === 'research') return 'R'
  return 'C'
})
const isAgentSidebarMode = ref(localStorage.getItem('origin_agent_sidebar_mode') === '1')
const isBootstrapped = ref(false)
const forceShowStartup = ref(false)
const showStartupPage = computed(() =>
  shouldShowStartupPage({
    isBootstrapped: isBootstrapped.value,
    totalNotesCount: noteStore.totalNotesCount,
    hasCurrentNote: !!noteStore.currentNote,
    forceShow: forceShowStartup.value
  })
)
const syncAgentSidebarMode = () => {
  isAgentSidebarMode.value = localStorage.getItem('origin_agent_sidebar_mode') === '1'
}
const applyAdaptiveLayout = () => {
  uiStore.adaptLayoutForViewport(window.innerWidth, isAgentSidebarMode.value)
}
const handleCycleLayoutPreset = () => {
  uiStore.cycleLayoutPreset({
    viewportWidth: window.innerWidth,
    hasAgentSidebar: isAgentSidebarMode.value
  })
}

type ResizeTarget = 'sidebar' | 'notelist' | 'agent' | null
const isResizing = ref(false)
const resizeTarget = ref<ResizeTarget>(null)
const startX = ref(0)
const startWidth = ref(0)

let rafId: number | null = null

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
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
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
  forceShowStartup.value = false
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
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  position: relative;
  flex-shrink: 0;
  transition: background-color 0.3s ease;

  &__drag-region {
    position: absolute;
    top: 0;
    left: 0;
    right: 220px;
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
    align-items: center;
    gap: 4px;
    margin-left: auto;
    -webkit-app-region: no-drag;
  }

  &__utility-btn {
    width: 30px;
    height: 24px;
    border: 1px solid var(--color-border-light);
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.16s ease, border-color 0.16s ease;

    &:hover {
      background: var(--color-bg-hover);
      border-color: var(--color-border);
    }
  }

  &__locale-btn {
    width: 34px;
    font-size: 11px;
    font-weight: 700;
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
  position: relative;
  display: flex;
  flex: 1;
  overflow: hidden;
  transition: padding-right 0.2s ease;

  &--agent-sidebar {
    padding-right: var(--agent-sidebar-width);
  }

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

.startup-shell {
  flex: 1;
  overflow: auto;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-bg-primary) 90%, #000 10%) 0%, var(--color-bg-primary) 100%);
}

.panel {
  position: relative;
  display: flex;
  flex-shrink: 0;
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

.panel :deep(> *:first-child) {
  width: 100%;
  height: 100%;
}

.agent-sidebar-resizer {
  position: fixed;
  top: var(--app-titlebar-height);
  bottom: 0;
  right: var(--agent-sidebar-width);
  width: 6px;
  cursor: col-resize;
  z-index: 10050;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 2px;
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
</style>
