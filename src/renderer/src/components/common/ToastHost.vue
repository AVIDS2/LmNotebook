<template>
  <div class="toast-host" aria-live="polite" aria-atomic="true">
    <transition-group name="toast" tag="div" class="toast-list">
      <div
        v-for="n in notices"
        :key="n.id"
        class="toast"
        :class="`toast--${n.type}`"
        role="status"
      >
        <div class="toast__message">{{ n.message }}</div>
        <button class="toast__close" @click="remove(n.id)" aria-label="Close">x</button>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useNotifyStore } from '@/stores/notifyStore'

const notify = useNotifyStore()
const { notices } = storeToRefs(notify)
const { remove } = notify
</script>

<style scoped>
.toast-host {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 10050;
  pointer-events: none;
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  min-width: 220px;
  max-width: 360px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(20, 20, 20, 0.9);
  color: #fff;
  font-size: 13px;
  line-height: 1.4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
  pointer-events: auto;
}

.toast--success { background: rgba(25, 120, 70, 0.95); }
.toast--warning { background: rgba(160, 110, 20, 0.95); }
.toast--error { background: rgba(170, 40, 40, 0.95); }

.toast__message {
  flex: 1;
  word-break: break-word;
}

.toast__close {
  border: none;
  background: transparent;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
