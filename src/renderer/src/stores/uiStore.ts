import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const DEFAULT_SIDEBAR_WIDTH = 176
const DEFAULT_NOTELIST_WIDTH = 252
const DEFAULT_AGENT_SIDEBAR_WIDTH = 430

const SIDEBAR_MIN = 132
const SIDEBAR_MAX = 300
const NOTELIST_MIN = 188
const NOTELIST_MAX = 450
const AGENT_SIDEBAR_MIN = 280
const AGENT_SIDEBAR_MAX = 620
const COLLAPSED_SIDEBAR_WIDTH = 44
const COLLAPSED_NOTELIST_WIDTH = 32

const STORAGE_KEY_SIDEBAR = 'lmnotebook-sidebar-width'
const STORAGE_KEY_NOTELIST = 'lmnotebook-notelist-width'
const STORAGE_KEY_AGENT_SIDEBAR = 'lmnotebook-agent-sidebar-width'
const STORAGE_KEY_THEME = 'lmnotebook-theme'
const STORAGE_KEY_LOCALE = 'lmnotebook-locale'
const STORAGE_KEY_LAYOUT_PRESET = 'lmnotebook-layout-preset'
const STORAGE_KEY_NOTELIST_COLLAPSED = 'lmnotebook-notelist-collapsed'
const STORAGE_KEY_NOTELIST_LAYER_MODE = 'lmnotebook-notelist-layer-mode'
const STORAGE_KEY_UI_VERSION = 'lmnotebook-ui-version'
const LEGACY_STORAGE_KEY_SIDEBAR = 'origin-notes-sidebar-width'
const LEGACY_STORAGE_KEY_NOTELIST = 'origin-notes-notelist-width'
const LEGACY_STORAGE_KEY_AGENT_SIDEBAR = 'origin-notes-agent-sidebar-width'
const LEGACY_STORAGE_KEY_THEME = 'origin-notes-theme'
const LEGACY_STORAGE_KEY_LOCALE = 'origin-notes-locale'
const LEGACY_STORAGE_KEY_LAYOUT_PRESET = 'origin-notes-layout-preset'
const LEGACY_STORAGE_KEY_NOTELIST_COLLAPSED = 'origin-notes-notelist-collapsed'
const LEGACY_STORAGE_KEY_NOTELIST_LAYER_MODE = 'origin-notes-notelist-layer-mode'
const LEGACY_STORAGE_KEY_UI_VERSION = 'origin-notes-ui-version'
const UI_VERSION = 'ob-rebuild-v3'

export type ThemeMode = 'light' | 'classic' | 'dark'
export type LocaleCode = 'zh-CN' | 'en-US'
export type LayoutPreset = 'writing' | 'balanced' | 'research' | 'custom'
export type NoteListViewMode = 'compact'
export type NoteListLayerMode = 'none' | 'category'

type LayoutConstraint = {
  minEditorWidth: number
  minSidebarWidth: number
  minNoteListWidth: number
  minAgentSidebarWidth: number
}

type LayoutPanel = 'sidebar' | 'noteList' | 'agent'

type LayoutAdaptPolicy = {
  reduceOrder: LayoutPanel[]
  collapseOrder: Array<'sidebar' | 'noteList'>
}

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(true)
  const noteListCollapsed = ref(false)
  const sidebarWidth = ref(DEFAULT_SIDEBAR_WIDTH)
  const noteListWidth = ref(DEFAULT_NOTELIST_WIDTH)
  const agentSidebarWidth = ref(DEFAULT_AGENT_SIDEBAR_WIDTH)
  const theme = ref<ThemeMode>('light')
  const locale = ref<LocaleCode>('zh-CN')
  const layoutPreset = ref<LayoutPreset>('balanced')
  const noteListViewMode = ref<NoteListViewMode>('compact')
  const noteListLayerMode = ref<NoteListLayerMode>('none')

  const PRESET_VALUES: Record<Exclude<LayoutPreset, 'custom'>, {
    normal: { sidebarCollapsed: boolean; sidebarWidth: number; noteListWidth: number; agentSidebarWidth: number }
    agent: { sidebarCollapsed: boolean; sidebarWidth: number; noteListWidth: number; agentSidebarWidth: number }
  }> = {
    writing: {
      normal: { sidebarCollapsed: true, sidebarWidth: 156, noteListWidth: 214, agentSidebarWidth: 340 },
      agent: { sidebarCollapsed: true, sidebarWidth: 156, noteListWidth: 198, agentSidebarWidth: 320 }
    },
    balanced: {
      normal: { sidebarCollapsed: false, sidebarWidth: DEFAULT_SIDEBAR_WIDTH, noteListWidth: DEFAULT_NOTELIST_WIDTH, agentSidebarWidth: DEFAULT_AGENT_SIDEBAR_WIDTH },
      agent: { sidebarCollapsed: false, sidebarWidth: 160, noteListWidth: 220, agentSidebarWidth: 360 }
    },
    research: {
      normal: { sidebarCollapsed: false, sidebarWidth: 186, noteListWidth: 294, agentSidebarWidth: 470 },
      agent: { sidebarCollapsed: false, sidebarWidth: 168, noteListWidth: 246, agentSidebarWidth: 390 }
    }
  }

  const PRESET_CONSTRAINTS: Record<LayoutPreset, LayoutConstraint> = {
    writing: {
      minEditorWidth: 620,
      minSidebarWidth: COLLAPSED_SIDEBAR_WIDTH,
      minNoteListWidth: NOTELIST_MIN,
      minAgentSidebarWidth: 300
    },
    balanced: {
      minEditorWidth: 560,
      minSidebarWidth: SIDEBAR_MIN,
      minNoteListWidth: NOTELIST_MIN,
      minAgentSidebarWidth: 310
    },
    research: {
      minEditorWidth: 420,
      minSidebarWidth: SIDEBAR_MIN,
      minNoteListWidth: 250,
      minAgentSidebarWidth: 360
    },
    custom: {
      minEditorWidth: 520,
      minSidebarWidth: SIDEBAR_MIN,
      minNoteListWidth: NOTELIST_MIN,
      minAgentSidebarWidth: AGENT_SIDEBAR_MIN
    }
  }

  const PRESET_ADAPT_POLICY: Record<LayoutPreset, LayoutAdaptPolicy> = {
    writing: {
      reduceOrder: ['noteList', 'sidebar', 'agent'],
      collapseOrder: ['noteList', 'sidebar']
    },
    balanced: {
      reduceOrder: ['noteList', 'sidebar', 'agent'],
      collapseOrder: ['noteList', 'sidebar']
    },
    research: {
      reduceOrder: ['sidebar', 'noteList', 'agent'],
      collapseOrder: ['sidebar', 'noteList']
    },
    custom: {
      reduceOrder: ['noteList', 'sidebar', 'agent'],
      collapseOrder: ['noteList', 'sidebar']
    }
  }

  function getStoredValue(primaryKey: string, legacyKey?: string): string | null {
    const value = localStorage.getItem(primaryKey)
    if (value !== null) return value
    return legacyKey ? localStorage.getItem(legacyKey) : null
  }

  function loadSavedState(): void {
    const savedUIVersion = getStoredValue(STORAGE_KEY_UI_VERSION, LEGACY_STORAGE_KEY_UI_VERSION)
    const shouldMigrateUI = savedUIVersion !== UI_VERSION
    if (shouldMigrateUI) {
      // One-time visual migration for redesigned shell density.
      localStorage.removeItem(STORAGE_KEY_SIDEBAR)
      localStorage.removeItem(LEGACY_STORAGE_KEY_SIDEBAR)
      localStorage.removeItem(STORAGE_KEY_NOTELIST)
      localStorage.removeItem(LEGACY_STORAGE_KEY_NOTELIST)
      localStorage.removeItem(STORAGE_KEY_LAYOUT_PRESET)
      localStorage.removeItem(LEGACY_STORAGE_KEY_LAYOUT_PRESET)
      localStorage.removeItem(STORAGE_KEY_NOTELIST_LAYER_MODE)
      localStorage.removeItem(LEGACY_STORAGE_KEY_NOTELIST_LAYER_MODE)
    }

    const savedSidebar = getStoredValue(STORAGE_KEY_SIDEBAR, LEGACY_STORAGE_KEY_SIDEBAR)
    const savedNoteList = getStoredValue(STORAGE_KEY_NOTELIST, LEGACY_STORAGE_KEY_NOTELIST)
    const savedAgentSidebar = getStoredValue(STORAGE_KEY_AGENT_SIDEBAR, LEGACY_STORAGE_KEY_AGENT_SIDEBAR)
    const savedNoteListCollapsed = getStoredValue(STORAGE_KEY_NOTELIST_COLLAPSED, LEGACY_STORAGE_KEY_NOTELIST_COLLAPSED)
    const savedNoteListLayerMode = getStoredValue(STORAGE_KEY_NOTELIST_LAYER_MODE, LEGACY_STORAGE_KEY_NOTELIST_LAYER_MODE) as NoteListLayerMode | null

    if (savedSidebar) {
      const width = parseInt(savedSidebar, 10)
      if (!isNaN(width) && width >= SIDEBAR_MIN && width <= SIDEBAR_MAX) {
        sidebarWidth.value = width
      }
    }

    if (savedNoteList) {
      const width = parseInt(savedNoteList, 10)
      if (!isNaN(width) && width >= NOTELIST_MIN && width <= NOTELIST_MAX) {
        noteListWidth.value = width
      }
    }

    if (savedAgentSidebar) {
      const width = parseInt(savedAgentSidebar, 10)
      if (!isNaN(width) && width >= AGENT_SIDEBAR_MIN && width <= AGENT_SIDEBAR_MAX) {
        agentSidebarWidth.value = width
      }
    }

    if (savedNoteListCollapsed === '1') {
      noteListCollapsed.value = true
    } else if (savedNoteListCollapsed === '0') {
      noteListCollapsed.value = false
    }

    noteListViewMode.value = 'compact'
    if (savedNoteListLayerMode === 'none' || savedNoteListLayerMode === 'category') {
      noteListLayerMode.value = savedNoteListLayerMode
    }

    const savedTheme = getStoredValue(STORAGE_KEY_THEME, LEGACY_STORAGE_KEY_THEME) as ThemeMode | null
    if (savedTheme === 'light' || savedTheme === 'classic' || savedTheme === 'dark') {
      theme.value = savedTheme
    }

    const savedLocale = getStoredValue(STORAGE_KEY_LOCALE, LEGACY_STORAGE_KEY_LOCALE) as LocaleCode | null
    if (savedLocale === 'zh-CN' || savedLocale === 'en-US') {
      locale.value = savedLocale
    }

    const savedLayoutPreset = getStoredValue(STORAGE_KEY_LAYOUT_PRESET, LEGACY_STORAGE_KEY_LAYOUT_PRESET) as LayoutPreset | null
    if (savedLayoutPreset === 'writing' || savedLayoutPreset === 'balanced' || savedLayoutPreset === 'research' || savedLayoutPreset === 'custom') {
      layoutPreset.value = savedLayoutPreset
      if (savedLayoutPreset !== 'custom') {
        const preset = PRESET_VALUES[savedLayoutPreset].normal
        sidebarCollapsed.value = preset.sidebarCollapsed
      }
    }

    if (shouldMigrateUI) {
      layoutPreset.value = 'balanced'
      sidebarCollapsed.value = false
      noteListCollapsed.value = false
      noteListLayerMode.value = 'none'
      localStorage.setItem(STORAGE_KEY_UI_VERSION, UI_VERSION)
    }

    applyTheme(theme.value)
  }

  function applyTheme(mode: ThemeMode): void {
    document.documentElement.setAttribute('data-theme', mode)
  }

  watch(sidebarWidth, (width) => {
    localStorage.setItem(STORAGE_KEY_SIDEBAR, String(width))
  })

  watch(noteListWidth, (width) => {
    localStorage.setItem(STORAGE_KEY_NOTELIST, String(width))
  })

  watch(agentSidebarWidth, (width) => {
    localStorage.setItem(STORAGE_KEY_AGENT_SIDEBAR, String(width))
  })

  watch(theme, (mode) => {
    localStorage.setItem(STORAGE_KEY_THEME, mode)
    applyTheme(mode)
  })

  watch(locale, (value) => {
    localStorage.setItem(STORAGE_KEY_LOCALE, value)
  })

  watch(layoutPreset, (value) => {
    localStorage.setItem(STORAGE_KEY_LAYOUT_PRESET, value)
  })

  watch(noteListCollapsed, (value) => {
    localStorage.setItem(STORAGE_KEY_NOTELIST_COLLAPSED, value ? '1' : '0')
  })

  watch(noteListLayerMode, (value) => {
    localStorage.setItem(STORAGE_KEY_NOTELIST_LAYER_MODE, value)
  })

  function markLayoutCustom(): void {
    if (layoutPreset.value !== 'custom') {
      layoutPreset.value = 'custom'
    }
  }

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
    markLayoutCustom()
  }

  function toggleNoteListCollapsed(): void {
    noteListCollapsed.value = !noteListCollapsed.value
    markLayoutCustom()
  }

  function setNoteListCollapsed(collapsed: boolean): void {
    noteListCollapsed.value = collapsed
  }

  function toggleNoteListViewMode(): void {
    noteListViewMode.value = 'compact'
  }

  function setNoteListViewMode(_mode: NoteListViewMode): void {
    noteListViewMode.value = 'compact'
  }

  function toggleNoteListLayerMode(): void {
    noteListLayerMode.value = noteListLayerMode.value === 'none' ? 'category' : 'none'
  }

  function setNoteListLayerMode(mode: NoteListLayerMode): void {
    noteListLayerMode.value = mode
  }

  function setSidebarCollapsed(collapsed: boolean): void {
    sidebarCollapsed.value = collapsed
  }

  function setSidebarWidth(width: number, options?: { preservePreset?: boolean }): void {
    sidebarWidth.value = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, width))
    if (!options?.preservePreset) markLayoutCustom()
  }

  function setNoteListWidth(width: number, options?: { preservePreset?: boolean }): void {
    noteListWidth.value = Math.max(NOTELIST_MIN, Math.min(NOTELIST_MAX, width))
    if (!options?.preservePreset) markLayoutCustom()
  }

  function setAgentSidebarWidth(width: number, options?: { preservePreset?: boolean }): void {
    agentSidebarWidth.value = Math.max(AGENT_SIDEBAR_MIN, Math.min(AGENT_SIDEBAR_MAX, width))
    if (!options?.preservePreset) markLayoutCustom()
  }

  function adaptLayoutForViewport(
    viewportWidth: number,
    hasAgentSidebar: boolean,
    presetHint?: LayoutPreset
  ): void {
    if (viewportWidth <= 0) return
    const activePreset = presetHint || layoutPreset.value
    const constraint = PRESET_CONSTRAINTS[activePreset]
    const policy = PRESET_ADAPT_POLICY[activePreset]

    const leftWidth = sidebarCollapsed.value ? COLLAPSED_SIDEBAR_WIDTH : sidebarWidth.value
    const listWidth = noteListCollapsed.value ? COLLAPSED_NOTELIST_WIDTH : noteListWidth.value
    const agentWidth = hasAgentSidebar ? agentSidebarWidth.value : 0
    const maxReserved = Math.max(0, viewportWidth - constraint.minEditorWidth)
    let overflow = leftWidth + listWidth + agentWidth - maxReserved

    if (overflow <= 0) return

    for (const panel of policy.reduceOrder) {
      if (overflow <= 0) break
      if (panel === 'noteList' && !noteListCollapsed.value) {
        const reducible = noteListWidth.value - constraint.minNoteListWidth
        const reduce = Math.min(reducible, overflow)
        if (reduce > 0) {
          setNoteListWidth(noteListWidth.value - reduce, { preservePreset: true })
          overflow -= reduce
        }
      }
      if (panel === 'sidebar' && !sidebarCollapsed.value) {
        const reducible = sidebarWidth.value - constraint.minSidebarWidth
        const reduce = Math.min(reducible, overflow)
        if (reduce > 0) {
          setSidebarWidth(sidebarWidth.value - reduce, { preservePreset: true })
          overflow -= reduce
        }
      }
      if (panel === 'agent' && hasAgentSidebar) {
        const reducible = agentSidebarWidth.value - constraint.minAgentSidebarWidth
        const reduce = Math.min(reducible, overflow)
        if (reduce > 0) {
          setAgentSidebarWidth(agentSidebarWidth.value - reduce, { preservePreset: true })
          overflow -= reduce
        }
      }
    }

    for (const panel of policy.collapseOrder) {
      if (overflow <= 0) break
      if (panel === 'noteList' && !noteListCollapsed.value) {
        noteListCollapsed.value = true
        overflow -= Math.max(0, noteListWidth.value - COLLAPSED_NOTELIST_WIDTH)
      }
      if (panel === 'sidebar' && !sidebarCollapsed.value) {
        sidebarCollapsed.value = true
        overflow -= Math.max(0, sidebarWidth.value - COLLAPSED_SIDEBAR_WIDTH)
      }
    }
  }

  function applyLayoutPreset(
    preset: Exclude<LayoutPreset, 'custom'>,
    context?: { viewportWidth?: number; hasAgentSidebar?: boolean }
  ): void {
    const profile = context?.hasAgentSidebar ? 'agent' : 'normal'
    const value = PRESET_VALUES[preset][profile]
    sidebarCollapsed.value = value.sidebarCollapsed
    noteListCollapsed.value = false
    setSidebarWidth(value.sidebarWidth, { preservePreset: true })
    setNoteListWidth(value.noteListWidth, { preservePreset: true })
    setAgentSidebarWidth(value.agentSidebarWidth, { preservePreset: true })
    if (typeof context?.viewportWidth === 'number') {
      adaptLayoutForViewport(context.viewportWidth, Boolean(context?.hasAgentSidebar), preset)
    }
    layoutPreset.value = preset
  }

  function cycleLayoutPreset(context?: { viewportWidth?: number; hasAgentSidebar?: boolean }): void {
    const ordered: Exclude<LayoutPreset, 'custom'>[] = ['writing', 'balanced', 'research']
    const currentIndex = ordered.indexOf(layoutPreset.value as Exclude<LayoutPreset, 'custom'>)
    const next = currentIndex === -1 ? 'balanced' : ordered[(currentIndex + 1) % ordered.length]
    applyLayoutPreset(next, context)
  }

  function toggleTheme(): void {
    if (theme.value === 'light') {
      theme.value = 'classic'
      return
    }
    if (theme.value === 'classic') {
      theme.value = 'dark'
      return
    }
    theme.value = 'light'
  }

  function setTheme(mode: ThemeMode): void {
    theme.value = mode
  }

  function setLocale(next: LocaleCode): void {
    locale.value = next
  }

  function toggleLocale(): void {
    locale.value = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  }

  loadSavedState()

  return {
    sidebarCollapsed,
    noteListCollapsed,
    noteListViewMode,
    noteListLayerMode,
    sidebarWidth,
    noteListWidth,
    agentSidebarWidth,
    theme,
    locale,
    layoutPreset,
    toggleSidebar,
    toggleNoteListCollapsed,
    toggleNoteListViewMode,
    toggleNoteListLayerMode,
    setNoteListViewMode,
    setNoteListLayerMode,
    setNoteListCollapsed,
    setSidebarCollapsed,
    setSidebarWidth,
    setNoteListWidth,
    setAgentSidebarWidth,
    adaptLayoutForViewport,
    applyLayoutPreset,
    cycleLayoutPreset,
    toggleTheme,
    setTheme,
    setLocale,
    toggleLocale,
    SIDEBAR_MIN,
    SIDEBAR_MAX,
    NOTELIST_MIN,
    NOTELIST_MAX,
    AGENT_SIDEBAR_MIN,
    AGENT_SIDEBAR_MAX
  }
})
