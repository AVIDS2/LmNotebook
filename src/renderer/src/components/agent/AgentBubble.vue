<template>
  <!-- Main Container with dynamic position -->
  <div 
    class="agent-container" 
    :style="containerStyle"
    :class="{ 'is-dragging': isDragging, 'is-docked': isDocked && !isOpen }"
  >
    <!-- Floating Bubble Button -->
    <div
      class="agent-bubble glass-panel"
      :class="{ 'agent-bubble--active': isOpen }"
      @mousedown="startDrag"
      @click.stop="handleClick"
    >
      <div class="agent-bubble__icon">
        <!-- Origin asterisk logo -->
        <svg v-if="!isOpen" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L13.09 8.26L18 4L14.74 9.91L21 10.91L14.74 12.09L18 18L13.09 13.74L12 20L10.91 13.74L6 18L9.26 12.09L3 10.91L9.26 9.91L6 4L10.91 8.26L12 2Z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </div>
      <div v-if="hasUnread" class="agent-bubble__badge"></div>
    </div>

    <!-- Chat Window -->
    <Transition name="chat-window">
      <div 
        v-if="isOpen" 
        class="agent-chat glass-panel" 
        :class="{ 
          'maximized': isMaximized,
          'align-left': position.x < windowWidth / 2 
        }"
        @mousedown.stop
      >
        <!-- Header -->
        <div class="agent-chat__header">
          <div class="agent-chat__title" @mousedown="startDrag" style="cursor: grab;">
            <span class="agent-chat__avatar">✦</span>
            <span>Origin Agent</span>
          </div>
          <div class="agent-chat__actions">
            <button 
              class="header-btn" 
              @click="showModelSettings = true; console.log('Settings toggle')" 
              title="模型设置"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="toggleSessionHistory" title="历史对话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="clearChat" title="开始新对话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="isMaximized = !isMaximized" :title="isMaximized ? '还原' : '最大化'">
              <svg v-if="!isMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="5" y="5" width="14" height="14" rx="2"/>
                <path d="M9 3h10a2 2 0 0 1 2 2v10"/>
              </svg>
            </button>
            <div class="agent-chat__status">
              <span v-if="isConnected" class="status-dot status-dot--online"></span>
              <span v-else class="status-dot status-dot--offline"></span>
            </div>
          </div>
        </div>

        <!-- Session History Panel -->
        <Transition name="slide-panel">
          <div v-if="showSessionHistory" class="session-history-panel">
            <div class="session-history__header">
              <span>历史对话</span>
              <button class="close-btn" @click="showSessionHistory = false">×</button>
            </div>
            <div class="session-history__list">
              <div v-if="sessionList.length === 0" class="session-history__empty">
                暂无历史对话
              </div>
              <div 
                v-for="session in sessionList" 
                :key="session.id"
                class="session-item"
                :class="{ 'session-item--active': session.id === currentSessionId, 'session-item--pinned': session.pinned }"
                @click="editingSessionId !== session.id && loadSession(session.id)"
              >
                <!-- Normal display mode -->
                <div v-if="editingSessionId !== session.id" class="session-item__preview">
                  <span v-if="session.pinned" class="pin-indicator">
                    <svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="12" height="12">
                      <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
                    </svg>
                  </span>
                  {{ session.preview }}
                </div>
                <!-- Editing mode -->
                <input 
                  v-else
                  v-model="editingTitle"
                  class="session-rename-input"
                  @click.stop
                  @keyup.enter="confirmRename(session.id)"
                  @keyup.escape="cancelRename"
                  @blur="confirmRename(session.id)"
                />
                <div v-if="editingSessionId !== session.id" class="session-item__actions">
                  <button class="session-item__btn" @click.stop="togglePinSession(session.id)" :title="session.pinned ? '取消置顶' : '置顶'">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
                    </svg>
                  </button>
                  <button class="session-item__btn" @click.stop="renameSession(session.id)" title="重命名">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="session-item__btn session-item__btn--danger" @click.stop="deleteSession(session.id)" title="删除">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Messages -->
        <div class="agent-chat__messages" ref="messagesContainer" @scroll="handleMessagesScroll">
          <div v-if="messages.length === 0" class="agent-chat__empty">
            <div class="agent-chat__welcome">
              <span class="welcome-icon">✦</span>
              <h3>Hello, explorer</h3>
              <p>我是 Origin，你的笔记助手。</p>
            </div>
            <div class="agent-chat__suggestions">
              <button
                v-for="suggestion in suggestions"
                :key="suggestion"
                class="suggestion-chip"
                @click="handleSuggestionClick(suggestion)"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>

          <div
            v-for="(msg, index) in messages.filter(m => m.content.trim() || (m.parts && m.parts.length))"
            :key="index"
            class="message-wrapper"
            :class="[`message--${msg.role}`]">
            <div class="message">
              <div class="message__avatar">
                {{ msg.role === 'user' ? '◉' : '✦' }}
              </div>
              <div class="message__content">
                <!-- Part-Based Rendering -->
                <template v-if="msg.parts && msg.parts.length">
                  <template v-for="(part, partIndex) in msg.parts" :key="partIndex">
                    <!-- Text Part -->
                    <div v-if="part.type === 'text'" 
                         class="message__text" 
                         v-html="renderMarkdown(part.content)"
                         @contextmenu="handleContextMenu($event, part.content)"></div>
                    
                    <!-- Tool Part -->
                    <div v-else-if="part.type === 'tool'" 
                         class="tool-part"
                         :class="[`tool-part--${part.status}`]">
                      <span class="tool-part__icon">{{ getToolIcon(part.tool) }}</span>
                      <span class="tool-part__name">{{ part.title || part.tool }}</span>
                      <span v-if="part.status === 'running'" class="tool-part__spinner"></span>
                      <span v-else-if="part.status === 'completed'" class="tool-part__check">✓</span>
                      <span v-if="part.output && part.status === 'completed'" class="tool-part__output">{{ part.output }}</span>
                    </div>
                  </template>
                </template>
                
                <!-- Fallback: Legacy content rendering -->
                <template v-else>
                  <div class="message__text" 
                       v-html="renderMarkdown(msg.content)"
                       @contextmenu="handleContextMenu($event, msg.content)"></div>
                </template>
              </div>
            </div>
          </div>

          <div v-if="currentStatus" class="status-update">
            <span class="status-update__text">{{ currentStatus }}</span>
            <span class="status-update__dots">...</span>
          </div>

          <div v-if="isTyping && !currentStatus" class="typing-minimal">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- Scroll to bottom button -->
        <Transition name="fade">
          <button 
            v-if="showScrollToBottom" 
            class="scroll-to-bottom-btn"
            @click="forceScrollToBottom"
            title="滚动到底部"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </Transition>

        <!-- Context Bar (Automatic & Explicit) -->
        <div class="agent-chat__context-bar">
          <!-- 1. Automatic: Current Active Note -->
          <div v-if="noteStore.currentNote" class="context-pill inspecting-pill" :class="{ 'inactive': !includeActiveNote }">
            <button class="pill-toggle-btn" @click="includeActiveNote = !includeActiveNote" title="切换上下文包含">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="eye-svg">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
                <line v-if="!includeActiveNote" x1="1" y1="1" x2="23" y2="23" stroke-width="3" />
              </svg>
            </button>
            <span class="pill-text">{{ noteStore.currentNote.title || '无标题' }}</span>
          </div>

          <!-- 2. Explicit: Manually selected @ note -->
          <div v-if="selectedContextNote" class="context-pill mentioned-pill">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="pill-svg">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span class="pill-text">{{ selectedContextNote.title }}</span>
            <button class="pill-clear" @click="clearContextNote">×</button>
          </div>
        </div>

        <!-- Compact Input Area -->
        <div class="agent-chat__footer">
          <div class="chat-input-unified-box">
            <!-- + Menu Button -->
            <div class="input-menu-wrapper">
              <button 
                class="menu-trigger-btn" 
                @click="showInputMenu = !showInputMenu"
                :class="{ 'active': showInputMenu }"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
              
              <!-- Popup Menu (Smaller) -->
              <Transition name="menu-fade">
                <div v-if="showInputMenu" class="input-menu-popup shallow-glass">
                  <div class="menu-item" @click="triggerKnowledgeSearch">
                    <span class="menu-icon">@</span>
                    <span class="menu-label">笔记知识库</span>
                  </div>
                  <div class="menu-item" @click="toggleNoteSelector">
                    <span class="menu-icon smaller">📎</span>
                    <span class="menu-label">添加笔记上下文</span>
                  </div>
                </div>
              </Transition>
              
              <!-- Note Selector (triggered from menu) -->
              <Transition name="menu-fade">
                <div v-if="showNoteSelector" class="note-selector-dropdown shallow-glass" ref="selectorRef">
                  <div class="selector-header">选择笔记</div>
                  <div class="selector-list">
                    <div 
                      v-for="note in noteStore.notes" 
                      :key="note.id" 
                      class="selector-item"
                      @click="selectNoteAsContext(note)"
                    >
                      <span class="item-icon">📄</span>
                      <span class="item-title">{{ note.title || '无标题' }}</span>
                    </div>
                    <div v-if="noteStore.notes.length === 0" class="selector-empty">暂无笔记</div>
                  </div>
                </div>
              </Transition>
            </div>

            <!-- Auto-resize Textarea (Background transparent to inherit container) -->
            <textarea
              v-model="inputText"
              @keydown.enter.exact.prevent="sendMessage()"
              @input="autoResizeInput"
              placeholder="输入消息..."
              rows="1"
              ref="inputRef"
            ></textarea>

            <!-- Compact Send Button -->
            <button
              v-if="!isTyping"
              class="send-btn-compact"
              :disabled="!inputText.trim()"
              @click="sendMessage()"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
            <button
              v-else
              class="stop-btn-compact"
              @click="stopGeneration"
            >
              <div class="stop-icon-small"></div>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Model Settings Modal -->
    <Teleport to="body">
      <ModelSettings 
        v-if="showModelSettings" 
        :backend-url="BACKEND_URL" 
        @close="() => { console.log('Closing settings'); showModelSettings = false; }"
        @updated="checkConnection"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, watch, inject, computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useNoteStore } from '@/stores/noteStore'
import { noteRepository } from '@/database/noteRepository'
import ModelSettings from './ModelSettings.vue'

// Inject dependencies

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  parts?: MessagePart[]  // Part-Based: for structured rendering
  timestamp: Date
  isError?: boolean
}

// Part-Based Message Types (OpenCode-style)
interface TextPart {
  type: 'text'
  content: string
}

interface ToolPart {
  type: 'tool'
  tool: string
  toolId?: string  // For precise status matching
  status: 'running' | 'completed' | 'error'
  title?: string
  output?: string
  inputPreview?: string
}

type MessagePart = TextPart | ToolPart

const STATUS_MAP = {
  THINKING: '思考中...',
  SEARCHING: '搜索知识库...',
  WRITING: '正在撰写...',
  ERROR: '出错了'
}

// Stores
const noteStore = useNoteStore()
const setEditorContent = inject<(html: string) => void>('setEditorContent')

// Config
const BACKEND_URL = 'http://127.0.0.1:8765'

// State
const isOpen = ref(false)
const isConnected = ref(false)
const isTyping = ref(false)
const hasUnread = ref(false)
const inputText = ref('')
const messages = ref<ChatMessage[]>([])
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const isMaximized = ref(false)
const showModelSettings = ref(false)
const streamingMessage = ref<ChatMessage | null>(null)
const currentStatus = ref('')
const abortController = ref<AbortController | null>(null)
const includeActiveNote = ref(true)

// --- Auto-scroll control ---
const userScrolledUp = ref(false)
const showScrollToBottom = ref(false)

// --- Context (@) Selection ---
const showNoteSelector = ref(false)
const selectedContextNote = ref<any>(null)
const selectorRef = ref<HTMLElement | null>(null)

// --- Session History ---
interface SessionInfo {
  id: string
  preview: string
  title?: string
  pinned?: boolean
  updated_at?: string
}
const showSessionHistory = ref(false)
const sessionList = ref<SessionInfo[]>([])

// Session metadata stored locally (pinned status, custom titles)
const sessionMeta = ref<Record<string, { pinned?: boolean; title?: string }>>({})

// Load session metadata from localStorage
function loadSessionMeta() {
  try {
    const stored = localStorage.getItem('agent_session_meta')
    if (stored) sessionMeta.value = JSON.parse(stored)
  } catch { sessionMeta.value = {} }
}

// Save session metadata to localStorage
function saveSessionMeta() {
  localStorage.setItem('agent_session_meta', JSON.stringify(sessionMeta.value))
}

async function toggleSessionHistory() {
  showSessionHistory.value = !showSessionHistory.value
  if (showSessionHistory.value) {
    loadSessionMeta()
    await loadSessionList()
  }
}

async function loadSessionList() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions`)
    if (response.ok) {
      const data = await response.json()
      // Merge with local metadata (pinned, custom title)
      const sessions = (data.sessions || []).map((s: SessionInfo) => {
        const meta = sessionMeta.value[s.id] || {}
        return {
          ...s,
          preview: meta.title || s.preview,
          pinned: meta.pinned || false
        }
      })
      // Sort: pinned first, then by updated_at
      sessions.sort((a: SessionInfo, b: SessionInfo) => {
        if (a.pinned && !b.pinned) return -1
        if (!a.pinned && b.pinned) return 1
        return 0
      })
      sessionList.value = sessions
    }
  } catch (e) {
    console.error('Failed to load sessions:', e)
  }
}

// Toggle pin status
function togglePinSession(sessionId: string) {
  if (!sessionMeta.value[sessionId]) {
    sessionMeta.value[sessionId] = {}
  }
  sessionMeta.value[sessionId].pinned = !sessionMeta.value[sessionId].pinned
  saveSessionMeta()
  // Update list
  const session = sessionList.value.find(s => s.id === sessionId)
  if (session) {
    session.pinned = sessionMeta.value[sessionId].pinned
    // Re-sort
    sessionList.value.sort((a, b) => {
      if (a.pinned && !b.pinned) return -1
      if (!a.pinned && b.pinned) return 1
      return 0
    })
  }
}

// Rename session - inline editing
const editingSessionId = ref<string | null>(null)
const editingTitle = ref('')

function renameSession(sessionId: string) {
  const session = sessionList.value.find(s => s.id === sessionId)
  if (!session) return
  
  editingSessionId.value = sessionId
  editingTitle.value = session.preview
  
  // Focus input after render
  nextTick(() => {
    const input = document.querySelector('.session-rename-input') as HTMLInputElement
    if (input) {
      input.focus()
      input.select()
    }
  })
}

function confirmRename(sessionId: string) {
  if (editingTitle.value.trim()) {
    if (!sessionMeta.value[sessionId]) {
      sessionMeta.value[sessionId] = {}
    }
    sessionMeta.value[sessionId].title = editingTitle.value.trim()
    saveSessionMeta()
    
    const session = sessionList.value.find(s => s.id === sessionId)
    if (session) {
      session.preview = editingTitle.value.trim()
    }
  }
  editingSessionId.value = null
  editingTitle.value = ''
}

function cancelRename() {
  editingSessionId.value = null
  editingTitle.value = ''
}

async function loadSession(sessionId: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions/${sessionId}/messages`)
    if (response.ok) {
      const data = await response.json()
      // Switch to this session
      currentSessionId.value = sessionId
      localStorage.setItem(SESSION_KEY, sessionId)
      // Load messages
      messages.value = (data.messages || []).map((m: any) => ({
        role: m.role,
        content: m.content,
        timestamp: new Date()
      }))
      showSessionHistory.value = false
      nextTick(() => scrollToBottom())
    }
  } catch (e) {
    console.error('Failed to load session:', e)
  }
}

async function deleteSession(sessionId: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      sessionList.value = sessionList.value.filter(s => s.id !== sessionId)
      // If deleted current session, start new one
      if (sessionId === currentSessionId.value) {
        clearChat()
      }
    }
  } catch (e) {
    console.error('Failed to delete session:', e)
  }
}

// --- New: Input Menu & Knowledge Search ---
const showInputMenu = ref(false)

function toggleNoteSelector() {
  showInputMenu.value = false  // Close menu first
  showNoteSelector.value = !showNoteSelector.value
  if (showNoteSelector.value) {
    noteStore.loadNotes()
  }
}

function triggerKnowledgeSearch() {
  const triggerText = "@笔记知识库 "
  if (!inputText.value.includes(triggerText)) {
    inputText.value = triggerText + inputText.value
  }
  showInputMenu.value = false
  nextTick(() => {
    inputRef.value?.focus()
    // Trigger height adjust
    if (inputRef.value) {
      autoResizeInput({ target: inputRef.value } as any)
    }
  })
}

function selectNoteAsContext(note: any) {
  selectedContextNote.value = note
  showNoteSelector.value = false
}

function clearContextNote() {
  selectedContextNote.value = null
}

// Auto-resize input
function autoResizeInput(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 100) + 'px'
}

// Reset textarea height when chat window opens
watch(isOpen, (newVal) => {
  if (newVal) {
    // Reset textarea height when window opens
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.style.height = 'auto'
      }
    })
  }
})

// Close menus when clicking outside
function handleGlobalClick(e: MouseEvent) {
  const menuWrapper = document.querySelector('.input-menu-wrapper')
  if (menuWrapper && !menuWrapper.contains(e.target as Node)) {
    showInputMenu.value = false
    showNoteSelector.value = false
  }
}

// --- Draggable Logic ---
const position = ref({ x: window.innerWidth - 40, y: window.innerHeight - 100 })
const isDragging = ref(false)
const isDocked = ref(true)
const dragOffset = ref({ x: 0, y: 0 })
const windowWidth = ref(window.innerWidth)

const containerStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`,
  transition: isDragging.value ? 'none' : 'all 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28)'
}))

function startDrag(e: MouseEvent) {
  if (isMaximized.value) return
  isDragging.value = true
  isDocked.value = false
  dragOffset.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  position.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  snapToEdge()
}

function snapToEdge() {
  const BUBBLE_SIZE = 50
  const screenW = window.innerWidth
  const screenH = window.innerHeight
  
  // Keep vertical within bounds
  if (position.value.y < 0) position.value.y = 10
  if (position.value.y > screenH - BUBBLE_SIZE) position.value.y = screenH - BUBBLE_SIZE - 10
  
  // Snap horizontal to nearest edge
  if (position.value.x > screenW / 2) {
    // Right Edge - Dock half way
    position.value.x = screenW - (BUBBLE_SIZE / 2)
  } else {
    // Left Edge - Dock half way
    position.value.x = -(BUBBLE_SIZE / 2)
  }
  isDocked.value = true
}

// Click handler (distinguish drag from click)
function handleClick() {
  if (!isDragging.value) {
    // If docked, pop out a bit
    if (isDocked.value && !isOpen.value) {
      const BUBBLE_SIZE = 50
      if (position.value.x < 0) position.value.x = 20
      else position.value.x = window.innerWidth - BUBBLE_SIZE - 20
      isDocked.value = false
    }
    toggleChat()
    
    // If closing, dock back? Maybe let user dock manually or auto dock after delay.
    // For now, let's auto-dock if closed
    if (!isOpen.value) {
       setTimeout(() => {
         if (!isOpen.value && !isDragging.value) snapToEdge()
       }, 500)
    }
  }
}

// Initial Position setup
// Handle window resize - keep bubble within visible bounds
const handleResize = () => {
  const oldWidth = windowWidth.value
  const newWidth = window.innerWidth
  const oldHeight = window.innerHeight // approximate
  
  // Update stored width
  windowWidth.value = newWidth
  
  const BUBBLE_SIZE = 50
  const screenH = window.innerHeight
  
  // Calculate distance from right edge BEFORE update
  const distanceFromRight = oldWidth - position.value.x
  
  // sticky horizontal: favor the side it was closer to
  if (position.value.x > oldWidth / 2) {
    // Right side: Keep same distance from right edge
    position.value.x = newWidth - distanceFromRight
  } else {
    // Left side: Keep same distance from left edge (position.x stays same)
    // But verify it doesn't stay off-screen if it was docked
    // Actually, if it was -25, it stays -25. That's fine.
  }

  // Safety clamps (in case of extreme resize or rounding)
  // 1. Right bound
  if (position.value.x > newWidth - BUBBLE_SIZE / 2) {
     position.value.x = newWidth - BUBBLE_SIZE / 2
  }
  // 2. Left bound
  if (position.value.x < -BUBBLE_SIZE / 2) {
     position.value.x = -BUBBLE_SIZE / 2
  }
  
  // Constrain Y position
  if (position.value.y > screenH - BUBBLE_SIZE) {
    position.value.y = screenH - BUBBLE_SIZE - 10
  }
  if (position.value.y < 0) {
    position.value.y = 10
  }
}

// Initial Position setup
onMounted(() => {
  checkConnection(true) // Start checks with "isStartup = true"
  setInterval(() => checkConnection(false), 30000) // Regular heartbeat
  
  window.addEventListener('resize', handleResize)
  document.addEventListener('mousedown', handleGlobalClick)
  setTimeout(snapToEdge, 100) // Initial dock
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('mousedown', handleGlobalClick)
})
// ----------------------

const suggestions = [
  '@笔记知识库 查找关于...',
  '帮我写一篇关于...的笔记',
  '总结一下这篇笔记的要点'
]

// Tool icon mapping for Part-Based rendering (minimal text icons, no emoji)
const TOOL_ICONS: Record<string, string> = {
  'search_knowledge': '◎',
  'read_note_content': '◉',
  'list_recent_notes': '◎',
  'update_note': '✎',
  'create_note': '+',
  'delete_note': '×',
  'list_categories': '◎',
  'set_note_category': '▸',
}

function getToolIcon(tool: string): string {
  return TOOL_ICONS[tool] || '▸'
}

function toggleChat() {
  isOpen.value = !isOpen.value
  hasUnread.value = false
  
  if (isOpen.value) {
    nextTick(() => {
      inputRef.value?.focus()
      checkConnection()
    })
  }
}

function clearChat() {
  messages.value = []
  isTyping.value = false
  currentStatus.value = ''
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  
  // Fix: Force New Session on Clear
  console.log('[Agent] User cleared chat. Rotating Session ID.')
  currentSessionId.value = crypto.randomUUID()
  localStorage.setItem('origin_agent_session_id', currentSessionId.value)
  
  inputRef.value?.focus()
}

const retryCount = ref(0)
const maxRetries = 30 // Wait up to 30s for startup

async function checkConnection(isStartup = false) {
  try {
    const response = await fetch(`${BACKEND_URL}/health`)
    isConnected.value = response.ok
    if (isConnected.value) {
        retryCount.value = 0 // Reset on success
    }
  } catch {
    isConnected.value = false
  }

  // Startup Intelligence: If starting up and failed, retry quickly
  if (isStartup && !isConnected.value && retryCount.value < maxRetries) {
    retryCount.value++
    setTimeout(() => checkConnection(true), 1000)
  }
}


// Fix: Reactive Session to prevent Context Locking
const SESSION_KEY = 'origin_agent_session_id'
// Initialize session ID (create if missing)
if (!localStorage.getItem(SESSION_KEY)) {
    localStorage.setItem(SESSION_KEY, crypto.randomUUID())
}
const currentSessionId = ref(localStorage.getItem(SESSION_KEY)!)

// Watch active note change to reset session
watch(() => noteStore.currentNote?.id, (newId, oldId) => {
    // Only reset if ID actually changed (and isn't just initializing to same value)
    if (newId !== oldId) {
        console.log(`[Agent] Note switched (${oldId} -> ${newId}). Rotating Session ID.`)
        currentSessionId.value = crypto.randomUUID()
        localStorage.setItem(SESSION_KEY, currentSessionId.value)
        // Optional: Insert a system divider in UI?
        // messages.value.push({ role: 'assistant', content: '*(New Context Loaded)*', timestamp: new Date() })
    }
})

// Handle suggestion chip click - fill input if contains "...", otherwise send directly
function handleSuggestionClick(suggestion: string) {
  if (suggestion.includes('...')) {
    // Fill input box and let user complete it
    inputText.value = suggestion
    // Focus the input
    nextTick(() => {
      const input = document.querySelector('.agent-chat__input') as HTMLTextAreaElement
      if (input) {
        input.focus()
        // Place cursor at the "..." position
        const dotIndex = suggestion.indexOf('...')
        if (dotIndex !== -1) {
          input.setSelectionRange(dotIndex, dotIndex + 3)
        }
      }
    })
  } else {
    // Send directly
    sendMessage(suggestion)
  }
}

async function sendMessage(text?: string) {
  const messageText = text || inputText.value.trim()
  if (!messageText || isTyping.value) return
  
  // Optimistic UI update
  messages.value.push({ role: 'user', content: messageText, timestamp: new Date() })
  // Clear state
  inputText.value = ''
  isTyping.value = true
  showInputMenu.value = false
  showNoteSelector.value = false
  
  // Reset scroll state - user sending message means they want to see the response
  userScrolledUp.value = false
  showScrollToBottom.value = false
  
  // Reset height
  if (inputRef.value) {
    inputRef.value.style.height = '24px' // Explicitly set to min-height
    nextTick(() => {
        if (inputRef.value) inputRef.value.style.height = '' // Then let CSS take over
    })
  }
  
  currentStatus.value = STATUS_MAP.THINKING
  
  // Ensure keyboard on mobile doesn't hide input
  nextTick(() => {
    scrollToBottom(true)
  })

  // Check connection before sending (Deep Check)
  if (!isConnected.value) {
     // Try one last ping
     try {
       const res = await fetch(`${BACKEND_URL}/health`)
       if (res.ok) isConnected.value = true
     } catch {}
     
     if (!isConnected.value) {
        messages.value.push({ 
            role: 'assistant', 
            content: '❌ 无法连接到 AI 服务。请确保后台服务 (Port 8765) 正在运行。',
            isError: true,
            timestamp: new Date()
        })
        isTyping.value = false
        currentStatus.value = ''
        return
     }
  }
  
  
  
  abortController.value = new AbortController()
  
  // Don't add assistant message yet - wait for first chunk
  // This prevents the "empty bubble" flash
  let assistantMessageIndex = -1
  
  try {
    const noteContext = includeActiveNote.value ? getCurrentNoteContext() : ""
    const activeNoteId = includeActiveNote.value ? (noteStore.currentNote?.id || null) : null
    
    // Detection for knowledge search in text
    const kbTrigger = "@笔记知识库 "
    let finalMessage = messageText
    let explicitKnowledge = false
    
    if (messageText.startsWith(kbTrigger)) {
      explicitKnowledge = true
      finalMessage = messageText.substring(kbTrigger.length).trim()
    }

    // Note: We no longer send full history. Backend manages state via session_id.
    const payload: any = {
      message: finalMessage,
      session_id: currentSessionId.value,
      history: [], // Deprecated client-side history
      note_context: noteContext,
      active_note_id: activeNoteId,
      use_knowledge: explicitKnowledge  // @ knowledge search flag
    }

    // Add context info if selected
    if (selectedContextNote.value) {
      payload.context_note_id = selectedContextNote.value.id
      payload.context_note_title = selectedContextNote.value.title
    } else if (noteStore.currentNote && includeActiveNote.value) {
      // If no context explicitly selected, fallback to current note if applicable
      payload.current_note_id = noteStore.currentNote.id
      payload.active_note_title = noteStore.currentNote.title
    }

    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: abortController.value.signal,
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) throw new Error('请求失败')
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')
    const decoder = new TextDecoder()
    let buffer = ''
    
    // We'll create the assistant message on the first chunk
    let messageIndex = -1
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // SSE events are delimited by double newline
      const parts = buffer.split('\n\n')
      // The last part is either empty (if events ended perfectly) or a partial event
      buffer = parts.pop() || ''
      
      for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          
          const rawData = line.substring(6).trim() // Remove 'data: '
          if (rawData === '[DONE]') continue
          
          try {
              const chunk = JSON.parse(rawData)
              console.log('[SSE] Parsed chunk:', chunk.type || chunk.tool_call || (chunk.text ? 'text' : 'unknown'))
              
              // 1. Status Update
              if (chunk.type === 'status') {
                  currentStatus.value = chunk.text
              } 
              // NEW: Part-Based Events
              else if (chunk.part_type) {
                  console.log('[SSE] Part event:', chunk.part_type)
                  
                  // Ensure message exists
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                      currentStatus.value = ''
                  }
                  
                  const msg = messages.value[messageIndex]
                  if (!msg.parts) msg.parts = []
                  
                  if (chunk.part_type === 'text') {
                      // Find or create text part at the end
                      const lastPart = msg.parts[msg.parts.length - 1]
                      if (lastPart && lastPart.type === 'text') {
                          // Append to existing text part
                          lastPart.content += chunk.delta
                      } else {
                          // Create new text part
                          msg.parts.push({ type: 'text', content: chunk.delta })
                      }
                      // Also update legacy content for compatibility
                      msg.content += chunk.delta
                  } 
                  else if (chunk.part_type === 'tool') {
                      if (chunk.status === 'running') {
                          // Add new tool part with toolId
                          msg.parts.push({
                              type: 'tool',
                              tool: chunk.tool,
                              toolId: chunk.tool_id,
                              status: 'running',
                              title: chunk.title,
                              inputPreview: chunk.input_preview
                          } as ToolPart)
                      } 
                      else if (chunk.status === 'completed') {
                          // Update existing tool part to completed - prefer matching by toolId
                          let toolPart: ToolPart | undefined
                          if (chunk.tool_id) {
                              toolPart = [...msg.parts].reverse().find(
                                  p => p.type === 'tool' && (p as ToolPart).toolId === chunk.tool_id
                              ) as ToolPart | undefined
                          }
                          // Fallback: match by tool name + running status
                          if (!toolPart) {
                              toolPart = [...msg.parts].reverse().find(
                                  p => p.type === 'tool' && (p as ToolPart).tool === chunk.tool && (p as ToolPart).status === 'running'
                              ) as ToolPart | undefined
                          }
                          if (toolPart) {
                              toolPart.status = 'completed'
                              toolPart.output = chunk.output
                          }
                      }
                  }
                  
                  messages.value = [...messages.value]
                  scrollToBottom()
              }
              // 2. Legacy Tool Call (for actions like note_created)
              else if (chunk.tool_call) {
                  // Ensure bubble exists
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                  }
                  // Wrap in separate try-catch to not block text processing
                  try {
                      await handleToolCallEvent(chunk, messages.value[messageIndex])
                  } catch (toolErr) {
                      console.warn('[SSE] Tool event handling failed (non-blocking):', toolErr)
                  }
              } 
              // 3. Legacy Text Content (fallback)
              else if (chunk.text) {
                  console.log('[SSE] Legacy text chunk:', chunk.text.substring(0, 20))
                  // Normal text
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                      
                      // Clear status
                      currentStatus.value = ''
                  }
                  
                  if (currentStatus.value) currentStatus.value = ''
                  
                  messages.value[messageIndex].content += chunk.text
                  messages.value = [...messages.value]
                  scrollToBottom()
              }
              // 4. Error
              else if (chunk.error) {
                   if (messageIndex === -1) {
                      messages.value.push({ role: 'assistant', content: '', parts: [], timestamp: new Date(), isError: true })
                      messageIndex = messages.value.length - 1
                   }
                   messages.value[messageIndex].content += `❌ ${chunk.error}`
              }
          } catch (e) {
              console.warn("Failed to parse SSE JSON:", rawData, e)
          }
      }
    }
    
    // Guard against no message created (edge case)
    if (messageIndex === -1) {
      messages.value.push({ role: 'assistant', content: '*(No response received)*', timestamp: new Date() })
      messageIndex = messages.value.length - 1
    }
    
    const finalMsg = messages.value[messageIndex]
    
    // Improved Tool-Call Detection: Check for JSON embedded anywhere in the message
    // or if the message is purely a JSON tool call.
    const trimmedContent = finalMsg.content.trim()
    let toolData = null
    
    // Case 1: Pure JSON
    if (trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) {
      try { toolData = JSON.parse(trimmedContent) } catch (e) {}
    } 
    // Case 2: Embedded JSON (happens in multi-task scenarios)
    else {
      const jsonMatch = trimmedContent.match(/\{"tool_call":.*\}/s)
      if (jsonMatch) {
        try { 
          toolData = JSON.parse(jsonMatch[0])
          // Remove the raw JSON from the displayed text
          finalMsg.content = finalMsg.content.replace(jsonMatch[0], '').trim()
        } catch (e) {}
      }
    }

    if (toolData) {
      try {
        const data = toolData
        if (data.tool_call === 'note_created') {
          await noteStore.loadNotes()
          if (data.note_id) {
            const newNote = await noteRepository.getById(data.note_id)
            if (newNote) noteStore.currentNote = newNote
          }
          finalMsg.content = data.message || `✅ 已成功创建笔记！`
        } else if (data.tool_call === 'note_updated') {
          await noteStore.loadNotes()
          finalMsg.content = data.message || '✅ 笔记已更新！'
        } else if (data.tool_call === 'note_deleted') {
          await noteStore.loadNotes()
          finalMsg.content = data.message || '🗑️ 笔记已移至回收站。'
        } else if ((data.tool_call === 'format_apply' || data.tool_call === 'note_updated') && data.formatted_html && setEditorContent) {
          const renderedHtml = await marked.parse(data.formatted_html, { async: true, breaks: true, gfm: true })
          setEditorContent(renderedHtml)
          finalMsg.content = finalMsg.content || data.message || '✨ 笔记同步完成。'
        } else if (data.tool_call === 'note_summarized') {
          finalMsg.content = data.message || data.content
        }
        messages.value = [...messages.value]
      } catch (e) {
        console.error('Tool execution error:', e)
      }
    }
    
    if (!isOpen.value) hasUnread.value = true
  } catch (error: any) {
    if (error.name === 'AbortError') {
      if (streamingMessage.value) streamingMessage.value.content += ' \n\n*(已由用户停止生成)*'
    } else {
      if (streamingMessage.value) streamingMessage.value.content = '❌ 无法连接到 AI 服务。请确保后台服务 (Port 8765) 正在运行。'
    }
    // Mark all running tools as completed/aborted on error
    finalizeRunningTools(streamingMessage.value)
  } finally {
    // Always finalize any remaining running tools
    finalizeRunningTools(streamingMessage.value)
    
    isTyping.value = false
    streamingMessage.value = null
    currentStatus.value = ''
    abortController.value = null
    scrollToBottom()
  }
}

// Helper: Mark all "running" tool parts as completed when stream ends
function finalizeRunningTools(msg: ChatMessage | null) {
  if (!msg || !msg.parts) return
  let changed = false
  for (const part of msg.parts) {
    if (part.type === 'tool' && (part as ToolPart).status === 'running') {
      (part as ToolPart).status = 'completed'
      changed = true
    }
  }
  if (changed) {
    messages.value = [...messages.value]
  }
}

async function handleToolCallEvent(data: any, msg: any) {
  try {
    if (data.tool_call === 'note_created') {
      await noteStore.loadNotes()
      if (data.note_id) {
        const newNote = await noteRepository.getById(data.note_id)
        if (newNote) noteStore.currentNote = newNote
      }
      // Only append log if there's already content (don't start with log)
      if (msg.content) {
        msg.content += `\n\n> [SYSTEM_LOG] Created Note ID: ${data.note_id}`
      }
    } else if (data.tool_call === 'note_updated') {
      await noteStore.loadNotes()
      
      // Fix: Real-time update for active note
      if (data.note_id && noteStore.currentNote?.id === data.note_id) {
          const fresh = await noteRepository.getById(data.note_id)
          if (fresh && setEditorContent) {
              setEditorContent(fresh.content)
              noteStore.currentNote = fresh
          }
      }

      // Only append log if there's already content
      if (msg.content) {
        msg.content += `\n\n> [SYSTEM_LOG] Updated Note`
      }
    } else if (data.tool_call === 'note_deleted') {
      try {
        await noteStore.loadNotes()
      } catch (e) {
        // Fallback: Remove from local state if DB refresh fails
        console.warn('[Agent] noteStore.loadNotes() failed, using local removal fallback')
        if (data.note_id && noteStore.notes) {
          noteStore.notes = noteStore.notes.filter((n: any) => n.id !== data.note_id)
          // Clear current note if it was deleted
          if (noteStore.currentNote?.id === data.note_id) {
            noteStore.currentNote = noteStore.notes[0] || null
          }
        }
      }
      if (msg.content) {
        msg.content += `\n\n> [SYSTEM_LOG] Deleted Note ID: ${data.note_id}`
      }
    } else if (data.tool_call === 'note_categorized') {
      await noteStore.loadNotes()
      if (msg.content) {
        msg.content += `\n\n> [SYSTEM_LOG] Categorized Note ${data.note_id} as '${data.category_id}'`
      }
    } else if (data.tool_call === 'note_renamed') {
      // Refresh note list to show new title
      await noteStore.loadNotes()
      // Also refresh current note to update title in editor header
      if (noteStore.currentNote?.id) {
        const fresh = await noteRepository.getById(noteStore.currentNote.id)
        if (fresh) noteStore.currentNote = fresh
      }
      if (msg.content) {
        msg.content += `\n\n> [SYSTEM_LOG] Renamed Note`
      }
    } else if ((data.tool_call === 'format_apply' || data.tool_call === 'note_updated') && data.formatted_html && setEditorContent) {
      // Fix: 'breaks: false' to prevent double spacing (newlines becoming <br>)
      // Ideally, the editor should handle markdown block spacing naturally.
      const renderedHtml = await marked.parse(data.formatted_html, { async: true, breaks: false, gfm: true })
      setEditorContent(renderedHtml)
      // Silent sync, no change to msg.content
    } else if (data.tool_call === 'note_summarized') {
      msg.content = data.message || data.content
    }
    messages.value = [...messages.value]
  } catch (e) {
    console.error('Real-time tool execution error:', e)
  }
}

function stopGeneration() {
  if (abortController.value) abortController.value.abort()
}

function getCurrentNoteContext(): string | null {
  try {
    const editor = document.querySelector('.tiptap.ProseMirror') as any
    if (editor && editor._tiptap) return editor._tiptap.getHTML()
    const editorContent = document.querySelector('.ProseMirror')?.innerHTML
    return editorContent || null
  } catch { return null }
}

function scrollToBottom(force = false) {
  nextTick(() => {
    if (messagesContainer.value) {
      // Only auto-scroll if user hasn't scrolled up, or if forced
      if (force || !userScrolledUp.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        userScrolledUp.value = false
        showScrollToBottom.value = false
      }
    }
  })
}

// Handle user scroll to detect if they scrolled up
function handleMessagesScroll() {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
  
  if (isAtBottom) {
    userScrolledUp.value = false
    showScrollToBottom.value = false
  } else {
    userScrolledUp.value = true
    showScrollToBottom.value = true
  }
}

// Force scroll to bottom (for button click)
function forceScrollToBottom() {
  userScrolledUp.value = false
  showScrollToBottom.value = false
  scrollToBottom(true)
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  
  // Hide system logs from UI but keep them in history for AI context
  const displayContent = text.split(/\n\n> \[SYSTEM_LOG\]/)[0]
  
  try {
    const mathBlocks: string[] = []
    const mathInlines: string[] = []

    // 1. Double escape certain math chars and protect blocks
    let tmp = displayContent
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, f) => {
        mathBlocks.push(f)
        return `__MATH_BLOCK_${mathBlocks.length - 1}__`
      })
      .replace(/\$([^\$\n]+?)\$/g, (_, f) => {
        mathInlines.push(f)
        return `__MATH_INLINE_${mathInlines.length - 1}__`
      })

    // 2. Render Markdown
    const renderer = new marked.Renderer()
    
    // 🔗 Enterprise Link Handling: Force open in external browser
    // Updated for marked v17+ compatibility
    renderer.link = (token) => {
      const href = token.href || ''
      const title = token.title || ''
      const text = token.text || ''
      const cleanHref = href.replace(/&amp;/g, '&')
      return `<a href="${cleanHref}" title="${title}" target="_blank" rel="noopener noreferrer">${text}</a>`
    }

    renderer.code = (token) => {
      const { text, lang } = token
      const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
      const highlighted = hljs.highlight(text, { language }).value
      return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`
    }
    
    let html = marked.parse(tmp, { renderer, async: false, breaks: true, gfm: true }) as string

    // Helper to decode entities
    const decodeEntities = (s: string) => s
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/<br\s*\/?>/gi, '\n')

    // 3. Restore and render KaTeX
    html = html.replace(/__MATH_BLOCK_(\d+)__/g, (_, i) => {
      try {
        const raw = decodeEntities(mathBlocks[parseInt(i)])
        return `<div class="math-block">${katex.renderToString(raw, { displayMode: true, throwOnError: false })}</div>`
      } catch (e) { return `<div class="math-error">$$${mathBlocks[parseInt(i)]}$$</div>` }
    })

    html = html.replace(/__MATH_INLINE_(\d+)__/g, (_, i) => {
      try {
        const raw = decodeEntities(mathInlines[parseInt(i)])
        return `<span class="math-inline">${katex.renderToString(raw, { displayMode: false, throwOnError: false })}</span>`
      } catch (e) { return `<span class="math-error">$${mathInlines[parseInt(i)]}$</span>` }
    })

    return html
  } catch (e) {
    console.error('Markdown rendering error:', e)
    return text
  }
}


function adjustHeight() {
  if (!inputRef.value) return
  inputRef.value.style.height = 'auto'
  const newHeight = Math.min(inputRef.value.scrollHeight, 150)
  inputRef.value.style.height = `${newHeight}px`
}

function handleContextMenu(event: MouseEvent, content: string) {
  event.preventDefault()
  const selection = window.getSelection()
  const selectedText = selection?.toString() || content
  const menu = document.createElement('div')
  menu.className = 'context-menu'
  menu.style.cssText = `position: fixed; left: ${event.clientX}px; top: ${event.clientY}px; background: white; border: 1px solid #E8E4DF; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 4px 0; z-index: 10000; min-width: 120px;`
  const copyItem = document.createElement('div')
  copyItem.textContent = '📋 复制'
  copyItem.style.cssText = `padding: 8px 16px; cursor: pointer; font-size: 14px; color: #2D2A26;`
  copyItem.onmouseover = () => { copyItem.style.background = '#F5F1EC' }
  copyItem.onmouseout = () => { copyItem.style.background = 'transparent' }
  copyItem.onclick = () => { navigator.clipboard.writeText(selectedText); document.body.removeChild(menu) }
  menu.appendChild(copyItem)
  document.body.appendChild(menu)
  const removeMenu = (e: MouseEvent) => { if (!menu.contains(e.target as Node)) { document.body.removeChild(menu); document.removeEventListener('click', removeMenu) } }
  setTimeout(() => document.addEventListener('click', removeMenu), 0)
}

onMounted(() => {
  checkConnection()
  setInterval(checkConnection, 30000)
})

watch(inputText, () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px'
  }
})
</script>

<style scoped>
/* ===== 🎨 Theme: Warm Glass (Claude-Inspired) with Dark Mode Support ===== */
.agent-container {
  /* Light Theme Variables (Default) */
  --theme-bg: rgba(250, 248, 245, 0.85);
  --theme-bg-solid: #FDFCFB;
  --theme-text: #2D2A26;
  --theme-text-secondary: #6B6762;
  --theme-accent: #D97D54;
  --theme-accent-light: #FEF3EE;
  --theme-border: rgba(232, 228, 223, 0.6);
  --theme-input-bg: rgba(0, 0, 0, 0.04);
  --theme-code-bg: #F3F4F6;
  --theme-bubble-bg: rgba(255, 255, 255, 0.6);
  --theme-bubble-active: rgba(255, 255, 255, 0.9);
  --theme-header-bg: rgba(255, 255, 255, 0.5);
  --theme-footer-bg: white;
  --theme-suggestion-bg: #FFFFFF;

  position: fixed;
  z-index: 9999;
}

/* Dark Theme Override */
[data-theme="dark"] .agent-container {
  --theme-bg: rgba(35, 35, 38, 0.92);
  --theme-bg-solid: #2A2A2E;
  --theme-text: #E8E8E6;
  --theme-text-secondary: #A8A8A5;
  --theme-accent: #E8A87C;
  --theme-accent-light: rgba(232, 168, 124, 0.15);
  --theme-border: rgba(60, 60, 65, 0.8);
  --theme-input-bg: rgba(255, 255, 255, 0.06);
  --theme-code-bg: #1E1E22;
  --theme-bubble-bg: rgba(50, 50, 55, 0.8);
  --theme-bubble-active: rgba(60, 60, 65, 0.95);
  --theme-header-bg: rgba(40, 40, 45, 0.8);
  --theme-footer-bg: #232326;
  --theme-suggestion-bg: #2A2A2E;
}

/* Glassmorphism Panel Base */
.glass-panel {
  background: var(--theme-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

/* ===== 🟢 Bubble: Draggable & Dockable ===== */
.agent-bubble {
  width: 50px;
  height: 50px;
  border-radius: 25px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease, background 0.3s ease;
  
  /* Bubble Style */
  background: var(--theme-bubble-bg);
  color: var(--theme-accent);
  border: 1px solid var(--theme-border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Dragging State */
.agent-container.is-dragging .agent-bubble {
  cursor: grabbing;
  transform: scale(1.1);
  background: var(--theme-bubble-active);
}

/* Docked State (Idle) */
.agent-container.is-docked .agent-bubble {
  opacity: 0.6;
  border-color: transparent;
  background: var(--theme-bubble-bg);
}
.agent-container.is-docked:hover .agent-bubble {
  opacity: 1;
  background: var(--theme-bubble-active);
}

/* Active State (Chat Open) */
.agent-bubble--active {
  background: var(--theme-accent) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(217, 125, 84, 0.4);
}

.agent-bubble:active {
  transform: scale(0.95);
}

.agent-bubble__icon {
  width: 24px;
  height: 24px;
  pointer-events: none;
}
.agent-bubble__icon svg { width: 100%; height: 100%; }

.agent-bubble__badge {
  position: absolute;
  top: 0; right: 0;
  width: 12px; height: 12px;
  background: #EF4444;
  border-radius: 50%;
  border: 2px solid white;
}

/* ===== 💬 Chat Window ===== */
.agent-chat {
  position: absolute;
  bottom: 60px;
  right: 0;
  width: 380px;
  height: 520px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: bottom right;
  z-index: 10000;
  
  /* Warm Texture with theme support */
  background: var(--theme-bg);
  transition: background 0.3s ease;
}

/* Responsive Chat Window - Scale up on larger screens */
@media (min-width: 1200px) {
  .agent-chat:not(.maximized) {
    width: 420px;
    height: 580px;
  }
}

@media (min-width: 1600px) {
  .agent-chat:not(.maximized) {
    width: 480px;
    height: 650px;
  }
}

@media (min-width: 1920px) {
  .agent-chat:not(.maximized) {
    width: 520px;
    height: 720px;
  }
}

/* Maximized State */
.agent-chat.maximized {
  position: fixed;
  top: 50px;
  left: 20px;
  right: 20px;
  bottom: 20px;
  width: auto;
  height: auto;
  transform: none !important;
  max-width: none;
  max-height: none;
  z-index: 10001;
}

/* Flip if on left */
.agent-chat.align-left {
  right: auto;
  left: 0;
  transform-origin: bottom left;
}

/* Animation */
.chat-window-enter-active,
.chat-window-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

/* Header */
.agent-chat__header {
  padding: 16px 20px;
  background: var(--theme-header-bg);
  border-bottom: 1px solid var(--theme-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.3s ease;
}

.agent-chat__title {
  display: flex; align-items: center; gap: 8px;
  font-weight: 600;
  color: var(--theme-text);
  font-size: 15px;
}
.agent-chat__avatar { font-size: 18px; color: var(--theme-accent); }
.agent-chat__actions { display: flex; gap: 6px; }

/* Header Buttons */
.header-btn {
  width: 28px; height: 28px;
  border: none; background: transparent;
  cursor: pointer; color: var(--theme-text-secondary);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.header-btn:hover { background: var(--theme-input-bg); color: var(--theme-text); }
.header-btn svg { width: 16px; height: 16px; }

/* Status */
.agent-chat__status { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--theme-text-secondary); margin-left: 8px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot--online { background: #22C55E; }
.status-dot--offline { background: var(--theme-text-secondary); }

/* Messages Area */
.agent-chat__messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scroll */
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

/* Readability Fix for Wide Windows */
.agent-chat.maximized .agent-chat__messages {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}
.agent-chat.maximized .agent-chat__input {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

/* Scroll to bottom button */
.scroll-to-bottom-btn {
  position: absolute;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--theme-bg-secondary);
  border: 1px solid var(--theme-border);
  color: var(--theme-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
  z-index: 10;
}
.scroll-to-bottom-btn:hover {
  background: var(--theme-bg-hover);
  color: var(--theme-text);
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.scroll-to-bottom-btn svg {
  width: 18px;
  height: 18px;
}

/* Welcome Screen */
.agent-chat__empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; text-align: center;
  padding: 20px;
}
.agent-chat__welcome h3 {
  margin: 0 0 8px;
  font-family: Georgia, serif; /* Restore Serif */
  font-weight: normal;
  font-size: 24px;
  color: var(--theme-text);
}
.agent-chat__welcome p { margin: 0; color: var(--theme-text-secondary); font-size: 14px; }
.welcome-icon { font-size: 32px; color: var(--theme-accent); margin-bottom: 16px; display: block; }

/* Suggestion Chips */
.agent-chat__suggestions {
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 24px;
}
.suggestion-chip {
  background: var(--theme-suggestion-bg);
  border: 1px solid var(--theme-border);
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 13px;
  color: var(--theme-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.suggestion-chip:hover {
  border-color: var(--theme-accent);
  color: var(--theme-accent);
  background: var(--theme-accent-light);
  transform: translateY(-1px);
}

/* Message Wrapper - Logic for Alignment */
.message-wrapper {
  display: flex;
  width: 100%;
}

.message-wrapper.message--user {
  justify-content: flex-end;
}

.message-wrapper.message--assistant {
  justify-content: flex-start;
}

/* Common Message Container */
.message {
  display: flex;
  gap: 12px;
  position: relative;
  /* Remove fixed width from base class to allow flexibility */
}

/* User Bubble Styles (Slim, Warm, Subtle) - fit-content is KEY */
.message--user .message {
  width: fit-content;
  max-width: 85%;
  background: var(--theme-bg-solid);
  color: var(--theme-text);
  border: 1px solid var(--theme-border);
  padding: 10px 16px;
  border-radius: 18px;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  margin-left: auto; /* Ensure it stays right even if flex weirdness happens */
}

/* Assistant Text Styles (Minimalist, Claude-like) */
.message--assistant .message {
  background: transparent;
  width: 100%;
  max-width: 100%;
  padding-left: 0;
}

/* Hide User Avatar (Claude Style) */
.message--user .message__avatar {
  display: none;
}

/* Assistant Avatar - Subtle Asterisk */
.message--assistant .message__avatar {
  font-size: 18px;
  color: var(--theme-accent);
  margin-top: 4px; /* Align with first line of text */
  flex-shrink: 0;
}

.message__content {
  flex: 1;
  overflow: hidden; /* Prevent horizontal overflow */
  min-width: 0; /* Required for flex child to shrink properly */
  max-width: 100%;
}

.message__text {
  font-size: 14px;
  line-height: 1.6;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  user-select: text; /* Overrides global user-select: none */
  cursor: text;
  max-width: 100%;
  overflow-x: auto; /* Allow scrolling for very wide content like code */
}

/* =========================================
   Tool Part Styles (OpenCode/Antigravity style)
   Minimal inline indicators, no prominent UI
   ========================================= */
.tool-part {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  margin: 2px 0;
  font-size: 12px;
  color: var(--theme-text-secondary);
  opacity: 0.85;
}

.tool-part--running {
  color: var(--theme-text-secondary);
}

.tool-part--completed {
  color: var(--theme-text-secondary);
}

.tool-part--error {
  color: #e74c3c;
}

.tool-part__icon {
  font-size: 12px;
  opacity: 0.7;
}

.tool-part__name {
  font-weight: 400;
}

.tool-part__spinner {
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--theme-border);
  border-top-color: var(--theme-text-secondary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tool-part__check {
  color: var(--theme-text-secondary);
  font-size: 11px;
}

.tool-part__output {
  display: none; /* Hide output in minimal style */
}

/* Ensure code blocks don't overflow */
.message__text pre {
  max-width: 100%;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.message__text code {
  word-break: break-all;
}

/* Tables should scroll horizontally if too wide but keep table layout */
.message__text table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--theme-border);
  table-layout: auto; /* Allow content to define width */
}

/* Status Update (Floating & Pulsing) */
.status-update {
  align-self: flex-start;
  margin: 5px 0 10px 12px; /* Moved left */
  padding: 4px 0;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px; /* Even smaller */
  color: var(--theme-accent);
  opacity: 0.8;
  animation: shimmer 2s infinite ease-in-out;
}

@keyframes shimmer {
  0% { opacity: 0.4; transform: translateY(0px); }
  50% { opacity: 0.8; transform: translateY(-1px); }
  100% { opacity: 0.4; transform: translateY(0px); }
}

.status-update__dots { opacity: 0.6; }

/* Typing Minimal */
.typing-minimal {
  align-self: flex-start;
  margin-left: 40px;
  padding: 8px 0;
}
.typing-indicator span {
  width: 4px; height: 4px; background: var(--theme-text-secondary); border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* ========== Compact & Unified Input Area (v2) ========== */
.agent-chat__footer {
  padding: 8px 12px;
  background: var(--theme-footer-bg);
  border-top: 1px solid var(--theme-border);
  transition: background 0.3s ease;
}

/* Responsive footer in maximized mode - match chat area width */
.agent-chat.maximized .agent-chat__footer {
  display: flex;
  justify-content: center;
  padding: 12px 20px;
}

.agent-chat.maximized .agent-chat__footer .chat-input-unified-box {
  width: 100%;
  max-width: 800px;
}

/* Context bar alignment in maximized mode */
.agent-chat.maximized .agent-chat__context-bar {
  display: flex;
  justify-content: flex-start; /* Align content to start (left) */
  width: 100%;
  max-width: 800px; /* Match input box width */
  margin: 0 auto;   /* Center the bar itself in the window */
  padding-left: 6px; /* Align strictly with input content (match input padding) */
}


.chat-input-unified-box {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  padding: 4px 6px;
  background: var(--theme-input-bg);
  border-radius: 12px;
  transition: background 0.2s, box-shadow 0.2s;
  position: relative;
}

.chat-input-unified-box:focus-within {
  background: var(--theme-input-bg);
  box-shadow: 0 0 0 1px rgba(217, 125, 84, 0.15);
}

/* + Menu Wrapper & Button */
.input-menu-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 1px; /* Visual alignment with textarea bottom */
}

.menu-trigger-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--theme-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.menu-trigger-btn:hover, .menu-trigger-btn.active {
  color: var(--theme-accent);
  background: var(--theme-accent-light);
}

.menu-trigger-btn svg {
  width: 12px;
  height: 12px;
}

/* Redesigned Popup Menu (Smaller) */
.input-menu-popup {
  position: absolute;
  bottom: 30px;
  left: -4px;
  min-width: 140px;
  background: var(--theme-bg-solid);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  overflow: hidden;
  z-index: 100;
  padding: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
  font-size: 12px;
  color: var(--theme-text);
}

.menu-item:hover {
  background: var(--theme-accent-light);
  color: var(--theme-accent);
}

.menu-icon {
  font-size: 12px;
  width: 14px;
  text-align: center;
  color: var(--theme-text-secondary);
}

.menu-item:hover .menu-icon {
  color: var(--theme-accent);
}

.menu-icon.smaller { font-size: 10px; }

/* Menu Fade Transition */
.menu-fade-enter-active, .menu-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.menu-fade-enter-from, .menu-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

/* Auto-resize Textarea */
.chat-input-unified-box textarea {
  flex: 1;
  min-height: 24px;
  max-height: 120px;
  padding: 4px 4px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.4;
  resize: none;
  outline: none;
  overflow-y: auto;
  color: var(--theme-text);
}

.chat-input-unified-box textarea::placeholder {
  color: var(--theme-text-secondary);
  opacity: 0.6;
  font-size: 12px;
}

/* Compact Send/Stop Buttons */
.send-btn-compact, .stop-btn-compact {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
  margin-bottom: 1px;
}

.send-btn-compact {
  background: transparent;
  color: var(--theme-text-secondary);
}

.send-btn-compact:hover:not(:disabled) {
  color: var(--theme-accent);
  background: var(--theme-accent-light);
}

.send-btn-compact:disabled {
  opacity: 0.4;
  cursor: default;
}

.send-btn-compact svg {
  width: 14px;
  height: 14px;
}

.stop-btn-compact {
  background: #EF4444;
}

.stop-icon-small {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 1px;
}

/* Note Selector Dropdown (Even smaller) */
.note-selector-dropdown {
  position: absolute;
  bottom: 30px;
  left: -4px;
  width: 180px;
  max-height: 200px;
  background: var(--theme-bg-solid);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 100;
}

.selector-header {
  padding: 6px 10px;
  font-size: 9px;
  font-weight: 700;
  color: var(--theme-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--theme-border);
}

.selector-list {
  flex: 1;
  overflow-y: auto;
  padding: 3px;
}

.selector-item {
  padding: 5px 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.selector-item:hover {
  background: var(--theme-accent-light);
}

.item-icon { font-size: 11px; }
.item-title {
  font-size: 11px;
  color: var(--theme-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selector-empty {
  padding: 12px;
  text-align: center;
  color: var(--theme-text-secondary);
  font-size: 11px;
}

/* Context Bar (Mini Pills) */
.agent-chat__context-bar {
  padding: 2px 12px 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.context-pill {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 9px;
  background: var(--theme-input-bg);
  color: var(--theme-text-secondary);
  max-width: 120px;
}

.mentioned-pill {
  background: rgba(217, 125, 84, 0.08);
  color: var(--theme-accent);
}

.inspecting-pill.inactive {
  opacity: 0.5;
  text-decoration: line-through;
  filter: grayscale(1);
}

.pill-toggle-btn {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  transition: transform 0.2s;
}

.pill-toggle-btn:hover {
  transform: scale(1.1);
}

.eye-svg, .pill-svg {
  width: 11px;
  height: 11px;
  flex-shrink: 0;
}

.pill-toggle-btn {
  display: flex;
  align-items: center;
}

.pill-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pill-clear {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 10px;
  cursor: pointer;
  opacity: 0.5;
}

.pill-clear:hover { opacity: 1; }

/* Shallow Glass override */
.shallow-glass {
  backdrop-filter: blur(4px);
  background: var(--theme-bg-solid) !important;
}

/* Custom Scrollbar */
.agent-chat__messages::-webkit-scrollbar { width: 4px; }
.agent-chat__messages::-webkit-scrollbar-track { background: transparent; }
.agent-chat__messages::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb, rgba(0,0,0,0.1)); border-radius: 4px; }

/* Markdown Styles Override */
/* Default (Small) Chat Headers */
:deep(.message__text h1) { font-size: 1.2em; margin: 12px 0 6px; }
:deep(.message__text h2) { font-size: 1.1em; margin: 10px 0 5px; }
:deep(.message__text h3) { font-size: 1.05em; margin: 8px 0 4px; }

:deep(.message__text h1), :deep(.message__text h2), :deep(.message__text h3) {
  font-weight: 600;
  line-height: 1.3;
  color: var(--theme-text);
}

/* Maximized Chat Headers */
.maximized :deep(.message__text h1) { font-size: 1.5em; margin: 18px 0 10px; }
.maximized :deep(.message__text h2) { font-size: 1.3em; margin: 16px 0 8px; }
.maximized :deep(.message__text h3) { font-size: 1.2em; margin: 14px 0 6px; }

@keyframes messageSlide {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
:deep(.message__text ul), :deep(.message__text ol) {
  padding-left: 28px; /* High enough to prevent overlap/cutoff */
  margin: 8px 0;
}
:deep(.message__text li) {
  margin-bottom: 4px;
}
:deep(.message__text li::marker) {
  color: var(--theme-accent);
  font-weight: 600;
}
:deep(.message__text pre) { 
  background: var(--theme-code-bg); 
  border-radius: 8px; 
  padding: 12px; 
  margin: 8px 0; 
  overflow-x: auto; /* Internal scroll ONLY */
  max-width: 100%;
}
:deep(.math-block) {
  margin: 12px 0;
  padding: 12px;
  background: var(--theme-input-bg);
  border-radius: 8px;
  overflow-x: auto;
  text-align: center;
}
:deep(.math-inline) {
  padding: 0 4px;
}
:deep(.math-error) {
  color: #EF4444;
  font-family: monospace;
  background: #FEF2F2;
  padding: 2px 4px;
  border-radius: 4px;
}
:deep(.message__text table) {
  display: table; /* Reset to standard table behavior */
  width: max-content;
  min-width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  background: var(--theme-bg-solid);
  border-radius: 8px;
  border: 1px solid var(--theme-border);
  overflow: hidden; /* For radius */
}

/* Wrapping table in a container for horizontal scroll without breaking table layout */
.message__text {
  overflow-x: auto;
}

:deep(.message__text th), :deep(.message__text td) {
  border: 1px solid var(--theme-border);
  padding: 10px 16px;
  text-align: left;
  min-width: 80px;
  white-space: normal;
  word-break: normal;
  line-height: 1.5;
}

:deep(.message__text th) {
  background: var(--theme-accent-light);
  font-weight: 600;
  white-space: nowrap; 
  color: var(--theme-accent);
}

/* Sub-scrollbar for the container */
.message__text::-webkit-scrollbar { height: 4px; }
.message__text::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb, rgba(0,0,0,0.1)); border-radius: 4px; }
:deep(.message__text hr) { border: none; border-top: 1px solid var(--theme-border); margin: 16px 0; }

/* Session History Panel */
.session-history-panel {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--theme-bg-solid);
  z-index: 100;
  display: flex;
  flex-direction: column;
  border-radius: 0 0 16px 16px;
}

.session-history__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--theme-border);
  font-weight: 500;
  color: var(--theme-text);
}

.session-history__header .close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--theme-text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
}

.session-history__header .close-btn:hover {
  background: var(--theme-hover);
}

.session-history__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-history__empty {
  text-align: center;
  color: var(--theme-text-secondary);
  padding: 40px 20px;
  font-size: 13px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 4px;
}

.session-item:hover {
  background: var(--theme-hover);
}

.session-item--active {
  background: var(--theme-accent-light, rgba(var(--accent-rgb), 0.1));
}

.session-item--pinned {
  border-left: 2px solid var(--theme-accent);
}

.session-item__preview {
  flex: 1;
  font-size: 13px;
  color: var(--theme-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pin-indicator {
  color: var(--theme-accent);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pin-indicator svg {
  width: 12px;
  height: 12px;
}

.session-item__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.session-item:hover .session-item__actions {
  opacity: 1;
}

.session-item__btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--theme-text-secondary);
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.session-item__btn:hover {
  background: var(--theme-bg-secondary);
  color: var(--theme-text);
}

.session-item__btn--danger:hover {
  color: var(--color-danger, #ef4444);
}

.session-item__btn svg {
  width: 14px;
  height: 14px;
}

.session-rename-input {
  flex: 1;
  background: var(--theme-bg);
  border: 1px solid var(--theme-accent);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  color: var(--theme-text);
  outline: none;
}

/* Slide Panel Transition */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
