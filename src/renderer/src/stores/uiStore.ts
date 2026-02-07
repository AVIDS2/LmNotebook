import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// 默认宽度
const DEFAULT_SIDEBAR_WIDTH = 200
const DEFAULT_NOTELIST_WIDTH = 280
const DEFAULT_AGENT_SIDEBAR_WIDTH = 460

// 宽度限制
const SIDEBAR_MIN = 160
const SIDEBAR_MAX = 300
const NOTELIST_MIN = 220
const NOTELIST_MAX = 450
const AGENT_SIDEBAR_MIN = 280
const AGENT_SIDEBAR_MAX = 620

// localStorage keys
const STORAGE_KEY_SIDEBAR = 'origin-notes-sidebar-width'
const STORAGE_KEY_NOTELIST = 'origin-notes-notelist-width'
const STORAGE_KEY_AGENT_SIDEBAR = 'origin-notes-agent-sidebar-width'
const STORAGE_KEY_THEME = 'origin-notes-theme'

export type ThemeMode = 'light' | 'classic' | 'dark'

export const useUIStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  
  // 可调整的宽度
  const sidebarWidth = ref(DEFAULT_SIDEBAR_WIDTH)
  const noteListWidth = ref(DEFAULT_NOTELIST_WIDTH)
  const agentSidebarWidth = ref(DEFAULT_AGENT_SIDEBAR_WIDTH)
  
  // 主题
  const theme = ref<ThemeMode>('light')

  // 从 localStorage 恢复状态
  function loadSavedState(): void {
    // 恢复宽度
    const savedSidebar = localStorage.getItem(STORAGE_KEY_SIDEBAR)
    const savedNoteList = localStorage.getItem(STORAGE_KEY_NOTELIST)
    const savedAgentSidebar = localStorage.getItem(STORAGE_KEY_AGENT_SIDEBAR)
    
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
    
    // 恢复主题
    const savedTheme = localStorage.getItem(STORAGE_KEY_THEME) as ThemeMode | null
    if (savedTheme === 'light' || savedTheme === 'classic' || savedTheme === 'dark') {
      theme.value = savedTheme
    }
    
    // 应用主题到 DOM
    applyTheme(theme.value)
  }

  // 应用主题到 DOM
  function applyTheme(mode: ThemeMode): void {
    document.documentElement.setAttribute('data-theme', mode)
  }

  // 保存状态到 localStorage
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

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed: boolean): void {
    sidebarCollapsed.value = collapsed
  }

  function setSidebarWidth(width: number): void {
    sidebarWidth.value = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, width))
  }

  function setNoteListWidth(width: number): void {
    noteListWidth.value = Math.max(NOTELIST_MIN, Math.min(NOTELIST_MAX, width))
  }

  function setAgentSidebarWidth(width: number): void {
    agentSidebarWidth.value = Math.max(AGENT_SIDEBAR_MIN, Math.min(AGENT_SIDEBAR_MAX, width))
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

  // 初始化时加载保存的状态
  loadSavedState()

  return {
    sidebarCollapsed,
    sidebarWidth,
    noteListWidth,
    agentSidebarWidth,
    theme,
    toggleSidebar,
    setSidebarCollapsed,
    setSidebarWidth,
    setNoteListWidth,
    setAgentSidebarWidth,
    toggleTheme,
    setTheme,
    // 导出常量供组件使用
    SIDEBAR_MIN,
    SIDEBAR_MAX,
    NOTELIST_MIN,
    NOTELIST_MAX,
    AGENT_SIDEBAR_MIN,
    AGENT_SIDEBAR_MAX
  }
})
