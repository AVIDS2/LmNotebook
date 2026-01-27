<template>
  <div class="agent-container">
    <!-- Floating Bubble Button with Origin Logo -->
    <div
      class="agent-bubble"
      :class="{ 'agent-bubble--active': isOpen }"
      @click="toggleChat"
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
      <div v-if="isOpen" class="agent-chat" :class="{ 'maximized': isMaximized }">
        <!-- Header -->
        <div class="agent-chat__header">
          <div class="agent-chat__title">
            <span class="agent-chat__avatar">✦</span>
            <span>Origin Agent</span>
          </div>
          <div class="agent-chat__actions">
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
              {{ isConnected ? '在线' : '离线' }}
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
            class="message"
            :class="[`message--${msg.role}`]">
            <div class="message__avatar">
              {{ msg.role === 'user' ? '◉' : '✦' }}
            </div>
            <div class="message__content">
              <div class="message__text" 
                   v-html="renderMarkdown(msg.content)"
                   @contextmenu="handleContextMenu($event, msg.content)"></div>
              <div class="message__time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>

          <div v-if="isTyping" class="message message--assistant">
            <div class="message__avatar">✦</div>
            <div class="message__content">
              <div class="typing-indicator">
                <div v-if="currentStatus" class="message__status-float">
                  {{ currentStatus }}
                </div>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="agent-chat__input">
          <textarea
            v-model="inputText"
            @keydown.enter.exact.prevent="sendMessage()"
            placeholder="输入消息... (Enter 发送)"
            rows="1"
            ref="inputRef"
          ></textarea>
          <button
            class="send-button"
            :disabled="!inputText.trim() || isTyping"
            @click="sendMessage()"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22,2 15,22 11,13 2,9"/>
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch, inject } from 'vue'
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

// Stores
const noteStore = useNoteStore()

// Inject editor action
const setEditorContent = inject<(html: string) => void>('setEditorContent')

// Backend URL
const BACKEND_URL = 'http://127.0.0.1:8765'

// Suggestions
const suggestions = [
  '帮我搜索最近的笔记',
  '整理一下当前笔记的格式',
  '总结一下这篇笔记的内容'
]

// Toggle chat window
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

// Check backend connection
async function checkConnection() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`)
    if (response.ok) {
      isConnected.value = true
    } else {
      isConnected.value = false
    }
  } catch {
    isConnected.value = false
  }
}

// Send message with SSE streaming
async function sendMessage(text?: string) {
  const messageText = text || inputText.value.trim()
  if (!messageText || isTyping.value) return
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: messageText,
    timestamp: new Date()
  })
  
  inputText.value = ''
  isTyping.value = true
  scrollToBottom()
  
  // Create assistant message placeholder for streaming
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
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')
    const decoder = new TextDecoder()
    let buffer = ''
    
    // Get the index of the assistant message for reactive updates
    const messageIndex = messages.value.length - 1
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // Split SSE events by \n\n
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      
      for (const event of events) {
        const dataMatch = event.match(/^data:\s*(.+)$/m)
        if (dataMatch && dataMatch[1] !== '[DONE]') {
          try {
            // Parse JSON-encoded chunk
            const chunk = JSON.parse(dataMatch[1])
            
            // Check for status message (shows current operation)
            if (chunk.type === 'status') {
              currentStatus.value = chunk.text
              continue
            }
            
            // Clear status when real content arrives
            if (currentStatus.value) {
              currentStatus.value = ''
            }
            
            if (chunk.text) {
              // Update via array index to trigger Vue reactivity
              messages.value[messageIndex].content += chunk.text
              // Force reactivity by triggering array update
              messages.value = [...messages.value]
              scrollToBottom()
            } else if (chunk.error) {
              messages.value[messageIndex].content = `❌ 错误: ${chunk.error}`
              messages.value = [...messages.value]
            }
          } catch {
            // Fallback for non-JSON data
            messages.value[messageIndex].content += dataMatch[1]
            messages.value = [...messages.value]
            scrollToBottom()
          }
        }
      }
    }
    
    // Get final message content for tool call check
    const assistantMessage = messages.value[messageIndex]
    
    // Final check for tool calls in the full message
    if (assistantMessage.content.trim().startsWith('{') && assistantMessage.content.trim().endsWith('}')) {
      try {
        const data = JSON.parse(assistantMessage.content.trim())
        
        // Handle Note Created
        if (data.tool_call === 'note_created') {
          await noteStore.loadNotes()
          if (data.note_id) {
            const newNote = await noteRepository.getById(data.note_id)
            if (newNote) noteStore.currentNote = newNote
          }
          assistantMessage.content = data.message || `✅ 已成功创建笔记！`
          messages.value = [...messages.value]
        }
        
        // Handle Note Updated
        else if (data.tool_call === 'note_updated') {
          await noteStore.loadNotes()
          assistantMessage.content = data.message || '✅ 笔记已更新！'
          messages.value = [...messages.value]
        }

        // Handle Note Deleted
        else if (data.tool_call === 'note_deleted') {
          await noteStore.loadNotes()
          // If deleted the current note, the store will likely select another one
          assistantMessage.content = data.message || '🗑️ 笔记已移至回收站。'
          messages.value = [...messages.value]
        }
        
        // Handle Format Brush
        else if (data.tool_call === 'format_apply' && data.formatted_html && setEditorContent) {
          setEditorContent(data.formatted_html)
          assistantMessage.content = '✨ 已完成内容排版与优化，并已直接应用到当前笔记。'
          messages.value = [...messages.value]
        }
        
        // Handle Summarization
        else if (data.tool_call === 'note_summarized') {
          assistantMessage.content = data.message || data.content
          messages.value = [...messages.value]
        }
      } catch (e) {
        // Not a JSON tool call, leave it as text
      }
    }
    
    if (!isOpen.value) {
      hasUnread.value = true
    }
  } catch (error) {
    assistantMessage.content = '抱歉，无法连接到 AI 后端。请确保后端服务正在运行。'
  } finally {
    isTyping.value = false
    streamingMessage.value = null
    currentStatus.value = ''
    scrollToBottom()
  }
}

// Get current note context from the editor
function getCurrentNoteContext(): string | null {
  try {
    // Attempt to get content from TipTap / ProseMirror
    const editor = document.querySelector('.tiptap.ProseMirror') as any
    if (editor && editor._tiptap) {
      // If we can access internal tiptap instance
      return editor._tiptap.getHTML()
    }
    // Fallback to text content
    const editorContent = document.querySelector('.ProseMirror')?.innerHTML
    return editorContent || null
  } catch {
    return null
  }
}

// Scroll to bottom of messages
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Render markdown to HTML
function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    // 1. Pre-process math patterns
    let processedText = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
      try {
        return `MATH_BLOCK_START${formula}MATH_BLOCK_END`
      } catch (e) { return match }
    })
    
    processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
      try {
        return `MATH_INLINE_START${formula}MATH_INLINE_END`
      } catch (e) { return match }
    })

    // 2. Configure marked
    const renderer = new marked.Renderer()
    renderer.code = function({ text, lang }) {
      const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
      const highlighted = hljs.highlight(text, { language }).value
      return `<pre class="hljs-container"><code class="hljs language-${language}">${highlighted}</code></pre>`
    }

    // 3. Render Markdown
    let html = marked.parse(processedText, { renderer, async: false, breaks: true, gfm: true }) as string

    // 4. Post-process math to insert real KaTeX
    html = html.replace(/MATH_BLOCK_START([\s\S]+?)MATH_BLOCK_END/g, (_, formula) => {
      return `<div class="math-block">${katex.renderToString(formula, { displayMode: true, throwOnError: false })}</div>`
    })
    html = html.replace(/MATH_INLINE_START([\s\S]+?)MATH_INLINE_END/g, (_, formula) => {
      return `<span class="math-inline">${katex.renderToString(formula, { displayMode: false, throwOnError: false })}</span>`
    })

    return html
  } catch (e) {
    console.error('Markdown error:', e)
    return text
  }
}

// Format timestamp
function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Handle right-click context menu
function handleContextMenu(event: MouseEvent, content: string) {
  event.preventDefault()
  
  // Get selected text or use full content
  const selection = window.getSelection()
  const selectedText = selection?.toString() || content
  
  // Create simple context menu
  const menu = document.createElement('div')
  menu.className = 'context-menu'
  menu.style.cssText = `
    position: fixed;
    left: ${event.clientX}px;
    top: ${event.clientY}px;
    background: white;
    border: 1px solid #E8E4DF;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 4px 0;
    z-index: 10000;
    min-width: 120px;
  `
  
  const copyItem = document.createElement('div')
  copyItem.textContent = '📋 复制'
  copyItem.style.cssText = `
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
    color: #2D2A26;
  `
  copyItem.onmouseover = () => { copyItem.style.background = '#F5F1EC' }
  copyItem.onmouseout = () => { copyItem.style.background = 'transparent' }
  copyItem.onclick = () => {
    navigator.clipboard.writeText(selectedText)
    document.body.removeChild(menu)
  }
  
  menu.appendChild(copyItem)
  document.body.appendChild(menu)
  
  // Remove menu on click outside
  const removeMenu = (e: MouseEvent) => {
    if (!menu.contains(e.target as Node)) {
      document.body.removeChild(menu)
      document.removeEventListener('click', removeMenu)
    }
  }
  setTimeout(() => document.addEventListener('click', removeMenu), 0)
}

// Check connection on mount
onMounted(() => {
  checkConnection()
  // Recheck every 30 seconds
  setInterval(checkConnection, 30000)
})

// Auto-resize textarea
watch(inputText, () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px'
  }
})
</script>

<style scoped>
/* ===== Claude-Inspired Theme Variables ===== */
:root {
  --claude-bg: #FAF8F5;
  --claude-card: #FFFFFF;
  --claude-border: #E8E4DF;
  --claude-text: #2D2A26;
  --claude-text-secondary: #6B6762;
  --claude-accent: #D97D54;
  --claude-accent-light: #FEF3EE;
  --claude-user-bubble: #F5F1EC;
}

.agent-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}

/* Floating Bubble - Terracotta accent */
.agent-bubble {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: #D97D54;
  box-shadow: 0 4px 12px rgba(217, 125, 84, 0.25);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  position: relative;
}

.agent-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(217, 125, 84, 0.35);
}

.agent-bubble--active {
  background: #C46A45;
}

.agent-bubble__icon {
  width: 24px;
  height: 24px;
  color: white;
}

.agent-bubble__icon svg {
  width: 100%;
  height: 100%;
}

.agent-bubble__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 12px;
  height: 12px;
  background: #EF4444;
  border-radius: 50%;
  border: 2px solid white;
}

/* Chat Window - Clean Claude Style */
.agent-chat {
  position: absolute;
  bottom: 64px;
  right: 0;
  min-width: 360px;
  max-width: 440px;
  width: 400px;
  min-height: 400px;
  max-height: 70vh;
  height: 520px;
  background: #FAF8F5;
  border-radius: 20px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.2s ease;
}

/* Maximized state */
.agent-chat.maximized {
  position: fixed;
  top: 24px;
  left: 24px;
  bottom: 24px;
  right: 24px;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  border-radius: 24px;
}

.chat-window-enter-active,
.chat-window-leave-active {
  transition: all 0.25s ease;
}

.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

/* Header - Minimal */
.agent-chat__header {
  padding: 16px 20px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8E4DF;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-chat__title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #2D2A26;
  font-size: 15px;
}

.agent-chat__avatar {
  font-size: 18px;
}

.agent-chat__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.header-btn:hover {
  background: #F0EDE8;
}

.header-btn svg {
  width: 16px;
  height: 16px;
  color: #6B6762;
}

.agent-chat__status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6B6762;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--online {
  background: #22C55E;
}

.status-dot--offline {
  background: #9CA3AF;
}

/* Messages Area */
.agent-chat__messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #FAF8F5;
}

.agent-chat__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 24px;
}

.agent-chat__welcome {
  margin-bottom: 24px;
}

.welcome-icon {
  font-size: 28px;
  display: block;
  margin-bottom: 16px;
  color: #D97D54;
}

.agent-chat__welcome h3 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 400;
  font-family: Georgia, 'Times New Roman', serif;
  color: #2D2A26;
  letter-spacing: -0.02em;
}

.agent-chat__welcome p {
  margin: 0;
  font-size: 14px;
  color: #6B6762;
  line-height: 1.5;
}

.agent-chat__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.suggestion-chip {
  padding: 8px 14px;
  background: #FFFFFF;
  border: 1px solid #E8E4DF;
  border-radius: 20px;
  color: #2D2A26;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.suggestion-chip:hover {
  background: #FEF3EE;
  border-color: #D97D54;
  color: #D97D54;
}

/* Message Bubbles */
.message {
  display: flex;
  gap: 12px;
  max-width: 95%;
}

.message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message--assistant {
  align-self: flex-start;
}

.message__avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #F0EDE8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}

.message--assistant .message__avatar {
  background: #FEF3EE;
}

.message__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.message__text {
  padding: 16px 20px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: #2D2A26;
  word-wrap: break-word;
  overflow-wrap: break-word;
  user-select: text;
  cursor: text;
  -webkit-user-select: text;
}

.message--user .message__text {
  background: #FFFFFF;
  border: 1px solid #E8E4DF;
  border-bottom-right-radius: 6px;
}

.message--assistant .message__text {
  background: #FAF8F5;
  border: 1px solid #E8E4DF;
  border-bottom-left-radius: 6px;
}

.message__text :deep(p) {
  margin: 0 0 12px;
}

.message__text :deep(p:last-child) {
  margin-bottom: 0;
}

.message__text :deep(h1),
.message__text :deep(h2),
.message__text :deep(h3),
.message__text :deep(h4) {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #1a1a1a;
}

.message__text :deep(h3) {
  font-size: 15px;
}

.message__text :deep(ul),
.message__text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message__text :deep(li) {
  margin: 6px 0;
}

.message__text :deep(code) {
  background: #F0EDE8;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
}

.message__text :deep(pre) {
  background: #F0EDE8;
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.message__text :deep(blockquote) {
  border-left: 3px solid #D97D54;
  margin: 12px 0;
  padding-left: 16px;
  color: #666;
  font-style: italic;
}

.message__text :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.message__time {
  font-size: 11px;
  color: #9CA3AF;
  padding: 0 4px;
}

.message--user .message__time {
  text-align: right;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  position: relative; /* For floating status */
}

.message__status-float {
  position: absolute;
  top: -24px;
  left: 0;
  font-size: 11px;
  color: #D97D54;
  opacity: 0.7;
  white-space: nowrap;
  font-style: italic;
  animation: status-pulse 1.5s infinite ease-in-out;
  pointer-events: none;
}

@keyframes status-pulse {
  0% { opacity: 0.4; transform: translateY(0.5px); }
  50% { opacity: 0.8; transform: translateY(-0.5px); }
  100% { opacity: 0.4; transform: translateY(0.5px); }
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #D97D54;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* Input Area */
.agent-chat__input {
  padding: 16px;
  background: #FFFFFF;
  border-top: 1px solid #E8E4DF;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.agent-chat__input textarea {
  flex: 1;
  background: #FAF8F5;
  border: 1px solid #E8E4DF;
  border-radius: 12px;
  padding: 12px 16px;
  color: #2D2A26;
  font-size: 14px;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  line-height: 1.5;
  transition: border-color 0.15s;
}

.agent-chat__input textarea::placeholder {
  color: #9CA3AF;
}

.agent-chat__input textarea:focus {
  outline: none;
  border-color: #D97D54;
}

.send-button {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #D97D54;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  background: #C46A45;
}

.send-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-button svg {
  width: 18px;
  height: 18px;
  color: white;
}

/* Scrollbar */
.agent-chat__messages::-webkit-scrollbar {
  width: 6px;
}

.agent-chat__messages::-webkit-scrollbar-track {
  background: transparent;
}

.agent-chat__messages::-webkit-scrollbar-thumb:hover {
  background: #B8B3AD;
}

/* Markdown Rendering Enhancements */
.message__text :deep(pre) {
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
  overflow-x: auto;
  border: 1px solid #e1e4e8;
}

.message__text :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 4px;
}

.message__text :deep(.hljs) {
  padding: 0;
  background: transparent;
}

.message__text :deep(.math-block) {
  margin: 16px 0;
  overflow-x: auto;
  text-align: center;
}

.message__text :deep(.math-inline) {
  padding: 0 2px;
}

.message__text :deep(.math-error) {
  color: #ef4444;
  font-family: monospace;
}
</style>
