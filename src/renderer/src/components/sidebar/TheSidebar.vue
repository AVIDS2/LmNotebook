<template>
  <aside class="sidebar-rail">
    <div class="sidebar-rail__top">
      <button class="rail-btn rail-btn--primary" :title="t('sidebar.newNote')" @click="handleNewNote">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 3.5V14.5M3.5 9H14.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        </svg>
      </button>

      <div class="rail-divider"></div>

      <button
        class="rail-btn"
        :class="{ 'rail-btn--active': noteStore.currentView === 'all' }"
        :title="t('sidebar.allNotes')"
        @click="noteStore.setView('all')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="2.2" y="2.2" width="13.6" height="13.6" rx="2.2" stroke="currentColor" stroke-width="1.3" />
          <path d="M5.3 6.2H12.7M5.3 9H12.7M5.3 11.8H10.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
        </svg>
      </button>

      <button
        class="rail-btn"
        :class="{ 'rail-btn--active': noteStore.currentView === 'pinned' }"
        :title="t('sidebar.pinnedNotes')"
        @click="noteStore.setView('pinned')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 2.2L10.4 6.3L14.6 6.8L11.3 9.7L12.2 14.2L9 12.3L5.8 14.2L6.7 9.7L3.4 6.8L7.6 6.3L9 2.2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
        </svg>
      </button>

      <div class="category-entry">
        <button
          class="rail-btn"
          :class="{ 'rail-btn--active': noteStore.currentView === 'category' || categoryMenuVisible }"
          :title="t('sidebar.categories')"
          @click="categoryMenuVisible = !categoryMenuVisible"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="5.2" cy="5.2" r="1.2" fill="currentColor"/>
            <circle cx="5.2" cy="9" r="1.2" fill="currentColor"/>
            <circle cx="5.2" cy="12.8" r="1.2" fill="currentColor"/>
            <path d="M8 5.2H13.7M8 9H13.7M8 12.8H13.7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
        </button>

        <Teleport to="body">
          <div
            v-if="categoryMenuVisible"
            class="category-menu-overlay"
            @click="closeCategoryPanels"
          ></div>
          <div
            v-if="categoryMenuVisible"
            ref="categoryMenuRef"
            class="category-menu"
            :style="{ left: `${categoryMenuPosition.x}px`, top: `${categoryMenuPosition.y}px` }"
            @contextmenu.prevent="handleCategoryMenuBlankContextMenu"
          >
            <button class="category-menu__item category-menu__item--ghost" @click="selectNoCategory">
              {{ t('noteList.layerUncategorized') }}
            </button>
            <button
              v-for="category in categoryStore.categories"
              :key="category.id"
              class="category-menu__item"
              :class="{ 'category-menu__item--active': noteStore.currentView === 'category' && noteStore.currentCategoryId === category.id }"
              @click="selectCategory(category.id)"
              @mousedown.right.prevent.stop="openCategoryContextMenu(category.id, $event)"
              @contextmenu.prevent.stop="openCategoryContextMenu(category.id, $event)"
            >
              <span class="category-dot" :style="{ background: category.color }"></span>
              <span>{{ category.name }}</span>
            </button>
            <div class="category-menu__divider"></div>
            <button class="category-menu__item" @click="openCreateCategoryModal">
              {{ t('sidebar.newCategory') }}
            </button>
          </div>
          <div
            v-if="categoryContextMenu.visible"
            ref="categoryContextMenuRef"
            class="category-menu category-menu--context"
            :style="{ left: `${categoryContextMenu.x}px`, top: `${categoryContextMenu.y}px` }"
            @click.stop
          >
            <button class="category-menu__item" @click="handleCreateNoteInCategoryFromContext">
              {{ t('noteList.contextNewNoteInFolder') }}
            </button>
            <div class="category-menu__divider"></div>
            <button class="category-menu__item" @click="openRenameCategoryModalFromContext">
              {{ t('noteList.contextRenameFolder') }}
            </button>
            <button class="category-menu__item category-menu__item--danger" @click="deleteCategoryFromContext">
              {{ t('noteList.contextDeleteFolder') }}
            </button>
          </div>
        </Teleport>
      </div>
    </div>

    <div class="sidebar-rail__bottom">
      <button
        class="rail-btn"
        :class="{ 'rail-btn--active': noteStore.currentView === 'trash' }"
        :title="t('sidebar.recycleBin')"
        @click="noteStore.setView('trash')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M3.2 5.5H14.8M6 5.5V4.3C6 3.7 6.5 3.2 7.1 3.2H10.9C11.5 3.2 12 3.7 12 4.3V5.5M13.7 5.5V14.2C13.7 14.8 13.2 15.3 12.6 15.3H5.4C4.8 15.3 4.3 14.8 4.3 14.2V5.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </button>

      <button class="rail-btn" :title="t('sidebar.dataSettings')" @click="showDataSettings = true">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 11.1C10.1598 11.1 11.1 10.1598 11.1 9C11.1 7.8402 10.1598 6.9 9 6.9C7.8402 6.9 6.9 7.8402 6.9 9C6.9 10.1598 7.8402 11.1 9 11.1Z" stroke="currentColor" stroke-width="1.2"/>
          <path d="M14.4 9.8V8.2L12.9 7.8C12.8 7.5 12.7 7.3 12.5 7L13.3 5.7L12.2 4.6L10.9 5.4C10.7 5.3 10.4 5.2 10.2 5.1L9.8 3.6H8.2L7.8 5.1C7.5 5.2 7.3 5.3 7 5.4L5.7 4.6L4.6 5.7L5.4 7C5.3 7.3 5.2 7.5 5.1 7.8L3.6 8.2V9.8L5.1 10.2C5.2 10.5 5.3 10.7 5.4 11L4.6 12.3L5.7 13.4L7 12.6C7.3 12.7 7.5 12.8 7.8 12.9L8.2 14.4H9.8L10.2 12.9C10.5 12.8 10.7 12.7 11 12.6L12.3 13.4L13.4 12.3L12.6 11C12.7 10.7 12.8 10.5 12.9 10.2L14.4 9.8Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <Teleport to="body">
      <div v-if="showAddCategory" class="modal-overlay" @click.self="showAddCategory = false">
        <div class="modal">
          <h3 class="modal__title">
            {{ categoryModalMode === 'create' ? t('sidebar.newCategory') : t('noteList.contextRenameFolder') }}
          </h3>
          <input
            v-model="newCategoryName"
            class="modal__input"
            :placeholder="t('sidebar.categoryName')"
            @keyup.enter="handleCategoryModalSubmit"
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
            <button class="modal__btn" @click="showAddCategory = false">{{ t('common.cancel') }}</button>
            <button class="modal__btn modal__btn--primary" @click="handleCategoryModalSubmit">{{ t('common.confirm') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <DataSettings v-if="showDataSettings" @close="showDataSettings = false" />
  </aside>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useCategoryStore } from '@/stores/categoryStore'
import { useI18n } from '@/i18n'
import { useNoteStore } from '@/stores/noteStore'
import DataSettings from './DataSettings.vue'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const { t } = useI18n()

const showDataSettings = ref(false)
const showAddCategory = ref(false)
const newCategoryName = ref('')
const newCategoryColor = ref('#C4A882')
const categoryModalMode = ref<'create' | 'rename'>('create')
const editingCategoryId = ref<string | null>(null)
const categoryMenuVisible = ref(false)
const categoryMenuRef = ref<HTMLElement | null>(null)
const categoryMenuPosition = reactive({ x: 72, y: 112 })
const categoryContextMenuRef = ref<HTMLElement | null>(null)
const categoryContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  categoryId: null as string | null
})

const categoryColors = [
  '#6366F1',
  '#8B5CF6',
  '#EC4899',
  '#F59E0B',
  '#10B981',
  '#06B6D4',
  '#F97316',
  '#EF4444'
]

async function handleNewNote(): Promise<void> {
  await noteStore.createNote()
}

function resetCategoryModalState(): void {
  categoryModalMode.value = 'create'
  editingCategoryId.value = null
  newCategoryName.value = ''
  newCategoryColor.value = '#C4A882'
}

function openCreateCategoryModal(): void {
  closeCategoryPanels()
  categoryModalMode.value = 'create'
  editingCategoryId.value = null
  newCategoryName.value = ''
  newCategoryColor.value = '#C4A882'
  showAddCategory.value = true
}

function openRenameCategoryModal(categoryId: string): void {
  const category = categoryStore.getCategoryById(categoryId)
  if (!category) return
  closeCategoryPanels()
  categoryModalMode.value = 'rename'
  editingCategoryId.value = category.id
  newCategoryName.value = category.name
  newCategoryColor.value = category.color
  showAddCategory.value = true
}

async function handleCategoryModalSubmit(): Promise<void> {
  const name = newCategoryName.value.trim()
  if (!name) return

  if (categoryModalMode.value === 'rename' && editingCategoryId.value) {
    await categoryStore.updateCategory(editingCategoryId.value, {
      name,
      color: newCategoryColor.value
    })
  } else {
    await categoryStore.addCategory(name, newCategoryColor.value)
  }
  resetCategoryModalState()
  newCategoryName.value = ''
  newCategoryColor.value = '#C4A882'
  showAddCategory.value = false
}

function selectCategory(categoryId: string): void {
  noteStore.setView('category', categoryId)
  closeCategoryPanels()
}

function selectNoCategory(): void {
  noteStore.setView('all')
  closeCategoryPanels()
}

function updateCategoryMenuPosition(): void {
  if (!categoryMenuVisible.value) return
  const trigger = document.querySelector('.category-entry .rail-btn') as HTMLElement | null
  if (!trigger) return
  const rect = trigger.getBoundingClientRect()
  const menuWidth = 196
  const margin = 8
  categoryMenuPosition.x = Math.min(rect.right + 8, window.innerWidth - menuWidth - margin)
  categoryMenuPosition.y = Math.max(margin, rect.top)
}

function updateCategoryContextMenuPosition(): void {
  if (!categoryContextMenu.visible || !categoryContextMenuRef.value) return
  const menuRect = categoryContextMenuRef.value.getBoundingClientRect()
  const padding = 8
  categoryContextMenu.x = Math.max(
    padding,
    Math.min(categoryContextMenu.x, window.innerWidth - menuRect.width - padding)
  )
  categoryContextMenu.y = Math.max(
    padding,
    Math.min(categoryContextMenu.y, window.innerHeight - menuRect.height - padding)
  )
}

function hideCategoryContextMenu(): void {
  categoryContextMenu.visible = false
  categoryContextMenu.categoryId = null
}

function openCategoryContextMenu(categoryId: string, event: MouseEvent): void {
  categoryContextMenu.visible = true
  categoryContextMenu.categoryId = categoryId
  categoryContextMenu.x = event.clientX
  categoryContextMenu.y = event.clientY
  nextTick(() => {
    updateCategoryContextMenuPosition()
  })
}

function handleCategoryMenuBlankContextMenu(event: MouseEvent): void {
  categoryContextMenu.visible = true
  categoryContextMenu.categoryId = null
  categoryContextMenu.x = event.clientX
  categoryContextMenu.y = event.clientY
  nextTick(() => {
    updateCategoryContextMenuPosition()
  })
}

async function handleCreateNoteInCategoryFromContext(): Promise<void> {
  const categoryId = categoryContextMenu.categoryId
  if (!categoryId) {
    openCreateCategoryModal()
    return
  }
  await noteStore.createNote({ categoryId })
  closeCategoryPanels()
}

function openRenameCategoryModalFromContext(): void {
  const categoryId = categoryContextMenu.categoryId
  if (!categoryId) {
    openCreateCategoryModal()
    return
  }
  openRenameCategoryModal(categoryId)
}

async function deleteCategoryFromContext(): Promise<void> {
  const categoryId = categoryContextMenu.categoryId
  if (!categoryId) {
    closeCategoryPanels()
    return
  }
  const category = categoryStore.getCategoryById(categoryId)
  if (!category) {
    closeCategoryPanels()
    return
  }
  if (!confirm(t('noteList.confirmDeleteFolder', { name: category.name }))) return
  await categoryStore.deleteCategory(categoryId)
  if (noteStore.currentView === 'category' && noteStore.currentCategoryId === categoryId) {
    noteStore.setView('all')
  }
  closeCategoryPanels()
}

function closeCategoryPanels(): void {
  categoryMenuVisible.value = false
  hideCategoryContextMenu()
}

watch(categoryMenuVisible, (open) => {
  if (!open) {
    hideCategoryContextMenu()
    return
  }
  nextTick(() => {
    updateCategoryMenuPosition()
  })
})

watch(showAddCategory, (open) => {
  if (!open) {
    resetCategoryModalState()
  }
})

function handleWindowUpdate(): void {
  updateCategoryMenuPosition()
  updateCategoryContextMenuPosition()
}

onMounted(() => {
  window.addEventListener('resize', handleWindowUpdate)
  window.addEventListener('scroll', handleWindowUpdate, true)
  window.addEventListener('click', hideCategoryContextMenu)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowUpdate)
  window.removeEventListener('scroll', handleWindowUpdate, true)
  window.removeEventListener('click', hideCategoryContextMenu)
})
</script>

<style scoped lang="scss">
.sidebar-rail {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  padding: 8px 6px 6px;
  background: var(--color-bg-secondary);
  border-right: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
}

.sidebar-rail__top,
.sidebar-rail__bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.rail-divider {
  width: 22px;
  height: 1px;
  margin: 3px 0;
  background: color-mix(in srgb, var(--color-border) 62%, transparent);
}

.rail-btn {
  width: 34px;
  height: 34px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease;

  &:hover {
    background: var(--color-bg-hover);
    border-color: color-mix(in srgb, var(--color-border) 56%, transparent);
    color: var(--color-text-primary);
  }

  &--active {
    background: color-mix(in srgb, var(--color-bg-hover) 88%, transparent);
    border-color: color-mix(in srgb, var(--color-border) 66%, transparent);
    color: var(--color-text-primary);
  }

  &--primary {
    border-color: color-mix(in srgb, var(--color-border-dark) 72%, transparent);
    color: var(--color-text-primary);
  }
}

.category-entry {
  position: relative;
}

.category-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 13020;
}

.category-menu {
  position: fixed;
  width: 196px;
  max-height: min(66vh, 420px);
  overflow-y: auto;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--color-border) 62%, transparent);
  background: color-mix(in srgb, var(--color-bg-card) 94%, transparent);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 13021;
}

.category-menu--context {
  width: 188px;
  z-index: 13022;
}

.category-menu__item {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 9px;
  padding: 8px 10px;
  text-align: left;
  font-size: 13px;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color 0.14s ease;

  &:hover {
    background: var(--color-bg-hover);
  }

  &--active {
    background: color-mix(in srgb, var(--color-accent) 10%, transparent);
  }

  &--ghost {
    color: var(--color-text-secondary);
  }

  &--danger {
    color: var(--color-danger, #ef4444);

    &:hover {
      background: color-mix(in srgb, #ef4444 12%, transparent);
    }
  }
}

.category-menu__divider {
  height: 1px;
  margin: 6px 2px;
  background: color-mix(in srgb, var(--color-border) 68%, transparent);
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50020;
}

.modal {
  width: 300px;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  background: var(--color-bg-card);
  box-shadow: var(--shadow-lg);
}

.modal__title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.modal__input {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--color-border) 60%, transparent);
  border-radius: 8px;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  padding: 8px 10px;
  font-size: 13px;
  outline: none;
}

.modal__colors {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.modal__color {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  border: 2px solid transparent;
  cursor: pointer;

  &--active {
    border-color: #fff;
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--color-border-dark) 80%, transparent);
  }
}

.modal__actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.modal__btn {
  border: 1px solid color-mix(in srgb, var(--color-border) 60%, transparent);
  background: transparent;
  color: var(--color-text-secondary);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
  cursor: pointer;

  &--primary {
    background: var(--color-accent);
    border-color: var(--color-accent);
    color: #fff;
  }
}
</style>
