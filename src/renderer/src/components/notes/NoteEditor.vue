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
      <div class="note-editor__content allow-select">
        <EditorContent :editor="editor" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Underline from '@tiptap/extension-underline'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { noteRepository } from '@/database/noteRepository'
import { exportService } from '@/services/exportService'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()

// 本地标题状态（用于减少渲染）
const localTitle = ref('')
const titleInputRef = ref<HTMLInputElement>()

// 保存防抖定时器
let saveTimer: ReturnType<typeof setTimeout> | null = null
let titleSaveTimer: ReturnType<typeof setTimeout> | null = null

// 当前正在编辑的笔记ID
let currentEditingId: string | null = null

// Tiptap 编辑器 - 优化配置
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3]
      },
      // 禁用历史记录以提高性能（如果不需要撤销功能可以启用）
      // history: false
    }),
    Placeholder.configure({
      placeholder: '开始写点什么...'
    }),
    TaskList,
    TaskItem.configure({
      nested: true
    }),
    Underline
  ],
  content: '',
  editable: true,
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
  }
])

// 监听当前笔记变化 - 只在切换笔记时更新编辑器
watch(
  () => noteStore.currentNote?.id,
  async (newId, oldId) => {
    if (newId !== oldId && noteStore.currentNote && editor.value) {
      currentEditingId = newId || null
      localTitle.value = noteStore.currentNote.title

      // 使用 nextTick 确保 DOM 更新完成
      await nextTick()

      // 只有内容真的不同时才更新
      const currentContent = editor.value.getHTML()
      if (currentContent !== noteStore.currentNote.content) {
        editor.value.commands.setContent(noteStore.currentNote.content || '', false)
      }

      editor.value.setEditable(noteStore.currentView !== 'trash')
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
    await noteRepository.update(noteStore.currentNote.id, { title: localTitle.value })
    await noteStore.loadNotes()
  }
}

// 处理分类变化
async function handleCategoryChange(event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement
  if (noteStore.currentNote) {
    await noteRepository.update(noteStore.currentNote.id, {
      categoryId: select.value || null
    })
    await noteStore.loadNotes()
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
  will-change: contents;
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
  transition: all 0.1s ease;

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
      padding-left: $spacing-lg;
      margin-bottom: $spacing-sm;
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

    code {
      background: $color-bg-secondary;
      padding: 2px 6px;
      border-radius: $radius-sm;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.9em;
      color: $color-text-primary;
    }

    blockquote {
      border-left: 3px solid $color-border-dark;
      padding-left: $spacing-md;
      margin: $spacing-md 0;
      color: $color-text-secondary;
      font-style: italic;
    }

    .is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: $color-text-placeholder;
      pointer-events: none;
      height: 0;
    }
  }
}
</style>
