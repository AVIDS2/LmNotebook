<template>
  <div class="note-editor">
    <!-- 无笔记状态 -->
    <div v-if="!noteStore.currentNote" class="note-editor__empty">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <rect x="12" y="8" width="40" height="48" rx="4" stroke="currentColor" stroke-width="2"/>
        <path d="M22 22H42M22 32H38M22 42H34" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>选择一篇笔记或创建新笔记</p>
    </div>

    <!-- 编辑器 -->
    <template v-else>
      <!-- 工具栏 -->
      <div class="note-editor__toolbar">
        <div class="note-editor__tools">
          <button
            v-for="tool in textTools"
            :key="tool.name"
            class="note-editor__tool"
            :class="{ 'note-editor__tool--active': tool.isActive?.() }"
            :title="tool.title"
            @click="tool.action"
          >
            <span v-html="tool.icon"></span>
          </button>
        </div>

        <div class="note-editor__actions">
          <!-- 分类选择 -->
          <div class="note-editor__category-select">
            <select
              :value="noteStore.currentNote.categoryId || ''"
              @change="handleCategoryChange"
            >
              <option value="">无分类</option>
              <option
                v-for="cat in categoryStore.categories"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>

          <!-- 导出 Markdown -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            title="导出为 Markdown"
            @click="handleExportCurrentMarkdown"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 3H11L14 6V15H4V3Z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11 3V6H14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M6 9H12M6 12H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
 
          <!-- Markdown 渲染按钮 -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            title="渲染 Markdown 内容"
            @click="handleRenderMarkdown"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 5H15M3 9H15M3 13H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M13 11L15 13L13 15" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
 
          <!-- 置顶按钮 -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            :class="{ 'note-editor__tool--active': noteStore.currentNote.isPinned }"
            title="置顶"
            @click="handleTogglePin"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2L10.5 6.5L15 7L11.5 10L12.5 15L9 12.5L5.5 15L6.5 10L3 7L7.5 6.5L9 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" :fill="noteStore.currentNote.isPinned ? 'currentColor' : 'none'"/>
            </svg>
          </button>

          <!-- 删除/恢复按钮 -->
          <button
            v-if="noteStore.currentView === 'trash'"
            class="note-editor__tool"
            title="恢复"
            @click="handleRestore"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9C3 5.68629 5.68629 3 9 3C11.2091 3 13.1204 4.26324 14.0583 6.10811" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M15 9C15 12.3137 12.3137 15 9 15C6.79086 15 4.87961 13.7368 3.94173 11.8919" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M14 3V6H11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M4 15V12H7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>

          <button
            class="note-editor__tool note-editor__tool--danger"
            :title="noteStore.currentView === 'trash' ? '永久删除' : '删除'"
            @click="handleDelete"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 5H15M6 5V4C6 3.44772 6.44772 3 7 3H11C11.5523 3 12 3.44772 12 4V5M14 5V14C14 14.5523 13.5523 15 13 15H5C4.44772 15 4 14.5523 4 14V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 标题输入 -->
      <input
        ref="titleInputRef"
        :value="localTitle"
        class="note-editor__title"
        type="text"
        placeholder="标题"
        :readonly="noteStore.currentView === 'trash'"
        @input="handleTitleInput"
        @blur="handleTitleBlur"
      />

      <!-- 富文本编辑器 -->
      <div class="note-editor__content allow-select" ref="editorContainerRef">
        <EditorContent :editor="editor" />
        
        <!-- 图片调整手柄 -->
        <div 
          v-if="selectedImage" 
          class="image-resize-handle"
          :style="resizeHandleStyle"
          @mousedown="startResize"
        ></div>
      </div>
    </template>
  </div>
  
  <!-- 图片右键菜单 -->
  <div 
    v-if="imageContextMenu.visible" 
    class="image-context-menu"
    :style="{ left: imageContextMenu.x + 'px', top: imageContextMenu.y + 'px' }"
  >
    <div class="menu-item" @click="setImageSize('30%')">小图 (30%)</div>
    <div class="menu-item" @click="setImageSize('50%')">中图 (50%)</div>
    <div class="menu-item" @click="setImageSize('70%')">大图 (70%)</div>
    <div class="menu-item" @click="setImageSize('100%')">全宽 (100%)</div>
    <div class="menu-divider"></div>
    <div class="menu-item" @click="setImageAlign('left')">居左对齐</div>
    <div class="menu-item" @click="setImageAlign('center')">居中对齐</div>
    <div class="menu-item" @click="setImageAlign('right')">居右对齐</div>
    <div class="menu-divider"></div>
    <div class="menu-item danger" @click="deleteImage">删除图片</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount, onMounted, computed, nextTick, reactive, inject } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import History from '@tiptap/extension-history'
import Placeholder from '@tiptap/extension-placeholder'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Underline from '@tiptap/extension-underline'
import Table from '@tiptap/extension-table'
import { NodeSelection } from '@tiptap/pm/state'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Image from '@tiptap/extension-image'
import { Mathematics } from '@/extensions/Mathematics'
import 'katex/dist/katex.min.css'
import katex from 'katex'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { common, createLowlight } from 'lowlight'
import DOMPurify from 'dompurify'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { noteRepository } from '@/database/noteRepository'
import { exportService } from '@/services/exportService'

const lowlight = createLowlight(common)

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()

// Register AI format brush action
const registerEditorAction = inject<(fn: (html: string) => void) => void>('registerEditorAction')
if (registerEditorAction) {
  registerEditorAction((html: string) => {
    if (editor.value) {
      console.log('🔮 AI Applying new content to editor...')
      editor.value.commands.setContent(html, true)
    }
  })
}

// 本地标题状态（用于减少渲染）
const localTitle = ref('')
const titleInputRef = ref<HTMLInputElement>()
const editorContainerRef = ref<HTMLElement>()

// 保存防抖定时器
let saveTimer: ReturnType<typeof setTimeout> | null = null
let titleSaveTimer: ReturnType<typeof setTimeout> | null = null

// 当前正在编辑的笔记ID
let currentEditingId: string | null = null

// Markdown 渲染切换状态
let isRenderedMode = false
let originalMarkdownText = ''

// 图片编辑状态
const selectedImage = ref<HTMLImageElement | null>(null)
const selectedImagePos = ref<number | null>(null)
const imageContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0
})

// 调整手柄位置 - 增加对滚动条的处理
const resizeHandleStyle = computed(() => {
  if (!selectedImage.value || !editorContainerRef.value) return { display: 'none' }
  
  const img = selectedImage.value
  const container = editorContainerRef.value
  
  // 使用 offset 代替 getBoundingClientRect 以应对内部滚动
  const top = img.offsetTop + img.offsetHeight - 8
  const left = img.offsetLeft + img.offsetWidth - 8
  
  return {
    transform: `translate(${left}px, ${top}px)`,
    display: 'block'
  }
})

// Tiptap 编辑器 - 优化配置
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3]
      },
      // Disable default CodeBlock since we'll use lowlight version
      codeBlock: false,
      history: false
    }),
    CodeBlockLowlight.configure({
      lowlight,
    }),
    // 单独添加 History 扩展，方便控制
    History.configure({
      depth: 100,
      newGroupDelay: 500
    }),
    Placeholder.configure({
      placeholder: '开始写点什么...'
    }),
    TaskList,
    TaskItem.configure({
      nested: true
    }),
    Underline,
    Table.configure({
      resizable: true,
    }),
    TableRow,
    TableHeader,
    TableCell,
    Image.extend({
      addAttributes() {
        return {
          ...this.parent?.(),
          width: {
            default: '50%',
            parseHTML: element => element.getAttribute('width') || '50%',
            renderHTML: attributes => ({
              width: attributes.width,
              style: `width: ${attributes.width}; max-width: 100%; height: auto; transition: width 0.1s ease;`
            }),
          },
          align: {
            default: 'center',
            parseHTML: element => element.getAttribute('data-align') || 'center',
            renderHTML: attributes => ({
              'data-align': attributes.align,
              class: `image-align-${attributes.align}`
            }),
          }
        }
      }
    }).configure({
      allowBase64: true,
    }),
    Mathematics
  ],
  content: '',
  editable: true,
  onSelectionUpdate({ editor }) {
    const { selection } = editor.state
    if (selection instanceof NodeSelection && selection.node.type.name === 'image') {
      const dom = editor.view.nodeDOM(selection.from) as HTMLImageElement
      if (dom && dom.tagName === 'IMG') {
        selectedImage.value = dom
        selectedImagePos.value = selection.from
        return
      }
    }
    selectedImage.value = null
    selectedImagePos.value = null
  },
  // 拦截粘贴事件，支持图片、表格和纯文本
  editorProps: {
    handlePaste: (view, event) => {
      const clipboardData = event.clipboardData
      if (!clipboardData) return false

      // 1. 优先检查是否有图片
      const items = clipboardData.items
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            // 将图片转为 base64
            const reader = new FileReader()
            reader.onload = (e) => {
              const base64 = e.target?.result as string
              if (base64) {
                const node = view.state.schema.nodes.image.create({ src: base64 })
                const { tr } = view.state
                view.dispatch(tr.replaceSelectionWith(node))
              }
            }
            reader.readAsDataURL(file)
            return true
          }
        }
      }

      // 2. 检查是否有 HTML 内容（WPS/Excel 复制的表格会带 HTML）
      const html = clipboardData.getData('text/html')
      if (html && html.includes('<table')) {
        // 有表格的 HTML，让 Tiptap 默认处理
        return false
      }

      // 3. 对于纯文本或 Markdown 源码，强制以纯文本插入
      const text = clipboardData.getData('text/plain')
      if (text) {
        const { tr } = view.state
        const textNode = view.state.schema.text(text)
        view.dispatch(tr.replaceSelectionWith(textNode, false))
        return true
      }

      return false
    }
  },
  // 使用 requestAnimationFrame 优化更新
  onUpdate: ({ editor }) => {
    if (noteStore.currentNote && noteStore.currentView !== 'trash') {
      // 防抖保存 - 增加到 800ms
      if (saveTimer) {
        clearTimeout(saveTimer)
      }

      saveTimer = setTimeout(async () => {
        const content = editor.getHTML()
        // 直接调用 repository 避免触发 store 的重新加载
        await noteRepository.update(noteStore.currentNote!.id, { content })
      }, 800)
    }
  }
})

// 工具栏按钮 - 使用 shallowRef 减少响应式开销
const textTools = computed(() => [
  {
    name: 'bold',
    title: '加粗',
    icon: '<strong>B</strong>',
    isActive: () => editor.value?.isActive('bold'),
    action: () => editor.value?.chain().focus().toggleBold().run()
  },
  {
    name: 'italic',
    title: '斜体',
    icon: '<em>I</em>',
    isActive: () => editor.value?.isActive('italic'),
    action: () => editor.value?.chain().focus().toggleItalic().run()
  },
  {
    name: 'underline',
    title: '下划线',
    icon: '<u>U</u>',
    isActive: () => editor.value?.isActive('underline'),
    action: () => editor.value?.chain().focus().toggleUnderline().run()
  },
  {
    name: 'strike',
    title: '删除线',
    icon: '<s>S</s>',
    isActive: () => editor.value?.isActive('strike'),
    action: () => editor.value?.chain().focus().toggleStrike().run()
  },
  {
    name: 'h1',
    title: '标题1',
    icon: 'H1',
    isActive: () => editor.value?.isActive('heading', { level: 1 }),
    action: () => editor.value?.chain().focus().toggleHeading({ level: 1 }).run()
  },
  {
    name: 'h2',
    title: '标题2',
    icon: 'H2',
    isActive: () => editor.value?.isActive('heading', { level: 2 }),
    action: () => editor.value?.chain().focus().toggleHeading({ level: 2 }).run()
  },
  {
    name: 'bulletList',
    title: '无序列表',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><circle cx="3" cy="4" r="1.5" fill="currentColor"/><circle cx="3" cy="8" r="1.5" fill="currentColor"/><circle cx="3" cy="12" r="1.5" fill="currentColor"/><line x1="6" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>',
    isActive: () => editor.value?.isActive('bulletList'),
    action: () => editor.value?.chain().focus().toggleBulletList().run()
  },
  {
    name: 'orderedList',
    title: '有序列表',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><text x="1" y="6" font-size="6" fill="currentColor">1</text><text x="1" y="10" font-size="6" fill="currentColor">2</text><text x="1" y="14" font-size="6" fill="currentColor">3</text><line x1="6" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>',
    isActive: () => editor.value?.isActive('orderedList'),
    action: () => editor.value?.chain().focus().toggleOrderedList().run()
  },
  {
    name: 'taskList',
    title: '任务列表',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="1" y="2" width="5" height="5" rx="1" stroke="currentColor" fill="none"/><path d="M2.5 4.5L3.5 5.5L5.5 3" stroke="currentColor" stroke-width="1"/><rect x="1" y="9" width="5" height="5" rx="1" stroke="currentColor" fill="none"/><line x1="8" y1="4.5" x2="14" y2="4.5" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="11.5" x2="14" y2="11.5" stroke="currentColor" stroke-width="1.5"/></svg>',
    isActive: () => editor.value?.isActive('taskList'),
    action: () => editor.value?.chain().focus().toggleTaskList().run()
  },
  {
    name: 'code',
    title: '代码',
    icon: '&lt;/&gt;',
    isActive: () => editor.value?.isActive('code'),
    action: () => editor.value?.chain().focus().toggleCode().run()
  },
  {
    name: 'blockquote',
    title: '引用',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 4C2.5 4 2 5 2 6.5C2 8 2.5 9 4 9C5.5 9 6 8 6 6.5C6 4 4 11 4 11" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M11 4C9.5 4 9 5 9 6.5C9 8 9.5 9 11 9C12.5 9 13 8 13 6.5C13 4 11 11 11 11" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>',
    isActive: () => editor.value?.isActive('blockquote'),
    action: () => editor.value?.chain().focus().toggleBlockquote().run()
  },
  {
    name: 'table',
    title: '插入表格',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="2" y1="7" x2="14" y2="7" stroke="currentColor"/><line x1="7" y1="2" x2="7" y2="14" stroke="currentColor"/></svg>',
    action: () => editor.value?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  },
  {
    name: 'deleteTable',
    title: '删除表格',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="2" y1="7" x2="14" y2="7" stroke="currentColor"/><line x1="7" y1="2" x2="7" y2="14" stroke="currentColor"/><line x1="4" y1="4" x2="12" y2="12" stroke="#e74c3c" stroke-width="1.5"/><line x1="12" y1="4" x2="4" y2="12" stroke="#e74c3c" stroke-width="1.5"/></svg>',
    action: () => editor.value?.chain().focus().deleteTable().run()
  },
  {
    name: 'image',
    title: '插入图片',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" rx="1" stroke="currentColor" fill="none"/><circle cx="5" cy="6" r="1.5" fill="currentColor"/><path d="M2 11L5 8L8 11L11 7L14 10" stroke="currentColor" stroke-width="1" fill="none"/></svg>',
    action: () => {
      // 创建隐藏的文件输入
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (event) => {
            const base64 = event.target?.result as string
            if (base64) {
              editor.value?.chain().focus().setImage({ src: base64 }).run()
            }
          }
          reader.readAsDataURL(file)
        }
      }
      input.click()
    }
  },
  {
    name: 'math',
    title: '插入公式 (LaTeX)',
    icon: '<svg width="16" height="16" viewBox="0 0 16 16"><text x="2" y="12" font-size="10" font-style="italic" fill="currentColor">∑</text><text x="9" y="8" font-size="6" fill="currentColor">x²</text></svg>',
    action: () => {
      const latex = prompt('输入 LaTeX 公式:', 'E=mc^2')
      if (latex !== null) {
        const isBlock = confirm('是否作为独立行(Block)显示？')
        editor.value?.chain().focus().insertMath(latex, isBlock).run()
      }
    }
  }
])

// ========== 图片编辑功能 ==========

// 设置图片对齐
function setImageAlign(align: 'left' | 'center' | 'right'): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .updateAttributes('image', { align })
    .run()
  
  imageContextMenu.visible = false
  // 强制重新计算手柄位置
  nextTick(() => {
    if (selectedImagePos.value !== null) {
      const dom = editor.value?.view.nodeDOM(selectedImagePos.value) as HTMLImageElement
      if (dom) selectedImage.value = dom
    }
  })
}

// 设置图片大小
function setImageSize(size: string): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .updateAttributes('image', { width: size })
    .run()
  
  imageContextMenu.visible = false
  selectedImage.value = null
  selectedImagePos.value = null
}

// 删除图片
function deleteImage(): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .deleteSelection()
    .run()
  
  imageContextMenu.visible = false
  selectedImage.value = null
  selectedImagePos.value = null
}

// 开始拖拽调整大小
let isResizing = false
let resizeStartX = 0
let resizeStartWidth = 0

function startResize(e: MouseEvent): void {
  if (!selectedImage.value || !editor.value) return
  
  e.preventDefault()
  e.stopPropagation()
  
  isResizing = true
  resizeStartX = e.clientX
  resizeStartWidth = selectedImage.value.offsetWidth
  
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

function onResize(e: MouseEvent): void {
  if (!isResizing || !selectedImage.value || !editorContainerRef.value) return
  
  const containerWidth = editorContainerRef.value.offsetWidth
  const delta = e.clientX - resizeStartX
  const newWidth = Math.max(100, Math.min(resizeStartWidth + delta, containerWidth))
  const widthPercent = Math.round((newWidth / containerWidth) * 100)
  
  selectedImage.value.style.width = widthPercent + '%'
}

function stopResize(): void {
  if (!isResizing || !selectedImage.value || !editor.value || selectedImagePos.value === null) {
    isResizing = false
    return
  }
  
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  
  // 保存新的宽度到编辑器
  const newWidth = selectedImage.value.style.width || '50%'
  editor.value.chain()
    .setNodeSelection(selectedImagePos.value)
    .updateAttributes('image', { width: newWidth })
    .run()
}

// 监听编辑器中的图片点击和右键事件
const attachImageListeners = (container: HTMLElement) => {
  // 点击图片选中
  container.addEventListener('click', (e: MouseEvent) => {
    const target = e.target as HTMLElement
    imageContextMenu.visible = false
    
    if (target.tagName === 'IMG') {
      selectedImage.value = target as HTMLImageElement
      if (editor.value) {
        const pos = editor.value.view.posAtDOM(target, 0)
        selectedImagePos.value = pos
        editor.value.chain().focus().setNodeSelection(pos).run()
      }
    } else {
      selectedImage.value = null
      selectedImagePos.value = null
    }
  })
  
  // 右键菜单
  container.addEventListener('contextmenu', (e: MouseEvent) => {
    const target = e.target as HTMLElement
    if (target.tagName === 'IMG') {
      e.preventDefault()
      selectedImage.value = target as HTMLImageElement
      if (editor.value) {
        const pos = editor.value.view.posAtDOM(target, 0)
        selectedImagePos.value = pos
      }
      imageContextMenu.x = e.clientX
      imageContextMenu.y = e.clientY
      imageContextMenu.visible = true
    }
  })
}

// 监听容器 DOM 变化，当笔记切换显现后绑定事件
watch(editorContainerRef, (newVal) => {
  if (newVal) {
    attachImageListeners(newVal)
  }
})

onMounted(() => {
  // 全局点击关闭右键菜单
  document.addEventListener('click', () => {
    imageContextMenu.visible = false
  })
})

// 渲染/源码 切换
async function handleRenderMarkdown(): Promise<void> {
  if (!editor.value) return
  
  const { from, to, empty } = editor.value.state.selection
  
  // 检测是否有选中文本（部分渲染不参与切换逻辑）
  if (!empty) {
    // 部分渲染：只渲染选中的文本
    const selectedText = editor.value.state.doc.textBetween(from, to, '\n')
    
    if (!selectedText.trim()) return
    
    // 检测选中文本是否包含 Markdown 语法 (包括数学公式 $)
    const hasMarkdownSyntax = /#{1,6}\s|\*\*|\*\s|^\d+\.\s|\|.*\||\$|`/m.test(selectedText)
    if (!hasMarkdownSyntax) {
      alert('选中的文本未检测到 Markdown 语法。')
      return
    }
    
    // 渲染选中部分
    const rawHtml = await marked.parse(selectedText, {
      gfm: true,
      breaks: true
    })
    const cleanHtml = DOMPurify.sanitize(rawHtml)
    
    // 替换选中内容
    editor.value.chain().focus().deleteSelection().insertContent(cleanHtml).run()
    return
  }
  
  // 整体切换逻辑
  if (isRenderedMode) {
    // 当前是渲染态 -> 切换回原始 Markdown
    if (originalMarkdownText) {
      // 将纯文本 Markdown 作为文本插入（保留 ## ** 等符号）
      editor.value.chain()
        .clearContent()
        .insertContent(originalMarkdownText)
        .focus()
        .run()
      isRenderedMode = false
      
      // 确保编辑器可编辑
      editor.value.setEditable(true)
    }
    return
  }
  
  // 当前是源码态 -> 切换到渲染态
  const markdownSource = editor.value.getText({ blockSeparator: '\n' })
  if (!markdownSource.trim()) return

  // 保存原始 Markdown 纯文本
  originalMarkdownText = markdownSource

  // 1. Pre-process math patterns: Shield them with custom tags that our extension understands
  let processedText = markdownSource.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    // Escape quotes in formula for HTML attribute
    const escapedFormula = formula.replace(/"/g, '&quot;')
    return `<div data-math="true" data-latex="${escapedFormula}" data-display="true"></div>`
  })
  processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    const escapedFormula = formula.replace(/"/g, '&quot;')
    return `<span data-math="true" data-latex="${escapedFormula}"></span>`
  })

  // 2. Configure marked for highlighting
  const renderer = new marked.Renderer()
  renderer.code = function({ text, lang }) {
    const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
    const highlighted = hljs.highlight(text, { language }).value
    return `<pre class="hljs-container"><code class="hljs language-${language}">${highlighted}</code></pre>`
  }

  // 3. Render Markdown
  // Important: We need to allow our custom tags through
  let html = (await marked.parse(processedText, { renderer, async: false, breaks: true, gfm: true })) as string

  // 使用 DOMPurify 清洗 HTML 并注入编辑器
  // 注意：我们需要允许 data-attributes
  const cleanHtml = DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-math', 'data-latex', 'data-display', 'contenteditable']
  })
  
  editor.value.chain().setContent(cleanHtml, true).focus().run()
  editor.value.setEditable(true)
  isRenderedMode = true
}

// 监听当前笔记变化 - 只在切换笔记时更新编辑器
watch(
  () => noteStore.currentNote?.id,
  async (newId, oldId) => {
    // 等待编辑器准备好
    if (!editor.value) {
      // 如果编辑器还没准备好，等待一小段时间后重试
      await new Promise(resolve => setTimeout(resolve, 50))
      if (!editor.value) return
    }
    
    if (noteStore.currentNote) {
      currentEditingId = newId || null
      localTitle.value = noteStore.currentNote.title
      
      // 重置渲染状态
      isRenderedMode = false
      originalMarkdownText = ''

      // 切换笔记时设置内容
      let newContent = noteStore.currentNote.content || ''
      
      // 自动识别并转换数学公式
      newContent = newContent.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        const escaped = formula.replace(/"/g, '&quot;')
        return `<div data-math="true" data-latex="${escaped}" data-display="true"></div>`
      })
      newContent = newContent.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        const escaped = formula.replace(/"/g, '&quot;')
        return `<span data-math="true" data-latex="${escaped}"></span>`
      })
      
      // 只在切换笔记时重置历史
      if (newId !== oldId) {
        const { state, view } = editor.value
        const tr = state.tr.setMeta('addToHistory', false)
        view.dispatch(tr)
      }
      
      editor.value.commands.setContent(newContent, false, { preserveWhitespace: 'full' })

      // 设置可编辑状态
      const isTrash = noteStore.currentView === 'trash'
      editor.value.setEditable(!isTrash)
    }
  },
  { immediate: true }
)

// 同步本地标题
watch(
  () => noteStore.currentNote?.title,
  (newTitle) => {
    if (newTitle !== undefined && document.activeElement !== titleInputRef.value) {
      localTitle.value = newTitle
    }
  }
)

// 处理标题输入 - 使用本地状态
function handleTitleInput(event: Event): void {
  const input = event.target as HTMLInputElement
  localTitle.value = input.value

  // 防抖保存标题
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
  }

  titleSaveTimer = setTimeout(async () => {
    if (noteStore.currentNote) {
      await noteRepository.update(noteStore.currentNote.id, { title: localTitle.value })
    }
  }, 500)
}

// 失去焦点时立即保存
async function handleTitleBlur(): Promise<void> {
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
    titleSaveTimer = null
  }
  if (noteStore.currentNote && localTitle.value !== noteStore.currentNote.title) {
    await noteStore.updateNote(noteStore.currentNote.id, { title: localTitle.value })
  }
}

// 处理分类变化
async function handleCategoryChange(event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement
  if (noteStore.currentNote) {
    await noteStore.updateNote(noteStore.currentNote.id, {
      categoryId: select.value || null
    })
  }
}

// 切换置顶
function handleTogglePin(): void {
  if (noteStore.currentNote) {
    noteStore.togglePin(noteStore.currentNote.id)
  }
}

// 删除笔记
function handleDelete(): void {
  if (noteStore.currentNote) {
    if (noteStore.currentView === 'trash') {
      if (confirm('确定要永久删除这篇笔记吗？此操作不可恢复。')) {
        noteStore.permanentDeleteNote(noteStore.currentNote.id)
      }
    } else {
      noteStore.deleteNote(noteStore.currentNote.id)
    }
  }
}

// 恢复笔记
function handleRestore(): void {
  if (noteStore.currentNote) {
    noteStore.restoreNote(noteStore.currentNote.id)
  }
}

// 导出当前笔记为 Markdown
async function handleExportCurrentMarkdown(): Promise<void> {
  if (noteStore.currentNote) {
    await exportService.exportNoteAsMarkdown(noteStore.currentNote)
  }
}

onBeforeUnmount(() => {
  editor.value?.destroy()
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
  }
})
</script>

<style lang="scss" scoped>
.note-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: $color-bg-card;
  overflow: hidden;
}

.note-editor__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $color-text-muted;

  svg {
    margin-bottom: $spacing-md;
    opacity: 0.4;
  }

  p {
    font-size: $font-size-md;
  }
}

.note-editor__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid $color-border-light;
  background: $color-bg-primary;
  flex-shrink: 0;
}

.note-editor__tools {
  display: flex;
  gap: 2px;
}

.note-editor__tool {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: $radius-sm;
  background: transparent;
  color: $color-text-secondary;
  font-size: $font-size-sm;
  cursor: pointer;
  transition: background-color 0.1s ease, color 0.1s ease, border-color 0.1s ease;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
  }

  &--active {
    border-color: $color-border-dark;
    background: $color-bg-card;
    color: $color-text-primary;
  }

  &--danger:hover {
    background: rgba($color-danger, 0.1);
    color: $color-danger;
  }
}

.note-editor__actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.note-editor__category-select {
  select {
    padding: $spacing-xs $spacing-sm;
    border: 1px solid $color-border;
    border-radius: $radius-sm;
    background: $color-bg-card;
    font-size: $font-size-xs;
    color: $color-text-secondary;
    cursor: pointer;
    outline: none;

    &:focus {
      border-color: $color-primary;
    }
  }
}

.note-editor__title {
  padding: $spacing-md $spacing-lg;
  border: none;
  background: transparent;
  font-size: $font-size-2xl;
  font-weight: 600;
  color: $color-text-primary;
  outline: none;
  flex-shrink: 0;

  &::placeholder {
    color: $color-text-placeholder;
  }
}

.note-editor__content {
  flex: 1;
  padding: 0 $spacing-lg $spacing-lg;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;

  :deep(.tiptap) {
    outline: none;
    min-height: 100%;
    font-size: $font-size-md;
    line-height: 1.75;
    color: $color-text-primary;

    p {
      margin-bottom: $spacing-sm;
    }

    h1, h2, h3 {
      margin-top: $spacing-lg;
      margin-bottom: $spacing-sm;
      font-weight: 600;
      color: $color-text-primary;
    }

    h1 { font-size: $font-size-2xl; }
    h2 { font-size: $font-size-xl; }
    h3 { font-size: $font-size-lg; }

    ul, ol {
      padding-left: $spacing-xl;
      margin-bottom: $spacing-sm;
      
      li {
        margin-bottom: $spacing-xs;
        list-style-position: outside;
      }
    }

    ul {
      list-style-type: disc;
    }

    ol {
      list-style-type: decimal;
    }

    ul[data-type="taskList"] {
      list-style: none;
      padding-left: 0;

      li {
        display: flex;
        align-items: flex-start;
        gap: $spacing-sm;

        > label {
          flex-shrink: 0;
          margin-top: 3px;

          input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: $color-primary;
          }
        }

        > div {
          flex: 1;
        }

        &[data-checked="true"] > div {
          text-decoration: line-through;
          color: $color-text-muted;
        }
      }
    }

    pre {
      background: #f6f8fa;
      border-radius: $radius-md;
      padding: $spacing-md;
      margin: $spacing-md 0;
      overflow-x: auto;
      border: 1px solid $color-border;
      
      code {
        background: transparent;
        padding: 0;
        border-radius: 0;
        font-size: 0.9em;
        color: inherit;
      }
    }

    code {
      background: $color-bg-secondary;
      padding: 2px 6px;
      border-radius: $radius-sm;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.9em;
      color: $color-text-primary;
    }

    .math-block {
      margin: $spacing-lg 0;
      text-align: center;
      overflow-x: auto;
    }

    .math-inline {
      padding: 0 2px;
    }

    .hljs-container {
      position: relative;
    }

    blockquote {
      border-left: 3px solid $color-border-dark;
      padding-left: $spacing-md;
      margin: $spacing-md 0;
      color: $color-text-secondary;
      font-style: italic;
    }

    table {
      border-collapse: collapse;
      table-layout: auto;
      width: 100%;
      margin: $spacing-md 0;
      overflow: hidden;
      border: 1px solid $color-border;
      border-radius: $radius-sm;

      td, th {
        min-width: 1em;
        border: 1px solid $color-border-light;
        padding: 8px 12px;
        vertical-align: middle;
        box-sizing: border-box;
        position: relative;
        text-align: left;

        > * {
          margin-bottom: 0;
        }
      }

      th {
        font-weight: 600;
        background-color: $color-bg-secondary;
        color: $color-text-primary;
        border-bottom: 2px solid $color-border;
      }

      tr:nth-child(even) {
        background-color: rgba($color-bg-secondary, 0.3);
      }

      tr:hover {
        background-color: rgba($color-primary, 0.05);
      }

      .selectedCell:after {
        z-index: 2;
        position: absolute;
        content: "";
        left: 0; right: 0; top: 0; bottom: 0;
        background: rgba(200, 200, 255, 0.4);
        pointer-events: none;
      }

      .column-resize-handle {
        position: absolute;
        right: -2px;
        top: 0;
        bottom: -2px;
        width: 4px;
        background-color: #adf;
        pointer-events: none;
      }
    }

    img {
      max-width: 100%;
      height: auto;
      border-radius: $radius-sm;
      margin: $spacing-md auto;
      display: block;

      &.ProseMirror-selectednode {
        outline: 3px solid $color-primary;
        box-shadow: 0 0 15px rgba($color-primary, 0.3);
      }

      // 对齐逻辑
      &.image-align-left {
        margin-left: 0;
        margin-right: auto;
      }

      &.image-align-center {
        margin-left: auto;
        margin-right: auto;
      }

      &.image-align-right {
        margin-left: auto;
        margin-right: 0;
      }
    }

    // 数学公式样式
    .math-node {
      display: inline-block;
      padding: 2px 6px;
      margin: 0 2px;
      background: rgba($color-primary, 0.08);
      border-radius: $radius-sm;
      cursor: pointer;
      transition: background $transition-fast;

      &:hover {
        background: rgba($color-primary, 0.15);
      }

      &.ProseMirror-selectednode {
        outline: 2px solid $color-primary;
        outline-offset: 2px;
      }
    }

    .math-placeholder {
      color: $color-text-muted;
      font-style: italic;
    }

    .math-error {
      color: $color-danger;
      font-family: monospace;
    }

    .is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: $color-text-placeholder;
      pointer-events: none;
      height: 0;
    }
  }
  
  // 图片调整手柄
  .image-resize-handle {
    position: absolute;
    width: 16px;
    height: 16px;
    background: $color-primary;
    border-radius: 50%;
    cursor: se-resize;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    
    &:hover {
      transform: scale(1.2);
    }
  }
}

// 图片右键菜单（全局定位）
.image-context-menu {
  position: fixed;
  background: $color-bg-secondary;
  border: 1px solid $color-border;
  border-radius: $radius-md;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: $spacing-xs 0;
  z-index: 9999;
  min-width: 120px;
  
  .menu-item {
    padding: $spacing-sm $spacing-md;
    cursor: pointer;
    font-size: 13px;
    color: $color-text-primary;
    
    &:hover {
      background: $color-bg-hover;
    }
    
    &.danger {
      color: $color-danger;
    }
  }
  
  .menu-divider {
    height: 1px;
    background: $color-border;
    margin: $spacing-xs 0;
  }
}
</style>

