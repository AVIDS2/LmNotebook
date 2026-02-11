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
  gap: 8px;
  margin: 8px 10px 6px;
  padding: 8px 10px;
  background: color-mix(in srgb, var(--color-bg-secondary) 92%, var(--color-bg-primary));
  border: 1px solid color-mix(in srgb, var(--color-border) 60%, transparent);
  border-radius: 12px;
  transition: border-color 0.16s ease, background-color 0.16s ease, box-shadow 0.16s ease;

  &:focus-within {
    border-color: color-mix(in srgb, var(--color-accent) 38%, var(--color-border));
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-accent) 12%, transparent);
  }
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
  width: 22px;
  height: 22px;
  border: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg-primary) 94%, transparent);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color $transition-fast, color $transition-fast, border-color $transition-fast;

  &:hover {
    background: var(--color-bg-active);
    color: var(--color-text-primary);
    border-color: var(--color-border);
  }
}

/* Lightweight enterprise pass */
.search-bar {
  gap: 6px;
  margin: 0 8px 8px;
  padding: 7px 10px;
  background: color-mix(in srgb, var(--color-bg-primary) 96%, transparent);
  border-color: color-mix(in srgb, var(--color-border) 60%, transparent);
  border-radius: 10px;
  box-shadow: none;
}

.search-bar__input {
  font-size: 13px;
  line-height: 1.3;
}

.search-bar__clear {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border-color: transparent;
  background: transparent;
}
</style>
