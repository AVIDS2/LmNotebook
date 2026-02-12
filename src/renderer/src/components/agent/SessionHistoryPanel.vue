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
            {{ session.title || session.preview }}
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
            <button class="session-item__btn" @click.stop="$emit('toggle-pin', session.id)" :title="session.pinned ? '取消置顶' : '置顶'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
              </svg>
            </button>
            <button class="session-item__btn" @click.stop="$emit('rename-session', session.id)" title="重命名">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="session-item__btn session-item__btn--danger" @click.stop="$emit('delete-session', session.id)" title="删除">
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
</script>
