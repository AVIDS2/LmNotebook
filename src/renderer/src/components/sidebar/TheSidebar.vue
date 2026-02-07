<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <!-- 收缩按钮 -->
    <button class="sidebar__toggle" @click="$emit('toggle')" :title="collapsed ? '展开' : '收起'">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" :style="{ transform: collapsed ? 'rotate(180deg)' : '' }">
        <path d="M10 4L6 8L10 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- 展开状态内容 - 使用 CSS 过渡而非 v-if -->
    <div class="sidebar__expanded-content" :class="{ 'sidebar__expanded-content--hidden': collapsed }">
      <!-- 新建笔记按钮 -->
      <button class="sidebar__new-btn" @click="handleNewNote" :tabindex="collapsed ? -1 : 0">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>新建笔记</span>
      </button>

      <!-- 导航菜单 -->
      <nav class="sidebar__nav">
        <div
          class="sidebar__item"
          :class="{ 'sidebar__item--active': noteStore.currentView === 'all' }"
          @click="noteStore.setView('all')"
          :tabindex="collapsed ? -1 : 0"
        >
          <svg class="sidebar__icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M5 6H13M5 9H13M5 12H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          <span>全部笔记</span>
          <span class="sidebar__count">{{ allNotesCount }}</span>
        </div>

        <div
          class="sidebar__item"
          :class="{ 'sidebar__item--active': noteStore.currentView === 'pinned' }"
          @click="noteStore.setView('pinned')"
          :tabindex="collapsed ? -1 : 0"
        >
          <svg class="sidebar__icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 2L10.5 6.5L15 7L11.5 10L12.5 15L9 12.5L5.5 15L6.5 10L3 7L7.5 6.5L9 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          </svg>
          <span>置顶笔记</span>
        </div>
      </nav>

      <!-- 分类 -->
      <div class="sidebar__section">
        <div class="sidebar__section-header">
          <span>分类</span>
          <button class="sidebar__add-btn" @click="showAddCategory = true" :tabindex="collapsed ? -1 : 0">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2V12M2 7H12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="sidebar__categories">
          <div
            v-for="category in categoryStore.categories"
            :key="category.id"
            class="sidebar__item sidebar__item--category"
            :class="{
              'sidebar__item--active': noteStore.currentView === 'category' && noteStore.currentCategoryId === category.id,
              'sidebar__item--dragging': draggedCategoryId === category.id,
              'sidebar__item--dragover': dragOverCategoryId === category.id
            }"
            draggable="true"
            @click="editingCategoryId !== category.id && noteStore.setView('category', category.id)"
            @dragstart="handleDragStart(category.id)"
            @dragover="handleDragOver($event, category.id)"
            @dragleave="handleDragLeave"
            @drop="handleDrop(category.id)"
            @dragend="handleDragEnd"
            :tabindex="collapsed ? -1 : 0"
          >
            <span class="sidebar__dot" :style="{ background: category.color }"></span>
            <input
              v-if="editingCategoryId === category.id"
              v-model="editingCategoryName"
              class="sidebar__category-input"
              @click.stop
              @keyup.enter="confirmRenameCategory"
              @keyup.escape="cancelRenameCategory"
              @blur="confirmRenameCategory"
              autofocus
            />
            <span v-else class="sidebar__category-name">{{ category.name }}</span>
            <button 
              v-if="editingCategoryId !== category.id"
              class="sidebar__more-btn"
              @click.stop="toggleCategoryMenu(category.id, $event)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="2"/>
                <circle cx="12" cy="12" r="2"/>
                <circle cx="12" cy="19" r="2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部 -->
      <div class="sidebar__footer">
        <div
          class="sidebar__item"
          :class="{ 'sidebar__item--active': noteStore.currentView === 'trash' }"
          @click="noteStore.setView('trash')"
          :tabindex="collapsed ? -1 : 0"
        >
          <svg class="sidebar__icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M3 5H15M6 5V4C6 3.44772 6.44772 3 7 3H11C11.5523 3 12 3.44772 12 4V5M14 5V14C14 14.5523 13.5523 15 13 15H5C4.44772 15 4 14.5523 4 14V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span>回收站</span>
        </div>

        <div class="sidebar__footer-actions">
          <button class="sidebar__footer-btn" @click="handleExportBackup" :tabindex="collapsed ? -1 : 0">导出备份</button>
          <button class="sidebar__footer-btn" @click="handleImportBackup" :tabindex="collapsed ? -1 : 0">导入备份</button>
          <button class="sidebar__footer-btn" @click="handleExportAllMarkdown" :tabindex="collapsed ? -1 : 0">导出全部 MD</button>
          <button class="sidebar__footer-btn sidebar__footer-btn--settings" @click="showDataSettings = true" :tabindex="collapsed ? -1 : 0">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 9C8.10457 9 9 8.10457 9 7C9 5.89543 8.10457 5 7 5C5.89543 5 5 5.89543 5 7C5 8.10457 5.89543 9 7 9Z" stroke="currentColor" stroke-width="1.2"/>
              <path d="M11.4 8.4C11.3 8.6 11.3 8.9 11.4 9.1L12.1 10.1C12.2 10.2 12.2 10.4 12.1 10.5L11.1 12.2C11 12.3 10.8 12.4 10.7 12.3L9.5 11.9C9.3 11.8 9 11.8 8.8 11.9L8.5 12C8.3 12.1 8.1 12.3 8 12.5L7.8 13.8C7.8 13.9 7.7 14 7.5 14H5.5C5.3 14 5.2 13.9 5.2 13.8L5 12.5C4.9 12.3 4.7 12.1 4.5 12L4.2 11.9C4 11.8 3.7 11.8 3.5 11.9L2.3 12.3C2.2 12.4 2 12.3 1.9 12.2L0.9 10.5C0.8 10.4 0.8 10.2 0.9 10.1L1.6 9.1C1.7 8.9 1.7 8.6 1.6 8.4L1.5 8.1C1.4 7.9 1.2 7.7 1 7.6L0.2 7.2C0.1 7.2 0 7.1 0 6.9V5.1C0 4.9 0.1 4.8 0.2 4.8L1 4.4C1.2 4.3 1.4 4.1 1.5 3.9L1.6 3.6C1.7 3.4 1.7 3.1 1.6 2.9L0.9 1.9C0.8 1.8 0.8 1.6 0.9 1.5L1.9 0.8C2 0.7 2.2 0.6 2.3 0.7L3.5 1.1C3.7 1.2 4 1.2 4.2 1.1L4.5 1C4.7 0.9 4.9 0.7 5 0.5L5.2 0.2C5.2 0.1 5.3 0 5.5 0H7.5C7.7 0 7.8 0.1 7.8 0.2L8 0.5C8.1 0.7 8.3 0.9 8.5 1L8.8 1.1C9 1.2 9.3 1.2 9.5 1.1L10.7 0.7C10.8 0.6 11 0.7 11.1 0.8L12.1 1.5C12.2 1.6 12.2 1.8 12.1 1.9L11.4 2.9C11.3 3.1 11.3 3.4 11.4 3.6L11.5 3.9C11.6 4.1 11.8 4.3 12 4.4L12.8 4.8C12.9 4.8 13 4.9 13 5.1V6.9C13 7.1 12.9 7.2 12.8 7.2L12 7.6C11.8 7.7 11.6 7.9 11.5 8.1L11.4 8.4Z" stroke="currentColor" stroke-width="1.2"/>
            </svg>
            数据设置
          </button>
        </div>
        
        <!-- 主题切换 -->
        <button class="sidebar__theme-btn" @click="uiStore.toggleTheme" :tabindex="collapsed ? -1 : 0" :title="themeToggleTitle">
          <svg v-if="uiStore.theme === 'light'" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="4" stroke="currentColor" stroke-width="1.3"/>
            <path d="M9 2V4M9 14V16M2 9H4M14 9H16M4.22 4.22L5.64 5.64M12.36 12.36L13.78 13.78M4.22 13.78L5.64 12.36M12.36 5.64L13.78 4.22" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <svg v-else-if="uiStore.theme === 'classic'" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="3" y="3" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M3 9H15" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M15 10.5A6 6 0 017.5 3a6 6 0 108 7.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ themeButtonLabel }}</span>
        </button>
      </div>
    </div>

    <!-- 收缩状态下的图标 - 使用 CSS 过渡 -->
    <div class="sidebar__collapsed-content" :class="{ 'sidebar__collapsed-content--visible': collapsed }">
      <div class="sidebar__collapsed-items">
        <!-- 新建笔记 -->
        <button class="sidebar__collapsed-btn sidebar__collapsed-btn--primary" @click="handleNewNote" title="新建笔记" :tabindex="collapsed ? 0 : -1">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        
        <!-- 全部笔记 -->
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'all' }"
          @click="noteStore.setView('all')"
          title="全部笔记"
          :tabindex="collapsed ? 0 : -1"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="3" y="3" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M6 7H14M6 10H14M6 13H11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
        </button>
        
        <!-- 置顶笔记 -->
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'pinned' }"
          @click="noteStore.setView('pinned')"
          title="置顶笔记"
          :tabindex="collapsed ? 0 : -1"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 3L11.5 7.5L16 8L12.5 11L13.5 16L10 13.5L6.5 16L7.5 11L4 8L8.5 7.5L10 3Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          </svg>
        </button>
        
        <!-- 分隔线 -->
        <div class="sidebar__collapsed-divider"></div>
        
        <!-- 分类列表 -->
        <div
          v-for="category in categoryStore.categories"
          :key="category.id"
          class="sidebar__collapsed-category"
          :class="{ 'sidebar__collapsed-category--active': noteStore.currentView === 'category' && noteStore.currentCategoryId === category.id }"
          :style="{ '--category-color': category.color }"
          @click="noteStore.setView('category', category.id)"
          :tabindex="collapsed ? 0 : -1"
        >
          <span class="sidebar__collapsed-letter">{{ getCategoryInitial(category.name) }}</span>
          <span class="sidebar__collapsed-tooltip">{{ category.name }}</span>
        </div>
        
        <!-- 分隔线 -->
        <div class="sidebar__collapsed-divider"></div>
        
        <!-- 回收站 -->
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'trash' }"
          @click="noteStore.setView('trash')"
          title="回收站"
          :tabindex="collapsed ? 0 : -1"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4 6H16M7 6V5C7 4.44772 7.44772 4 8 4H12C12.5523 4 13 4.44772 13 5V6M15 6V15C15 15.5523 14.5523 16 14 16H6C5.44772 16 5 15.5523 5 15V6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
        </button>
        
        <!-- 分隔线 -->
        <div class="sidebar__collapsed-divider"></div>
        
        <!-- 主题切换 -->
        <button
          class="sidebar__collapsed-btn"
          @click="uiStore.toggleTheme"
          :title="themeToggleTitle"
          :tabindex="collapsed ? 0 : -1"
        >
          <svg v-if="uiStore.theme === 'light'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="1.3"/>
            <path d="M10 2V4M10 16V18M2 10H4M16 10H18M4.93 4.93L6.34 6.34M13.66 13.66L15.07 15.07M4.93 15.07L6.34 13.66M13.66 6.34L15.07 4.93" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <svg v-else-if="uiStore.theme === 'classic'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="4" y="4" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M4 10H16" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M17 11.5A7 7 0 018.5 3a7 7 0 109 8.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 分类右键菜单 -->
    <Teleport to="body">
      <div 
        v-if="categoryContextMenu.visible" 
        class="context-menu"
        :style="{ left: categoryContextMenu.x + 'px', top: categoryContextMenu.y + 'px' }"
      >
        <div class="context-menu__item" @click="startRenameCategory">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          <span>重命名</span>
        </div>
        <div class="context-menu__item context-menu__item--danger" @click="deleteCategory">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
          <span>删除</span>
        </div>
      </div>
      <div v-if="categoryContextMenu.visible" class="context-menu-overlay" @click="hideCategoryContextMenu"></div>
    </Teleport>

    <!-- 添加分类对话框 -->
    <div v-if="showAddCategory" class="modal-overlay" @click.self="showAddCategory = false">
      <div class="modal">
        <h3 class="modal__title">新建分类</h3>
        <input
          v-model="newCategoryName"
          class="input"
          placeholder="分类名称"
          @keyup.enter="handleAddCategory"
        />
        <div class="modal__colors">
          <button
            v-for="color in categoryColors"
            :key="color"
            class="modal__color"
            :class="{ 'modal__color--active': newCategoryColor === color }"
            :style="{ background: color }"
            @click="newCategoryColor = color"
          ></button>
        </div>
        <div class="modal__actions">
          <button class="btn" @click="showAddCategory = false">取消</button>
          <button class="btn btn--primary" @click="handleAddCategory">确定</button>
        </div>
      </div>
    </div>

    <!-- 数据设置对话框 -->
    <DataSettings v-if="showDataSettings" @close="showDataSettings = false" />
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { useUIStore } from '@/stores/uiStore'
import { exportService } from '@/services/exportService'
import DataSettings from './DataSettings.vue'

defineProps<{
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
}>()

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const uiStore = useUIStore()

const showAddCategory = ref(false)
const showDataSettings = ref(false)
const newCategoryName = ref('')
const newCategoryColor = ref('#C4A882')

// 分类编辑状态
const editingCategoryId = ref<string | null>(null)
const editingCategoryName = ref('')
const categoryContextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  categoryId: ''
})

const categoryColors = [
  '#6366F1', // 靛蓝 - Indigo
  '#8B5CF6', // 紫罗兰 - Violet  
  '#EC4899', // 粉红 - Pink
  '#F59E0B', // 琥珀 - Amber
  '#10B981', // 翠绿 - Emerald
  '#06B6D4', // 青色 - Cyan
  '#F97316', // 橙色 - Orange
  '#EF4444', // 红色 - Red
]

// 获取分类名称首字母（支持中英文）
function getCategoryInitial(name: string): string {
  if (!name) return '?'
  const firstChar = name.charAt(0)
  // 如果是中文，直接返回第一个字
  if (/[\u4e00-\u9fa5]/.test(firstChar)) {
    return firstChar
  }
  // 英文返回大写首字母
  return firstChar.toUpperCase()
}

// 使用 store 的 totalNotesCount（全部笔记总数）
const allNotesCount = computed(() => noteStore.totalNotesCount)
const themeButtonLabel = computed(() => {
  if (uiStore.theme === 'light') return '暖色主题'
  if (uiStore.theme === 'classic') return '默认主题'
  return '深色主题'
})
const themeToggleTitle = computed(() => {
  if (uiStore.theme === 'light') return '切换到默认主题'
  if (uiStore.theme === 'classic') return '切换到深色主题'
  return '切换到暖色主题'
})

// 拖拽相关状态
const draggedCategoryId = ref<string | null>(null)
const dragOverCategoryId = ref<string | null>(null)

// 新建笔记
async function handleNewNote(): Promise<void> {
  await noteStore.createNote()
}

// 添加分类
async function handleAddCategory(): Promise<void> {
  if (newCategoryName.value.trim()) {
    await categoryStore.addCategory(newCategoryName.value.trim(), newCategoryColor.value)
    newCategoryName.value = ''
    newCategoryColor.value = '#C4A882'
    showAddCategory.value = false
  }
}

// 分类菜单
function toggleCategoryMenu(categoryId: string, e: MouseEvent): void {
  if (categoryContextMenu.value.visible && categoryContextMenu.value.categoryId === categoryId) {
    hideCategoryContextMenu()
  } else {
    const btn = e.currentTarget as HTMLElement
    const rect = btn.getBoundingClientRect()
    categoryContextMenu.value = {
      visible: true,
      x: rect.right + 4,
      y: rect.top,
      categoryId
    }
  }
}

function hideCategoryContextMenu(): void {
  categoryContextMenu.value.visible = false
}

// 开始重命名分类
function startRenameCategory(): void {
  const category = categoryStore.categories.find(c => c.id === categoryContextMenu.value.categoryId)
  if (category) {
    editingCategoryId.value = category.id
    editingCategoryName.value = category.name
    hideCategoryContextMenu()
  }
}

// 确认重命名
async function confirmRenameCategory(): Promise<void> {
  if (editingCategoryId.value && editingCategoryName.value.trim()) {
    await categoryStore.updateCategory(editingCategoryId.value, { name: editingCategoryName.value.trim() })
  }
  editingCategoryId.value = null
  editingCategoryName.value = ''
}

// 取消重命名
function cancelRenameCategory(): void {
  editingCategoryId.value = null
  editingCategoryName.value = ''
}

// 删除分类
async function deleteCategory(): Promise<void> {
  const categoryId = categoryContextMenu.value.categoryId
  hideCategoryContextMenu()
  
  if (categoryId) {
    // 如果当前正在查看这个分类，切换到全部笔记
    if (noteStore.currentView === 'category' && noteStore.currentCategoryId === categoryId) {
      await noteStore.setView('all')
    }
    await categoryStore.deleteCategory(categoryId)
  }
}

// 拖拽开始
function handleDragStart(categoryId: string): void {
  draggedCategoryId.value = categoryId
}

// 拖拽经过
function handleDragOver(e: DragEvent, categoryId: string): void {
  e.preventDefault()
  
  // 检查是否在拖拽笔记
  const isNote = e.dataTransfer?.types.includes('source/type')
  if (isNote) {
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  }
  
  dragOverCategoryId.value = categoryId
}

// 拖拽离开
function handleDragLeave(): void {
  dragOverCategoryId.value = null
}

// 拖拽放下
async function handleDrop(targetCategoryId: string): Promise<void> {
  // 处理分类重排序
  if (draggedCategoryId.value && draggedCategoryId.value !== targetCategoryId) {
    await categoryStore.reorderCategories(draggedCategoryId.value, targetCategoryId)
    draggedCategoryId.value = null
  } 
  // 处理笔记移动到分类
  else {
    const noteId = document.querySelector('.note-card--dragging')?.getAttribute('data-id') 
                   || (window as any)._draggedNoteId // 兜底
    
    if (noteId) {
      await noteStore.updateNote(noteId, { categoryId: targetCategoryId })
    }
  }
  
  dragOverCategoryId.value = null
}

// 拖拽结束
function handleDragEnd(): void {
  draggedCategoryId.value = null
  dragOverCategoryId.value = null
}

// 导出/导入
async function handleExportBackup(): Promise<void> {
  await exportService.exportBackup()
}

async function handleImportBackup(): Promise<void> {
  const result = await exportService.importBackup()
  if (result.success) {
    await noteStore.loadNotes()
    await categoryStore.loadCategories()
  }
}

async function handleExportAllMarkdown(): Promise<void> {
  await exportService.exportAllAsMarkdown()
}
</script>

<style lang="scss" scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-light);
  padding: $spacing-md;
  position: relative;
  overflow: hidden;
  // 苹果风格丝滑过渡
  transition: padding 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
              background-color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: padding;
  backface-visibility: hidden;

  &--collapsed {
    padding: $spacing-sm;
  }
}

// 展开状态内容容器
.sidebar__expanded-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  opacity: 1;
  transform: translateX(0);
  // 苹果风格丝滑过渡
  transition: opacity 0.18s cubic-bezier(0.25, 0.1, 0.25, 1),
              transform 0.18s cubic-bezier(0.25, 0.1, 0.25, 1),
              visibility 0.18s;
  visibility: visible;
  will-change: opacity, transform;
  backface-visibility: hidden;
  
  &--hidden {
    opacity: 0;
    transform: translateX(-8px);
    visibility: hidden;
    pointer-events: none;
    position: absolute;
  }
}

// 收缩状态内容容器
.sidebar__collapsed-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 48px;
  opacity: 0;
  transform: translateX(8px);
  // 优化过渡：更快的动画
  transition: opacity 0.15s ease-out 0.03s,
              transform 0.15s ease-out 0.03s,
              visibility 0.15s 0.03s;
  visibility: hidden;
  pointer-events: none;
  will-change: opacity, transform;
  
  &--visible {
    opacity: 1;
    transform: translateX(0);
    visibility: visible;
    pointer-events: auto;
  }
}

.sidebar__toggle {
  position: absolute;
  top: $spacing-sm;
  right: $spacing-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.2s ease,
              color 0.2s ease,
              transform 0.2s ease;
  z-index: 10;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
  
  &:active {
    transform: scale(0.95);
  }

  svg {
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

.sidebar__new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  width: 100%;
  padding: $spacing-sm $spacing-md;
  margin-top: 32px;
  background: transparent;
  color: var(--color-text-primary);
  border: 1.5px solid var(--color-border-dark);
  border-radius: $radius-md;
  font-size: $font-size-sm;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s ease,
              border-color 0.2s ease,
              transform 0.15s ease;

  &:hover {
    background: var(--color-bg-hover);
    border-color: var(--color-text-secondary);
  }

  &:active {
    background: var(--color-bg-active);
    transform: scale(0.98);
  }
}

.sidebar__nav {
  margin-top: $spacing-lg;
}

.sidebar__item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-md;
  font-size: $font-size-sm;
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  // 优化过渡：只过渡必要属性，使用更快的时间
  transition: background-color 0.1s ease,
              color 0.1s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }

  &--active {
    background: var(--color-bg-card);
    color: var(--color-text-primary);
    box-shadow: var(--shadow-sm);
  }

  &--dragging {
    opacity: 0.5;
  }

  &--dragover {
    border-top: 2px solid var(--color-accent);
  }
}

.sidebar__icon {
  flex-shrink: 0;
}

.sidebar__count {
  margin-left: auto;
  font-size: $font-size-xs;
  color: var(--color-text-muted);
}

.sidebar__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px color-mix(in srgb, currentColor 10%, transparent);
}

.sidebar__section {
  margin-top: $spacing-lg;
}

.sidebar__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-sm;
  margin-bottom: $spacing-sm;
  font-size: $font-size-xs;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.sidebar__add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.2s ease,
              color 0.2s ease,
              transform 0.15s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
  
  &:active {
    transform: scale(0.9);
  }
}

.sidebar__categories {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__footer {
  margin-top: auto;
  padding-top: $spacing-md;
  border-top: 1px solid var(--color-border-light);
}

.sidebar__footer-actions {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
  margin-top: $spacing-sm;
}

.sidebar__footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: $spacing-xs $spacing-sm;
  border: 1px solid var(--color-border-dark);
  border-radius: $radius-sm;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: $font-size-xs;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s ease,
              color 0.2s ease,
              transform 0.15s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
  
  &:active {
    transform: scale(0.98);
  }
  
  &--settings {
    margin-top: $spacing-xs;
    border-style: dashed;
    
    svg {
      flex-shrink: 0;
    }
  }
}

// 主题切换按钮
.sidebar__theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  width: 100%;
  padding: $spacing-sm;
  margin-top: $spacing-md;
  border: none;
  border-radius: $radius-md;
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s ease,
              color 0.2s ease,
              transform 0.15s ease;

  &:hover {
    background: var(--color-bg-active);
    color: var(--color-text-primary);
  }
  
  &:active {
    transform: scale(0.98);
  }
  
  svg {
    flex-shrink: 0;
  }
}

// 收缩状态下的图标按钮
.sidebar__collapsed-items {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
}

.sidebar__collapsed-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1.5px solid transparent;
  border-radius: $radius-md;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background-color 0.2s ease,
              color 0.2s ease,
              border-color 0.2s ease,
              transform 0.15s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
  
  &:active {
    transform: scale(0.95);
  }

  &--active {
    background: var(--color-bg-card);
    color: var(--color-text-primary);
    border-color: var(--color-border-dark);
  }

  &--primary {
    border-color: var(--color-border-dark);
    color: var(--color-text-primary);

    &:hover {
      background: var(--color-bg-hover);
    }
  }
  
  // 分类按钮 - 更小更紧凑
  &--category {
    width: 32px;
    height: 32px;
    border-radius: $radius-sm;
    
    &:hover {
      background: var(--color-bg-hover);
      transform: scale(1.1);
    }
    
    &.sidebar__collapsed-btn--active {
      background: var(--color-bg-card);
      box-shadow: var(--shadow-sm);
    }
  }
}

// 分类圆点
.sidebar__collapsed-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.15s ease;
}

// 收缩状态分类按钮 - 首字母样式
.sidebar__collapsed-category {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: $radius-sm;
  background: color-mix(in srgb, var(--category-color) 15%, transparent);
  cursor: pointer;
  transition: background-color 0.2s ease,
              transform 0.15s ease,
              box-shadow 0.2s ease;

  &:hover {
    background: color-mix(in srgb, var(--category-color) 25%, transparent);
    transform: scale(1.08);
    
    .sidebar__collapsed-tooltip {
      opacity: 1;
      visibility: visible;
      transform: translateX(0);
    }
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  &--active {
    background: color-mix(in srgb, var(--category-color) 30%, transparent);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--category-color) 40%, transparent);
  }
}

.sidebar__collapsed-letter {
  font-size: 13px;
  font-weight: 600;
  color: var(--category-color);
  line-height: 1;
  user-select: none;
}

.sidebar__collapsed-tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateX(-4px) translateY(-50%);
  padding: 6px 10px;
  background: rgba(45, 42, 38, 0.95);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  border-radius: $radius-sm;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease,
              transform 0.2s ease,
              visibility 0.2s;
  z-index: 100;
  pointer-events: none;
  
  // 小三角箭头
  &::before {
    content: '';
    position: absolute;
    left: -4px;
    top: 50%;
    transform: translateY(-50%);
    border: 4px solid transparent;
    border-right-color: rgba(45, 42, 38, 0.95);
  }
}

// 分隔线
.sidebar__collapsed-divider {
  width: 24px;
  height: 1px;
  background: var(--color-border-light);
  margin: $spacing-xs 0;
}

// 模态框
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-bg-card);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  width: 300px;
  box-shadow: var(--shadow-lg);
}

.modal__title {
  font-size: $font-size-lg;
  font-weight: 500;
  margin-bottom: $spacing-md;
  color: var(--color-text-primary);
}

.modal__colors {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  margin-top: $spacing-md;
}

.modal__color {
  width: 32px;
  height: 32px;
  border-radius: $radius-sm;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.15s ease,
              border-color 0.15s ease,
              box-shadow 0.15s ease;
  position: relative;

  &:hover {
    transform: scale(1.1);
  }

  &--active {
    border-color: var(--color-text-primary);
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
    
    &::after {
      content: '✓';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: white;
      font-size: 14px;
      font-weight: bold;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
  }
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  margin-top: $spacing-lg;
}

// 分类内联编辑输入框
.sidebar__category-input {
  flex: 1;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-accent);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 13px;
  color: var(--color-text-primary);
  outline: none;
  min-width: 0;
}

.sidebar__category-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 分类项更多按钮
.sidebar__item--category {
  position: relative;
}

.sidebar__more-btn {
  opacity: 0;
  background: none;
  border: none;
  padding: 2px;
  cursor: pointer;
  color: var(--color-text-secondary);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.15s, background 0.15s;
  flex-shrink: 0;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
}

.sidebar__item--category:hover .sidebar__more-btn {
  opacity: 1;
}

// 右键菜单
.context-menu {
  position: fixed;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 4px;
  min-width: 120px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
}

.context-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-primary);
  transition: background 0.15s;

  &:hover {
    background: var(--color-bg-hover);
  }

  svg {
    flex-shrink: 0;
  }
}

.context-menu__item--danger {
  color: var(--color-danger, #ef4444);

  &:hover {
    background: rgba(239, 68, 68, 0.1);
  }
}

.context-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
}
</style>
