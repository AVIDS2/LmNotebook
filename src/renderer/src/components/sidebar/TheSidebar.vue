<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <!-- 收缩按钮 -->
    <button class="sidebar__toggle" @click="$emit('toggle')" :title="collapsed ? '展开' : '收起'">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" :style="{ transform: collapsed ? 'rotate(180deg)' : '' }">
        <path d="M10 4L6 8L10 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <template v-if="!collapsed">
      <!-- 新建笔记按钮 -->
      <button class="sidebar__new-btn" @click="handleNewNote">
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
          <button class="sidebar__add-btn" @click="showAddCategory = true">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2V12M2 7H12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="sidebar__categories">
          <div
            v-for="category in categoryStore.categories"
            :key="category.id"
            class="sidebar__item"
            :class="{
              'sidebar__item--active': noteStore.currentView === 'category' && noteStore.currentCategoryId === category.id,
              'sidebar__item--dragging': draggedCategoryId === category.id,
              'sidebar__item--dragover': dragOverCategoryId === category.id
            }"
            draggable="true"
            @click="noteStore.setView('category', category.id)"
            @dragstart="handleDragStart(category.id)"
            @dragover="handleDragOver($event, category.id)"
            @dragleave="handleDragLeave"
            @drop="handleDrop(category.id)"
            @dragend="handleDragEnd"
          >
            <span class="sidebar__dot" :style="{ background: category.color }"></span>
            <span>{{ category.name }}</span>
          </div>
        </div>
      </div>

      <!-- 底部 -->
      <div class="sidebar__footer">
        <div
          class="sidebar__item"
          :class="{ 'sidebar__item--active': noteStore.currentView === 'trash' }"
          @click="noteStore.setView('trash')"
        >
          <svg class="sidebar__icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M3 5H15M6 5V4C6 3.44772 6.44772 3 7 3H11C11.5523 3 12 3.44772 12 4V5M14 5V14C14 14.5523 13.5523 15 13 15H5C4.44772 15 4 14.5523 4 14V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <span>回收站</span>
        </div>

        <div class="sidebar__footer-actions">
          <button class="sidebar__footer-btn" @click="handleExportBackup">导出备份</button>
          <button class="sidebar__footer-btn" @click="handleImportBackup">导入备份</button>
          <button class="sidebar__footer-btn" @click="handleExportAllMarkdown">导出全部 MD</button>
        </div>
      </div>
    </template>

    <!-- 收缩状态下的图标 -->
    <template v-else>
      <div class="sidebar__collapsed-items">
        <button class="sidebar__collapsed-btn" @click="handleNewNote" title="新建笔记">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'all' }"
          @click="noteStore.setView('all')"
          title="全部笔记"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="3" y="3" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <path d="M6 7H14M6 10H14M6 13H11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
        </button>
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'pinned' }"
          @click="noteStore.setView('pinned')"
          title="置顶笔记"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 3L11.5 7.5L16 8L12.5 11L13.5 16L10 13.5L6.5 16L7.5 11L4 8L8.5 7.5L10 3Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          </svg>
        </button>
        <button
          class="sidebar__collapsed-btn"
          :class="{ 'sidebar__collapsed-btn--active': noteStore.currentView === 'trash' }"
          @click="noteStore.setView('trash')"
          title="回收站"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4 6H16M7 6V5C7 4.44772 7.44772 4 8 4H12C12.5523 4 13 4.44772 13 5V6M15 6V15C15 15.5523 14.5523 16 14 16H6C5.44772 16 5 15.5523 5 15V6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </template>

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
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { exportService } from '@/services/exportService'

defineProps<{
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
}>()

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()

const showAddCategory = ref(false)
const newCategoryName = ref('')
const newCategoryColor = ref('#C4A882')

const categoryColors = [
  '#C4A882', '#8FA882', '#82A8C4', '#C4A8A8', '#A8A2C4', '#8C9198'
]

// 使用 store 的 totalNotesCount（全部笔记总数）
const allNotesCount = computed(() => noteStore.totalNotesCount)

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

// 拖拽开始
function handleDragStart(categoryId: string): void {
  draggedCategoryId.value = categoryId
}

// 拖拽经过
function handleDragOver(e: DragEvent, categoryId: string): void {
  e.preventDefault()
  dragOverCategoryId.value = categoryId
}

// 拖拽离开
function handleDragLeave(): void {
  dragOverCategoryId.value = null
}

// 拖拽放下
async function handleDrop(targetCategoryId: string): Promise<void> {
  if (draggedCategoryId.value && draggedCategoryId.value !== targetCategoryId) {
    await categoryStore.reorderCategories(draggedCategoryId.value, targetCategoryId)
  }
  draggedCategoryId.value = null
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
  width: $sidebar-width;
  background: $color-bg-secondary;
  border-right: 1px solid $color-border-light;
  padding: $spacing-md;
  transition: width 0.25s ease;
  position: relative;

  &--collapsed {
    width: 56px;
    padding: $spacing-sm;
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
  color: $color-text-muted;
  cursor: pointer;
  transition: all $transition-fast;
  z-index: 10;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
  }

  svg {
    transition: transform 0.25s ease;
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
  color: $color-text-primary;
  border: 1.5px solid $color-border-dark;
  border-radius: $radius-md;
  font-size: $font-size-sm;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
    border-color: $color-text-secondary;
  }

  &:active {
    background: $color-bg-active;
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
  color: $color-text-secondary;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
  }

  &--active {
    background: $color-bg-card;
    color: $color-text-primary;
    box-shadow: $shadow-sm;
  }

  &--dragging {
    opacity: 0.5;
  }

  &--dragover {
    border-top: 2px solid $color-accent;
  }
}

.sidebar__icon {
  flex-shrink: 0;
}

.sidebar__count {
  margin-left: auto;
  font-size: $font-size-xs;
  color: $color-text-muted;
}

.sidebar__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
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
  color: $color-text-muted;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  color: $color-text-muted;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
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
  border-top: 1px solid $color-border-light;
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
  width: 100%;
  padding: $spacing-xs $spacing-sm;
  border: 1px solid $color-border-dark;
  border-radius: $radius-sm;
  background: transparent;
  color: $color-text-secondary;
  font-size: $font-size-xs;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
  }
}

// 收缩状态下的图标按钮
.sidebar__collapsed-items {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  margin-top: 40px;
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
  color: $color-text-secondary;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-bg-hover;
    color: $color-text-primary;
  }

  &--active {
    background: $color-bg-card;
    color: $color-text-primary;
    border-color: $color-border-dark;
  }

  &:first-child {
    border-color: $color-border-dark;
    color: $color-text-primary;

    &:hover {
      background: $color-bg-hover;
    }
  }
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
  background: $color-bg-card;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  width: 300px;
  box-shadow: $shadow-lg;
}

.modal__title {
  font-size: $font-size-lg;
  font-weight: 500;
  margin-bottom: $spacing-md;
  color: $color-text-primary;
}

.modal__colors {
  display: flex;
  gap: $spacing-sm;
  margin-top: $spacing-md;
}

.modal__color {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    transform: scale(1.1);
  }

  &--active {
    border-color: $color-text-primary;
  }
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  margin-top: $spacing-lg;
}
</style>
