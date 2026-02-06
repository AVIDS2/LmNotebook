import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NoticeType = 'info' | 'success' | 'warning' | 'error'

export interface NoticeItem {
  id: string
  type: NoticeType
  message: string
  timeoutMs: number
}

const DEFAULT_TIMEOUT_MS = 3000
const ERROR_TIMEOUT_MS = 5000

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export const useNotifyStore = defineStore('notify', () => {
  const notices = ref<NoticeItem[]>([])

  function add(message: string, type: NoticeType = 'info', timeoutMs?: number): void {
    const item: NoticeItem = {
      id: newId(),
      type,
      message,
      timeoutMs: timeoutMs ?? (type === 'error' ? ERROR_TIMEOUT_MS : DEFAULT_TIMEOUT_MS)
    }
    notices.value.push(item)

    if (item.timeoutMs > 0) {
      setTimeout(() => remove(item.id), item.timeoutMs)
    }
  }

  function remove(id: string): void {
    notices.value = notices.value.filter(n => n.id !== id)
  }

  function clear(): void {
    notices.value = []
  }

  return { notices, add, remove, clear }
})
