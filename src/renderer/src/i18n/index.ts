import { computed } from 'vue'
import { useUIStore, type LocaleCode } from '@/stores/uiStore'
import messages from './messages.json'

type MessageValue = string | Record<string, MessageValue>

type MessageCatalog = Record<LocaleCode, Record<string, MessageValue>>

const catalog = messages as MessageCatalog

function getNestedValue(obj: Record<string, MessageValue>, path: string): string | undefined {
  const parts = path.split('.')
  let current: MessageValue | undefined = obj

  for (const part of parts) {
    if (!current || typeof current === 'string') {
      return undefined
    }
    current = (current as Record<string, MessageValue>)[part]
  }

  return typeof current === 'string' ? current : undefined
}

function applyParams(template: string, params?: Record<string, string | number>): string {
  if (!params) return template
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (_match, key: string) => {
    const value = params[key]
    return value === undefined ? '' : String(value)
  })
}

export function translate(locale: LocaleCode, key: string, params?: Record<string, string | number>): string {
  const targetLocale = catalog[locale] ? locale : 'zh-CN'
  const localized = getNestedValue(catalog[targetLocale], key)
  const fallback = getNestedValue(catalog['zh-CN'], key)
  const text = localized ?? fallback ?? key
  return applyParams(text, params)
}

export function useI18n() {
  const uiStore = useUIStore()

  const locale = computed(() => uiStore.locale)
  const t = (key: string, params?: Record<string, string | number>) => {
    return translate(locale.value, key, params)
  }

  return {
    locale,
    t,
    setLocale: uiStore.setLocale,
    toggleLocale: uiStore.toggleLocale
  }
}
