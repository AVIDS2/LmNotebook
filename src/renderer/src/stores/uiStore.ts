import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const DEFAULT_SIDEBAR_WIDTH = 200
const DEFAULT_NOTELIST_WIDTH = 280
const DEFAULT_AGENT_SIDEBAR_WIDTH = 460

const SIDEBAR_MIN = 160
const SIDEBAR_MAX = 300
const NOTELIST_MIN = 220
const NOTELIST_MAX = 450
const AGENT_SIDEBAR_MIN = 280
const AGENT_SIDEBAR_MAX = 620
const COLLAPSED_SIDEBAR_WIDTH = 56
const COLLAPSED_NOTELIST_WIDTH = 44
const MIN_EDITOR_WIDTH = 520

const STORAGE_KEY_SIDEBAR = 'origin-notes-sidebar-width'
const STORAGE_KEY_NOTELIST = 'origin-notes-notelist-width'
const STORAGE_KEY_AGENT_SIDEBAR = 'origin-notes-agent-sidebar-width'
const STORAGE_KEY_THEME = 'origin-notes-theme'
const STORAGE_KEY_LOCALE = 'origin-notes-locale'
const STORAGE_KEY_LAYOUT_PRESET = 'origin-notes-layout-preset'
const STORAGE_KEY_NOTELIST_COLLAPSED = 'origin-notes-notelist-collapsed'

export type ThemeMode = 'light' | 'classic' | 'dark'
export type LocaleCode = 'zh-CN' | 'en-US'
export type LayoutPreset = 'writing' | 'balanced' | 'research' | 'custom'

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(true)
  const noteListCollapsed = ref(false)
  const sidebarWidth = ref(DEFAULT_SIDEBAR_WIDTH)
  const noteListWidth = ref(DEFAULT_NOTELIST_WIDTH)
  const agentSidebarWidth = ref(DEFAULT_AGENT_SIDEBAR_WIDTH)
  const theme = ref<ThemeMode>('light')
  const locale = ref<LocaleCode>('zh-CN')
  const layoutPreset = ref<LayoutPreset>('balanced')

  const PRESET_VALUES: Record<Exclude<LayoutPreset, 'custom'>, {
    normal: { sidebarCollapsed: boolean; sidebarWidth: number; noteListWidth: number; agentSidebarWidth: number }
    agent: { sidebarCollapsed: boolean; sidebarWidth: number; noteListWidth: number; agentSidebarWidth: number }
  }> = {
    writing: {
      normal: { sidebarCollapsed: true, sidebarWidth: 180, noteListWidth: 240, agentSidebarWidth: 360 },
      agent: { sidebarCollapsed: true, sidebarWidth: 180, noteListWidth: 220, agentSidebarWidth: 340 }
    },
    balanced: {
      normal: { sidebarCollapsed: false, sidebarWidth: DEFAULT_SIDEBAR_WIDTH, noteListWidth: DEFAULT_NOTELIST_WIDTH, agentSidebarWidth: DEFAULT_AGENT_SIDEBAR_WIDTH },
      agent: { sidebarCollapsed: false, sidebarWidth: 180, noteListWidth: 240, agentSidebarWidth: 380 }
    },
    research: {
      normal: { sidebarCollapsed: false, sidebarWidth: 220, noteListWidth: 360, agentSidebarWidth: 520 },
      agent: { sidebarCollapsed: false, sidebarWidth: 190, noteListWidth: 280, agentSidebarWidth: 420 }
    }
  }

  function loadSavedState(): void {
    const savedSidebar = localStorage.getItem(STORAGE_KEY_SIDEBAR)
    const savedNoteList = localStorage.getItem(STORAGE_KEY_NOTELIST)
    const savedAgentSidebar = localStorage.getItem(STORAGE_KEY_AGENT_SIDEBAR)
    const savedNoteListCollapsed = localStorage.getItem(STORAGE_KEY_NOTELIST_COLLAPSED)

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

    const savedTheme = localStorage.getItem(STORAGE_KEY_THEME) as ThemeMode | null
    if (savedTheme === 'light' || savedTheme === 'classic' || savedTheme === 'dark') {
      theme.value = savedTheme
    }

    const savedLocale = localStorage.getItem(STORAGE_KEY_LOCALE) as LocaleCode | null
    if (savedLocale === 'zh-CN' || savedLocale === 'en-US') {
      locale.value = savedLocale
    }

    const savedLayoutPreset = localStorage.getItem(STORAGE_KEY_LAYOUT_PRESET) as LayoutPreset | null
    if (savedLayoutPreset === 'writing' || savedLayoutPreset === 'balanced' || savedLayoutPreset === 'research' || savedLayoutPreset === 'custom') {
      layoutPreset.value = savedLayoutPreset
      if (savedLayoutPreset !== 'custom') {
        const preset = PRESET_VALUES[savedLayoutPreset].normal
        sidebarCollapsed.value = preset.sidebarCollapsed
      }
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

  function adaptLayoutForViewport(viewportWidth: number, hasAgentSidebar: boolean): void {
    if (viewportWidth <= 0) return

    const leftWidth = sidebarCollapsed.value ? COLLAPSED_SIDEBAR_WIDTH : sidebarWidth.value
    const listWidth = noteListCollapsed.value ? COLLAPSED_NOTELIST_WIDTH : noteListWidth.value
    const agentWidth = hasAgentSidebar ? agentSidebarWidth.value : 0
    const maxReserved = Math.max(0, viewportWidth - MIN_EDITOR_WIDTH)
    let overflow = leftWidth + listWidth + agentWidth - maxReserved

    if (overflow <= 0) return

    if (!noteListCollapsed.value) {
      const reducible = noteListWidth.value - NOTELIST_MIN
      const reduce = Math.min(reducible, overflow)
      if (reduce > 0) {
        setNoteListWidth(noteListWidth.value - reduce, { preservePreset: true })
        overflow -= reduce
      }
    }

    if (overflow > 0 && !sidebarCollapsed.value) {
      const reducible = sidebarWidth.value - SIDEBAR_MIN
      const reduce = Math.min(reducible, overflow)
      if (reduce > 0) {
        setSidebarWidth(sidebarWidth.value - reduce, { preservePreset: true })
        overflow -= reduce
      }
    }

    if (overflow > 0 && hasAgentSidebar) {
      const reducible = agentSidebarWidth.value - AGENT_SIDEBAR_MIN
      const reduce = Math.min(reducible, overflow)
      if (reduce > 0) {
        setAgentSidebarWidth(agentSidebarWidth.value - reduce, { preservePreset: true })
        overflow -= reduce
      }
    }

    if (overflow > 0 && !noteListCollapsed.value) {
      noteListCollapsed.value = true
      overflow -= Math.max(0, noteListWidth.value - COLLAPSED_NOTELIST_WIDTH)
    }

    if (overflow > 0 && !sidebarCollapsed.value) {
      sidebarCollapsed.value = true
      overflow -= Math.max(0, sidebarWidth.value - COLLAPSED_SIDEBAR_WIDTH)
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
      adaptLayoutForViewport(context.viewportWidth, Boolean(context?.hasAgentSidebar))
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
    sidebarWidth,
    noteListWidth,
    agentSidebarWidth,
    theme,
    locale,
    layoutPreset,
    toggleSidebar,
    toggleNoteListCollapsed,
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
