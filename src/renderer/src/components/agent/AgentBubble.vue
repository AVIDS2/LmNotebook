<template>
  <!-- Main Container with dynamic position -->
  <div 
    class="agent-container" 
    :style="containerStyle"
    @mousedown="startDrag"
    :class="{ 'is-dragging': isDragging, 'is-docked': isDocked && !isOpen }"
  >
    <!-- Floating Bubble Button -->
    <div
      class="agent-bubble glass-panel"
      :class="{ 'agent-bubble--active': isOpen }"
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
          <div class="agent-chat__title">
            <span class="agent-chat__avatar">✦</span>
            <span>Origin Agent</span>
          </div>
          <div class="agent-chat__actions">
            <button class="header-btn" @click="clearChat" title="开始新对话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            </button>
            <button class="header-btn" @click="isMaximized = !isMaximized" :title="isMaximized ? '还原' : '最大化'">
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

        <!-- Messages -->
        <div class="agent-chat__messages" ref="messagesContainer">
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
                @click="sendMessage(suggestion)"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>

          <div
            v-for="(msg, index) in messages.filter(m => m.content.trim())"
            :key="index"
            class="message-wrapper"
            :class="[`message--${msg.role}`]">
            <div class="message">
              <div class="message__avatar">
                {{ msg.role === 'user' ? '◉' : '✦' }}
              </div>
              <div class="message__content">
                <div class="message__text" 
                     v-html="renderMarkdown(msg.content)"
                     @contextmenu="handleContextMenu($event, msg.content)"></div>
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

        <!-- Input -->
        <div class="agent-chat__input">
          <textarea
            v-model="inputText"
            @keydown.enter.exact.prevent="sendMessage()"
            @input="adjustHeight"
            placeholder="输入消息... (Enter 发送)"
            rows="1"
            ref="inputRef"
          ></textarea>
          <div class="input-actions">
            <button
              v-if="!isTyping"
              class="send-button"
              :disabled="!inputText.trim()"
              @click="sendMessage()"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22,2 15,22 11,13 2,9"/>
              </svg>
            </button>
            <button
              v-else
              class="stop-button"
              @click="stopGeneration"
              title="停止生成"
            >
              <div class="stop-icon"></div>
            </button>
          </div>
        </div>
      </div>
    </Transition>
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

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
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
const streamingMessage = ref<ChatMessage | null>(null)
const currentStatus = ref('')
const abortController = ref<AbortController | null>(null)

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
onMounted(() => {
  window.addEventListener('resize', () => { windowWidth.value = window.innerWidth })
  setTimeout(snapToEdge, 100) // Initial dock
})
onUnmounted(() => {
  window.removeEventListener('resize', () => { windowWidth.value = window.innerWidth })
})
// ----------------------

const suggestions = [
  '帮我搜索最近的笔记',
  '整理一下当前笔记的格式',
  '总结一下这篇笔记的内容'
]

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
  inputRef.value?.focus()
}

async function checkConnection() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`)
    isConnected.value = response.ok
  } catch {
    isConnected.value = false
  }
}

async function sendMessage(text?: string) {
  const messageText = text || inputText.value.trim()
  if (!messageText || isTyping.value) return
  
  messages.value.push({
    role: 'user',
    content: messageText,
    timestamp: new Date()
  })
  
  inputText.value = ''
  nextTick(() => adjustHeight())
  isTyping.value = true
  scrollToBottom()
  
  abortController.value = new AbortController()
  
  const assistantMessage: ChatMessage = {
    role: 'assistant',
    content: '',
    timestamp: new Date()
  }
  messages.value.push(assistantMessage)
  streamingMessage.value = assistantMessage
  
  try {
    const noteContext = getCurrentNoteContext()
    
    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: abortController.value.signal,
      body: JSON.stringify({
        message: messageText,
        history: messages.value.slice(0, -2).slice(-10).map(m => ({
          role: m.role,
          content: m.content
        })),
        note_context: noteContext,
        active_note_id: noteStore.currentNote?.id || null
      })
    })
    
    if (!response.ok) throw new Error('请求失败')
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')
    const decoder = new TextDecoder()
    let buffer = ''
    
    const messageIndex = messages.value.length - 1
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      
      for (const line of events) {
        if (!line.trim()) continue
        const dataMatch = line.match(/^data:\s*(.*)$/)
        if (!dataMatch) continue
        
        const rawData = dataMatch[1]
        if (rawData === '[DONE]') continue
        
        try {
          const chunk = JSON.parse(rawData)
          
          if (chunk.type === 'status') {
            currentStatus.value = chunk.text
            continue
          }
          if (currentStatus.value) currentStatus.value = ''
          
          if (chunk.text) {
            messages.value[messageIndex].content += chunk.text
            messages.value = [...messages.value]
            scrollToBottom()
          } else if (chunk.tool_call) {
            // HANDLE REAL-TIME TOOL CALL
            await handleToolCallEvent(chunk, messages.value[messageIndex])
          } else if (chunk.error) {
            messages.value[messageIndex].content = `❌ 错误: ${chunk.error}`
            messages.value = [...messages.value]
          }
        } catch {
          messages.value[messageIndex].content += rawData
          messages.value = [...messages.value]
          scrollToBottom()
        }
      }
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
      if (streamingMessage.value) streamingMessage.value.content = '❌ 抱歉，连接服务器出错。'
    }
  } finally {
    isTyping.value = false
    streamingMessage.value = null
    currentStatus.value = ''
    abortController.value = null
    scrollToBottom()
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
      msg.content = data.message || `✅ 已成功创建笔记！`
    } else if (data.tool_call === 'note_updated') {
      await noteStore.loadNotes()
      msg.content = data.message || '✅ 笔记已更新！'
    } else if (data.tool_call === 'note_deleted') {
      await noteStore.loadNotes()
      msg.content = data.message || '🗑️ 笔记已从知识库中移除。'
    } else if ((data.tool_call === 'format_apply' || data.tool_call === 'note_updated') && data.formatted_html && setEditorContent) {
      const renderedHtml = await marked.parse(data.formatted_html, { async: true, breaks: true, gfm: true })
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

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    const mathBlocks: string[] = []
    const mathInlines: string[] = []

    // 1. Double escape certain math chars and protect blocks
    let tmp = text
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
    renderer.code = function({ text, lang }) {
      const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
      const highlighted = hljs.highlight(text, { language }).value
      return `<pre class="hljs-container"><code class="hljs language-${language}">${highlighted}</code></pre>`
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
/* ===== 🎨 Theme: Warm Glass (Claude-Inspired) ===== */
.agent-container {
  /* Define variables locally within the component scope */
  --theme-bg: rgba(250, 248, 245, 0.85); /* Warm Beige Glass */
  --theme-text: #2D2A26;
  --theme-text-secondary: #6B6762;
  --theme-accent: #D97D54; /* Terracotta */
  --theme-accent-light: #FEF3EE;
  --theme-border: rgba(232, 228, 223, 0.6);

  position: fixed;
  z-index: 9999;
  /* dynamic top/left */
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
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
  
  /* Bubble Style */
  background: rgba(255, 255, 255, 0.6); /* Translucent when idle */
  color: var(--theme-accent);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Dragging State */
.agent-container.is-dragging .agent-bubble {
  cursor: grabbing;
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.9);
}

/* Docked State (Idle) */
.agent-container.is-docked .agent-bubble {
  opacity: 0.6; /* Dim to blend in */
  border-color: transparent;
  background: rgba(255, 255, 255, 0.4); 
}
.agent-container.is-docked:hover .agent-bubble {
  opacity: 1;
  background: rgba(255, 255, 255, 0.9);
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
  
  /* Re-apply Warm Texture */
  background: rgba(250, 248, 245, 0.90);
}

/* Maximized State */
.agent-chat.maximized {
  position: fixed;
  top: 20px;
  left: 20px;
  right: 20px;
  bottom: 80px;
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
  background: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid var(--theme-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  transition: background 0.2s;
}
.header-btn:hover { background: rgba(0,0,0,0.06); color: var(--theme-text); }
.header-btn svg { width: 16px; height: 16px; }

/* Status */
.agent-chat__status { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #999; margin-left: 8px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot--online { background: #22C55E; }
.status-dot--offline { background: #9CA3AF; }

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
  background: #FFFFFF;
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
  background: #FDFCFB;
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
  overflow: visible; /* Allow math to peek out if needed, handled by parent scroll */
}

.message__text {
  font-size: 14px;
  line-height: 1.6;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  user-select: text; /* Overrides global user-select: none */
  cursor: text;
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
  width: 4px; height: 4px; background: #999; border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* Input Area */
.agent-chat__input {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.6);
  border-top: 1px solid var(--theme-border);
  display: flex;
  align-items: flex-end; /* Align to bottom as it grows */
  gap: 10px;
}

.agent-chat__input textarea {
  flex: 1;
  border: 1px solid transparent;
  border-radius: 14px;
  padding: 10px 14px;
  background: #FFFFFF;
  font-family: inherit;
  resize: none; 
  outline: none; 
  font-size: 14px;
  max-height: 150px;
  overflow-y: hidden; /* No scrollbar as requested */
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
  transition: border-color 0.2s, box-shadow 0.2s;
  line-height: 1.4;
}

.input-actions {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}
.agent-chat__input textarea:focus {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border-color: rgba(217, 125, 84, 0.3);
}

.send-button, .stop-button {
  width: 40px; height: 40px;
  border-radius: 12px;
  border: none;
  background: var(--theme-accent);
  color: white;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.1s, background 0.2s;
  box-shadow: 0 4px 10px rgba(217, 125, 84, 0.3);
}
.send-button:hover { background: #C46A45; transform: scale(1.05); }
.send-button:active { transform: scale(0.95); }
.send-button:disabled { background: #E5E7EB; box-shadow: none; cursor: default; }

.stop-button { background: #EF4444; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.3); }
.stop-icon { width: 12px; height: 12px; background: white; border-radius: 2px; }

/* Custom Scrollbar */
.agent-chat__messages::-webkit-scrollbar { width: 4px; }
.agent-chat__messages::-webkit-scrollbar-track { background: transparent; }
.agent-chat__messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 4px; }

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
  background: #F3F4F6; 
  border-radius: 8px; 
  padding: 12px; 
  margin: 8px 0; 
  overflow-x: auto; /* Internal scroll ONLY */
  max-width: 100%;
}
:deep(.math-block) {
  margin: 12px 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.02);
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
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  margin: 12px 0;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--theme-border);
  -webkit-overflow-scrolling: touch;
}
:deep(.message__text th), :deep(.message__text td) {
  border: 1px solid var(--theme-border);
  padding: 8px 16px;
  text-align: left;
  min-width: 120px; /* Guard against character stacking */
  white-space: normal;
  word-break: normal;
  overflow-wrap: normal;
}
:deep(.message__text th) {
  background: var(--theme-accent-light);
  font-weight: 600;
  white-space: nowrap; 
}
/* Sub-scrollbar for tables */
:deep(.message__text table::-webkit-scrollbar) { height: 4px; }
:deep(.message__text table::-webkit-scrollbar-thumb) { background: rgba(0,0,0,0.1); border-radius: 4px; }
:deep(.message__text hr) { border: none; border-top: 1px solid var(--theme-border); margin: 16px 0; }
</style>
