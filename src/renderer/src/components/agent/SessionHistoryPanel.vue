<template>
  <Transition name="slide-panel">
    <div v-if="visible" class="session-history-panel">
      <div class="session-history__header">
        <span>{{ title }}</span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="session-history__list">
        <div v-if="sessions.length === 0" class="session-history__empty">
          {{ emptyText }}
        </div>
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ 'session-item--active': session.id === currentSessionId, 'session-item--pinned': session.pinned }"
          @click="editingSessionId !== session.id && $emit('load-session', session.id)"
        >
          <div v-if="editingSessionId !== session.id" class="session-item__preview">
            <span v-if="session.pinned" class="pin-indicator">
              <svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="12" height="12">
                <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
              </svg>
            </span>
            {{ toSingleLine(session.title || session.preview) }}
          </div>
          <input
            v-else
            :value="editingTitle"
            class="session-rename-input"
            @click.stop
            @input="$emit('update:editing-title', ($event.target as HTMLInputElement).value)"
            @keyup.enter="$emit('confirm-rename', session.id)"
            @keyup.escape="$emit('cancel-rename')"
            @blur="$emit('confirm-rename', session.id)"
          />
          <div v-if="editingSessionId !== session.id" class="session-item__actions">
            <button class="session-item__btn" @click.stop="$emit('toggle-pin', session.id)" :title="session.pinned ? unpinTitle : pinTitle">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
              </svg>
            </button>
            <button class="session-item__btn" @click.stop="$emit('rename-session', session.id)" :title="renameTitle">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="session-item__btn session-item__btn--danger" @click.stop="$emit('delete-session', session.id)" :title="deleteTitle">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import type { SessionInfo } from './sessionTypes'

defineProps<{
  visible: boolean
  title: string
  emptyText: string
  sessions: SessionInfo[]
  currentSessionId: string
  editingSessionId: string | null
  editingTitle: string
  pinTitle: string
  unpinTitle: string
  renameTitle: string
  deleteTitle: string
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'load-session', sessionId: string): void
  (e: 'toggle-pin', sessionId: string): void
  (e: 'rename-session', sessionId: string): void
  (e: 'delete-session', sessionId: string): void
  (e: 'confirm-rename', sessionId: string): void
  (e: 'cancel-rename'): void
  (e: 'update:editing-title', value: string): void
}>()

function toSingleLine(value: string): string {
  return String(value || '')
    .replace(/[\uE000-\uF8FF]/g, '')
    .replace(/[\u200B-\u200F\u2060\uFEFF]/g, '')
    .replace(/[\r\n\t]+/g, ' ')
    .replace(/\|{2,}/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim()
}
</script>

<style scoped lang="scss">
.session-history-panel {
  position: relative;
  width: 100%;
  max-height: 100%;
  z-index: 1;
  border: 1px solid color-mix(in srgb, var(--color-border) 62%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, var(--color-bg-card) 97%, transparent);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.16);
  overflow: hidden;
}

.session-history__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
}

.session-history__header .close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.session-history__header .close-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.session-history__list {
  max-height: min(56vh, 420px);
  overflow-y: auto;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-history__empty {
  padding: 14px 10px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 8px;
  border-radius: 9px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.session-item:hover {
  background: var(--color-bg-hover);
}

.session-item--active {
  background: color-mix(in srgb, var(--color-accent) 11%, transparent);
}

.session-item--pinned {
  border-left: 1px solid color-mix(in srgb, var(--color-accent) 34%, transparent);
}

.session-item__preview {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pin-indicator {
  display: inline-flex;
  align-items: center;
  color: var(--color-text-muted);
}

.session-item__actions {
  display: none;
  align-items: center;
  gap: 2px;
}

.session-item:hover .session-item__actions {
  display: inline-flex;
}

.session-item__btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.session-item__btn:hover {
  background: color-mix(in srgb, var(--color-bg-hover) 80%, transparent);
  color: var(--color-text-primary);
}

.session-item__btn--danger:hover {
  background: color-mix(in srgb, #ef4444 14%, transparent);
  color: #ef4444;
}

.session-item__btn svg {
  width: 13px;
  height: 13px;
}

.session-rename-input {
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
  border-radius: 8px;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-size: 13px;
  padding: 5px 8px;
  outline: none;
}

.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
