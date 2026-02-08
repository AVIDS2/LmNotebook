<template>
  <div class="search-bar">
    <svg class="search-bar__icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <input
      v-model="searchValue"
      class="search-bar__input"
      type="text"
      :placeholder="t('search.placeholder')"
      @input="handleSearch"
    />
    <button
      v-if="searchValue"
      class="search-bar__clear"
      @click="handleClear"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useNoteStore } from '@/stores/noteStore'
import { useI18n } from '@/i18n'

const noteStore = useNoteStore()
const { t } = useI18n()
const searchValue = ref('')

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function handleSearch(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(() => {
    noteStore.search(searchValue.value)
  }, 300)
}

function handleClear(): void {
  searchValue.value = ''
  noteStore.search('')
}

// 当视图切换时清空搜索
watch(() => noteStore.currentView, () => {
  searchValue.value = ''
})
</script>

<style lang="scss" scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  transition: background-color 0.3s ease;
}

.search-bar__icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.search-bar__input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: $font-size-sm;
  color: var(--color-text-primary);
  outline: none;

  &::placeholder {
    color: var(--color-text-placeholder);
  }
}

.search-bar__clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: var(--color-bg-hover);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color $transition-fast, color $transition-fast;

  &:hover {
    background: var(--color-bg-active);
    color: var(--color-text-primary);
  }
}
</style>
