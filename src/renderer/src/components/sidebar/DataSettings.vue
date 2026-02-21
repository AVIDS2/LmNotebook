<template>
  <Teleport to="body">
    <div class="settings-overlay" @click.self="$emit('close')">
      <div class="settings-modal" @click.stop>
        <header class="settings-header">
          <div>
            <h2 class="settings-title">{{ t('settings.title') }}</h2>
            <p class="settings-subtitle">{{ t('settings.subtitle') }}</p>
          </div>
          <button class="icon-btn" @click="$emit('close')" :title="t('common.close')">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <div class="settings-main">
          <aside class="settings-nav">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="settings-nav-item"
              :class="{ 'settings-nav-item--active': activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
          </aside>

          <section class="settings-panel">
            <template v-if="activeTab === 'general'">
              <div class="settings-card">
                <div class="settings-row">
                  <div>
                    <h3>{{ t('settings.general.appVersion') }}</h3>
                    <p>{{ appMeta.name }} {{ appMeta.version }}</p>
                  </div>
                  <span class="badge" :class="{ 'badge--muted': !appMeta.packaged }">
                    {{ appMeta.packaged ? t('settings.general.buildRelease') : t('settings.general.buildDev') }}
                  </span>
                </div>
                <div class="settings-row">
                  <div>
                    <h3>{{ t('settings.general.language') }}</h3>
                    <p>{{ t('settings.general.languageHint') }}</p>
                  </div>
                  <div class="dropdown-select" ref="localeDropdownRef">
                    <button
                      class="dropdown-select__trigger"
                      :class="{ 'dropdown-select__trigger--open': localeDropdownOpen }"
                      @click="localeDropdownOpen = !localeDropdownOpen"
                    >
                      <span class="dropdown-select__label">{{ localeLabel }}</span>
                      <svg class="dropdown-select__caret" width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M4 5.5L7 8.5L10 5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <Transition name="dropdown-fade">
                      <div v-if="localeDropdownOpen" class="dropdown-select__menu">
                        <button
                          class="dropdown-select__item"
                          :class="{ 'dropdown-select__item--active': locale === 'zh-CN' }"
                          @click="setLocaleFromMenu('zh-CN')"
                        >
                          {{ t('language.zh-CN') }}
                        </button>
                        <button
                          class="dropdown-select__item"
                          :class="{ 'dropdown-select__item--active': locale === 'en-US' }"
                          @click="setLocaleFromMenu('en-US')"
                        >
                          {{ t('language.en-US') }}
                        </button>
                      </div>
                    </Transition>
                  </div>
                </div>
                <div class="settings-row settings-row--stackable">
                  <div>
                    <h3>{{ t('settings.general.theme') }}</h3>
                    <p>{{ t('settings.general.themeHint') }}</p>
                  </div>
                  <div class="segmented">
                    <button
                      class="segmented__item"
                      :class="{ 'segmented__item--active': uiStore.theme === 'classic' }"
                      @click="setTheme('classic')"
                    >
                      {{ t('sidebar.theme.classic') }}
                    </button>
                    <button
                      class="segmented__item"
                      :class="{ 'segmented__item--active': uiStore.theme === 'light' }"
                      @click="setTheme('light')"
                    >
                      {{ t('sidebar.theme.light') }}
                    </button>
                    <button
                      class="segmented__item"
                      :class="{ 'segmented__item--active': uiStore.theme === 'dark' }"
                      @click="setTheme('dark')"
                    >
                      {{ t('sidebar.theme.dark') }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="settings-card">
                <h3 class="card-title">{{ t('settings.general.aboutTitle') }}</h3>
                <p class="muted">{{ t('settings.general.aboutDescription') }}</p>
                <div class="about-grid">
                  <div class="about-item">
                    <h4>{{ t('settings.general.aboutNotebookTitle') }}</h4>
                    <p>{{ t('settings.general.aboutNotebookBody') }}</p>
                  </div>
                  <div class="about-item">
                    <h4>{{ t('settings.general.aboutAgentTitle') }}</h4>
                    <p>{{ t('settings.general.aboutAgentBody') }}</p>
                  </div>
                  <div class="about-item">
                    <h4>{{ t('settings.general.aboutModeTitle') }}</h4>
                    <p>{{ t('settings.general.aboutModeBody') }}</p>
                  </div>
                  <div class="about-item">
                    <h4>{{ t('settings.general.aboutSafetyTitle') }}</h4>
                    <p>{{ t('settings.general.aboutSafetyBody') }}</p>
                  </div>
                </div>
              </div>
            </template>

            <template v-else-if="activeTab === 'data'">
              <div class="settings-card">
                <h3 class="card-title">{{ t('settings.data.stats') }}</h3>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-value">{{ stats.noteCount }}</span>
                    <span class="stat-label">{{ t('settings.data.notes') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ stats.categoryCount }}</span>
                    <span class="stat-label">{{ t('settings.data.categories') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ formatSize(stats.dbSize) }}</span>
                    <span class="stat-label">{{ t('settings.data.databaseSize') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ imageStats.count }}</span>
                    <span class="stat-label">{{ t('settings.data.images') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ formatSize(imageStats.totalSize) }}</span>
                    <span class="stat-label">{{ t('settings.data.imageSize') }}</span>
                  </div>
                </div>
              </div>

              <div class="settings-card">
                <h3 class="card-title">{{ t('settings.data.storage') }}</h3>
                <p class="muted">{{ t('settings.data.storageHint') }}</p>
                <div class="path-row">
                  <input type="text" class="input" :value="config.dataDirectory" readonly />
                  <button class="btn" @click="selectDataDirectory">{{ t('settings.actions.change') }}</button>
                </div>
                <div class="action-row">
                  <button class="btn btn--ghost" @click="openDataDirectory">{{ t('settings.actions.open') }}</button>
                  <button v-if="!isDefaultDirectory" class="btn btn--ghost" @click="resetToDefault">{{ t('settings.actions.resetDefault') }}</button>
                </div>
              </div>

              <div class="settings-card">
                <h3 class="card-title">{{ t('settings.data.embeddingTitle') }}</h3>
                <p class="muted">{{ t('settings.data.embeddingHint') }}</p>
                <div class="settings-row settings-row--stackable">
                  <div>
                    <h3>{{ t('settings.data.embeddingMode') }}</h3>
                    <p>{{ t('settings.data.embeddingModeHint') }}</p>
                  </div>
                  <div class="dropdown-select" ref="embeddingModeDropdownRef">
                    <button
                      class="dropdown-select__trigger"
                      :class="{ 'dropdown-select__trigger--open': embeddingModeDropdownOpen }"
                      @click="embeddingModeDropdownOpen = !embeddingModeDropdownOpen"
                    >
                      <span class="dropdown-select__label">{{ embeddingModeLabel }}</span>
                      <svg class="dropdown-select__caret" width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M4 5.5L7 8.5L10 5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <Transition name="dropdown-fade">
                      <div v-if="embeddingModeDropdownOpen" class="dropdown-select__menu">
                        <button
                          class="dropdown-select__item"
                          :class="{ 'dropdown-select__item--active': config.embeddingMode === 'api' }"
                          @click="setEmbeddingMode('api')"
                        >
                          API
                        </button>
                        <button
                          class="dropdown-select__item"
                          :class="{ 'dropdown-select__item--active': config.embeddingMode === 'local' }"
                          @click="setEmbeddingMode('local')"
                        >
                          Local
                        </button>
                      </div>
                    </Transition>
                  </div>
                </div>
                <div class="settings-row settings-row--stackable">
                  <div>
                    <h3>{{ t('settings.data.embeddingModel') }}</h3>
                    <p>{{ t('settings.data.embeddingModelHint') }}</p>
                  </div>
                  <input
                    type="text"
                    class="input"
                    v-model="config.embeddingModel"
                    @blur="saveEmbeddingModel"
                    @keyup.enter="saveEmbeddingModel"
                  />
                </div>
              </div>
            </template>

            <template v-else-if="activeTab === 'backup'">
              <div class="settings-card">
                <div class="settings-row">
                  <div>
                    <h3>{{ t('settings.backup.autoBackup') }}</h3>
                    <p>{{ t('settings.backup.autoBackupHint') }}</p>
                  </div>
                  <label class="switch">
                    <input type="checkbox" v-model="config.autoBackup" @change="saveConfig" />
                    <span></span>
                  </label>
                </div>

                <div class="settings-row" v-if="config.autoBackup">
                  <div>
                    <h3>{{ t('settings.backup.maxCount') }}</h3>
                    <p>{{ t('settings.backup.maxCountHint') }}</p>
                  </div>
                  <div class="dropdown-select" ref="backupCountDropdownRef">
                    <button
                      class="dropdown-select__trigger"
                      :class="{ 'dropdown-select__trigger--open': backupCountDropdownOpen }"
                      @click="backupCountDropdownOpen = !backupCountDropdownOpen"
                    >
                      <span class="dropdown-select__label">{{ config.maxBackups }}</span>
                      <svg class="dropdown-select__caret" width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M4 5.5L7 8.5L10 5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <Transition name="dropdown-fade">
                      <div v-if="backupCountDropdownOpen" class="dropdown-select__menu">
                        <button
                          v-for="count in backupCountOptions"
                          :key="count"
                          class="dropdown-select__item"
                          :class="{ 'dropdown-select__item--active': config.maxBackups === count }"
                          @click="setBackupCount(count)"
                        >
                          {{ count }}
                        </button>
                      </div>
                    </Transition>
                  </div>
                </div>
              </div>

              <div class="settings-card">
                <div class="settings-row">
                  <h3>{{ t('settings.backup.backups') }}</h3>
                  <button class="btn btn--primary" @click="createBackup" :disabled="isCreatingBackup">
                    {{ isCreatingBackup ? t('settings.backup.creating') : t('settings.backup.createNow') }}
                  </button>
                </div>

                <div class="backup-list" v-if="backups.length > 0">
                  <div class="backup-item" v-for="backup in backups" :key="backup.filename">
                    <div>
                      <div class="backup-name">{{ backup.filename }}</div>
                      <div class="backup-meta">{{ formatSize(backup.size) }} 路 {{ formatDate(backup.createdAt) }}</div>
                    </div>
                    <button class="btn" @click="restoreBackup(backup)">{{ t('settings.actions.restore') }}</button>
                  </div>
                </div>
                <p class="muted" v-else>{{ t('settings.backup.empty') }}</p>
              </div>
            </template>

            <template v-else>
              <div class="settings-card">
                <div class="settings-row">
                  <div>
                    <h3>{{ t('settings.update.currentVersion') }}</h3>
                    <p>{{ appMeta.version }}</p>
                  </div>
                  <span class="badge">{{ updaterStageLabel }}</span>
                </div>

                <div class="settings-row">
                  <div>
                    <h3>{{ t('settings.update.autoCheck') }}</h3>
                    <p>{{ t('settings.update.autoCheckHint') }}</p>
                  </div>
                  <label class="switch">
                    <input type="checkbox" :checked="updateState.autoCheck" @change="handleUpdateAutoCheck" />
                    <span></span>
                  </label>
                </div>

                <div class="update-actions">
                  <button class="btn" @click="checkUpdates" :disabled="isChecking || !appMeta.packaged">
                    {{ t('settings.update.checkNow') }}
                  </button>
                  <button class="btn" @click="downloadUpdate" :disabled="!canDownload">
                    {{ t('settings.update.download') }}
                  </button>
                  <button class="btn btn--primary" @click="installUpdate" :disabled="!canInstall">
                    {{ t('settings.update.installRestart') }}
                  </button>
                </div>

                <div class="progress" v-if="isDownloading">
                  <div class="progress-bar" :style="{ width: `${Math.max(0, Math.min(100, updateState.percent || 0))}%` }"></div>
                </div>

                <p class="muted">{{ updateState.message }}</p>
                <p class="muted" v-if="!appMeta.packaged">{{ t('settings.update.devHint') }}</p>
              </div>
            </template>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useNotifyStore } from '@/stores/notifyStore'
import { useI18n } from '@/i18n'
import { useUIStore, type ThemeMode } from '@/stores/uiStore'

const emit = defineEmits<{ close: [] }>()

type TabKey = 'general' | 'data' | 'backup' | 'update'

interface AppConfig {
  dataDirectory: string
  autoBackup: boolean
  backupDirectory: string
  maxBackups: number
  updateAutoCheck: boolean
  embeddingMode: string
  embeddingModel: string
}

interface BackupInfo {
  filename: string
  path: string
  size: number
  createdAt: number
}

interface DbStats {
  noteCount: number
  categoryCount: number
  dbSize: number
}

interface ImageStats {
  count: number
  totalSize: number
}

type UpdaterStage =
  | 'idle'
  | 'checking'
  | 'available'
  | 'not-available'
  | 'downloading'
  | 'downloaded'
  | 'error'
  | 'disabled-dev'

interface UpdaterState {
  stage: UpdaterStage
  message: string
  currentVersion: string
  availableVersion?: string
  percent?: number
  autoCheck: boolean
}

const { t, locale, setLocale } = useI18n()
const uiStore = useUIStore()
const notify = useNotifyStore()

const activeTab = ref<TabKey>('general')
const appMeta = ref({ name: 'LmNotebook', version: '1.0.0', packaged: false })
const config = ref<AppConfig>({
  dataDirectory: '',
  autoBackup: true,
  backupDirectory: '',
  maxBackups: 10,
  updateAutoCheck: true,
  embeddingMode: 'api',
  embeddingModel: 'text-embedding-v3'
})
const stats = ref<DbStats>({ noteCount: 0, categoryCount: 0, dbSize: 0 })
const imageStats = ref<ImageStats>({ count: 0, totalSize: 0 })
const backups = ref<BackupInfo[]>([])
const isCreatingBackup = ref(false)
const defaultDirectory = ref('')
const updateState = ref<UpdaterState>({
  stage: 'idle',
  message: t('settings.update.ready'),
  currentVersion: appMeta.value.version,
  autoCheck: true
})
const localeDropdownRef = ref<HTMLElement | null>(null)
const localeDropdownOpen = ref(false)
const embeddingModeDropdownRef = ref<HTMLElement | null>(null)
const embeddingModeDropdownOpen = ref(false)
const backupCountDropdownRef = ref<HTMLElement | null>(null)
const backupCountDropdownOpen = ref(false)
const backupCountOptions = [5, 10, 20, 50]

let unsubscribeUpdater: (() => void) | null = null

const tabs = computed(() => [
  { key: 'general' as const, label: t('settings.tabs.general') },
  { key: 'data' as const, label: t('settings.tabs.data') },
  { key: 'backup' as const, label: t('settings.tabs.backup') },
  { key: 'update' as const, label: t('settings.tabs.update') }
])

const isDefaultDirectory = computed(() => config.value.dataDirectory === defaultDirectory.value)
const isChecking = computed(() => updateState.value.stage === 'checking')
const isDownloading = computed(() => updateState.value.stage === 'downloading')
const canDownload = computed(() => updateState.value.stage === 'available')
const canInstall = computed(() => updateState.value.stage === 'downloaded')
const updaterStageLabel = computed(() => {
  const map: Record<UpdaterStage, string> = {
    idle: t('settings.update.stageIdle'),
    checking: t('settings.update.stageChecking'),
    available: t('settings.update.stageAvailable'),
    'not-available': t('settings.update.stageLatest'),
    downloading: t('settings.update.stageDownloading'),
    downloaded: t('settings.update.stageDownloaded'),
    error: t('settings.update.stageError'),
    'disabled-dev': t('settings.update.stageDisabled')
  }
  return map[updateState.value.stage] || updateState.value.stage
})
const localeLabel = computed(() => (locale.value === 'zh-CN' ? t('language.zh-CN') : t('language.en-US')))
const embeddingModeLabel = computed(() => (config.value.embeddingMode === 'local' ? 'Local' : 'API'))

function setLocaleFromMenu(value: 'zh-CN' | 'en-US'): void {
  setLocale(value)
  localeDropdownOpen.value = false
}

async function setBackupCount(value: number): Promise<void> {
  config.value.maxBackups = value
  backupCountDropdownOpen.value = false
  await saveConfig()
}

async function setEmbeddingMode(mode: 'api' | 'local'): Promise<void> {
  if (config.value.embeddingMode === mode) {
    embeddingModeDropdownOpen.value = false
    return
  }
  config.value.embeddingMode = mode
  embeddingModeDropdownOpen.value = false
  await saveConfig()
}

function handleGlobalPointerDown(event: MouseEvent): void {
  const target = event.target as Node
  if (localeDropdownOpen.value && !localeDropdownRef.value?.contains(target)) {
    localeDropdownOpen.value = false
  }
  if (embeddingModeDropdownOpen.value && !embeddingModeDropdownRef.value?.contains(target)) {
    embeddingModeDropdownOpen.value = false
  }
  if (backupCountDropdownOpen.value && !backupCountDropdownRef.value?.contains(target)) {
    backupCountDropdownOpen.value = false
  }
}

function setTheme(mode: ThemeMode): void {
  uiStore.setTheme(mode)
}

onMounted(async () => {
  await Promise.all([
    loadAppMeta(),
    loadConfig(),
    loadStats(),
    loadImageStats(),
    loadBackups(),
    loadDefaultDirectory(),
    loadUpdaterState()
  ])

  if (window.electronAPI.updater?.onStatus) {
    unsubscribeUpdater = window.electronAPI.updater.onStatus((state) => {
      updateState.value = state
    })
  }
  document.addEventListener('mousedown', handleGlobalPointerDown)
})

onBeforeUnmount(() => {
  unsubscribeUpdater?.()
  document.removeEventListener('mousedown', handleGlobalPointerDown)
})

async function loadAppMeta(): Promise<void> {
  const meta = await window.electronAPI.app.getMeta()
  appMeta.value = meta
}

async function loadConfig(): Promise<void> {
  config.value = await window.electronAPI.config.get()
}

async function loadStats(): Promise<void> {
  stats.value = await window.electronAPI.db.getStats()
}

async function loadImageStats(): Promise<void> {
  imageStats.value = await window.electronAPI.image.getStats()
}

async function loadBackups(): Promise<void> {
  backups.value = await window.electronAPI.backup.list()
}

async function loadDefaultDirectory(): Promise<void> {
  defaultDirectory.value = await window.electronAPI.db.getDefaultDataPath()
}

async function loadUpdaterState(): Promise<void> {
  if (!window.electronAPI.updater?.getState) return
  updateState.value = await window.electronAPI.updater.getState()
}

async function saveConfig(): Promise<void> {
  config.value = await window.electronAPI.config.save(config.value)
}

async function saveEmbeddingModel(): Promise<void> {
  const trimmed = (config.value.embeddingModel || '').trim()
  config.value.embeddingModel = trimmed || 'text-embedding-v3'
  await saveConfig()
}

async function handleUpdateAutoCheck(event: Event): Promise<void> {
  const enabled = (event.target as HTMLInputElement).checked
  updateState.value = await window.electronAPI.updater.setAutoCheck(enabled)
  config.value = await window.electronAPI.config.save({ updateAutoCheck: enabled })
}

async function checkUpdates(): Promise<void> {
  try {
    updateState.value = await window.electronAPI.updater.checkForUpdates()
  } catch (error) {
    notify.add(`妫€鏌ユ洿鏂板け璐? ${error instanceof Error ? error.message : String(error)}`, 'error')
  }
}

async function downloadUpdate(): Promise<void> {
  try {
    updateState.value = await window.electronAPI.updater.downloadUpdate()
  } catch (error) {
    notify.add(`涓嬭浇鏇存柊澶辫触: ${error instanceof Error ? error.message : String(error)}`, 'error')
  }
}

async function installUpdate(): Promise<void> {
  const confirmed = confirm(t('settings.update.confirmInstall'))
  if (!confirmed) return
  await window.electronAPI.updater.quitAndInstall()
}

async function selectDataDirectory(): Promise<void> {
  const result = await window.electronAPI.dialog.selectDirectory({
    title: t('settings.data.pickDirectory'),
    defaultPath: config.value.dataDirectory
  })

  if (result.success && result.path) {
    const confirmMove = confirm(
      `${t('settings.data.confirmMove')}\n\n${result.path}\n\n${t('settings.data.willRestart')}`
    )

    if (confirmMove) {
      const migrateResult = await window.electronAPI.data.migrate(result.path)
      if (!migrateResult.success) {
        notify.add(`杩佺Щ澶辫触: ${migrateResult.error}`, 'error')
      }
    }
  }
}

async function openDataDirectory(): Promise<void> {
  await window.electronAPI.shell.openPath(config.value.dataDirectory)
}

async function resetToDefault(): Promise<void> {
  const confirmed = confirm(
    `${t('settings.data.confirmReset')}\n\n${defaultDirectory.value}\n\n${t('settings.data.willRestart')}`
  )

  if (confirmed) {
    const result = await window.electronAPI.data.migrate(defaultDirectory.value)
    if (!result.success) {
      notify.add(`鎭㈠澶辫触: ${result.error}`, 'error')
    }
  }
}

async function createBackup(): Promise<void> {
  isCreatingBackup.value = true
  try {
    const result = await window.electronAPI.backup.create()
    if (result) {
      await loadBackups()
      notify.add(t('settings.backup.createSuccess'), 'success')
    } else {
      notify.add(t('settings.backup.createFailed'), 'error')
    }
  } finally {
    isCreatingBackup.value = false
  }
}

async function restoreBackup(backup: BackupInfo): Promise<void> {
  const confirmed = confirm(`${t('settings.backup.confirmRestore')}\n\n${backup.filename}`)
  if (!confirmed) return

  const success = await window.electronAPI.backup.restore(backup.path)
  if (success) {
    notify.add(t('settings.backup.restoreSuccess'), 'success', 6000)
    emit('close')
  } else {
    notify.add(t('settings.backup.restoreFailed'), 'error')
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleString(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 50000;
  background: color-mix(in srgb, #0f172a 24%, transparent);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.settings-modal {
  width: min(980px, calc(100vw - 44px));
  height: min(700px, calc(100vh - 44px));
  background: var(--color-bg-card);
  border: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.16);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.settings-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
}

.settings-title {
  font-size: 18px;
  line-height: 1.25;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.settings-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.icon-btn {
  width: 30px;
  height: 30px;
  border: 1px solid color-mix(in srgb, var(--color-border) 64%, transparent);
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
}

.settings-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 180px 1fr;
}

.settings-nav {
  border-right: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.settings-nav-item {
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  text-align: left;
  padding: 9px 10px;
  border-radius: 8px;
  cursor: pointer;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }

  &--active {
    border-color: color-mix(in srgb, var(--color-border) 66%, transparent);
    background: color-mix(in srgb, var(--color-bg-hover) 90%, transparent);
    color: var(--color-text-primary);
  }
}

.settings-panel {
  padding: 12px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.settings-card {
  border: 1px solid color-mix(in srgb, var(--color-border) 62%, transparent);
  border-radius: 10px;
  padding: 12px;
  background: color-mix(in srgb, var(--color-bg-primary) 97%, transparent);
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;

  &:not(:last-child) {
    border-bottom: 1px solid color-mix(in srgb, var(--color-border) 42%, transparent);
  }

  h3 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  p {
    margin: 3px 0 0;
    font-size: 12px;
    color: var(--color-text-muted);
  }
}

.settings-row--stackable {
  align-items: flex-start;
}

.segmented {
  display: inline-flex;
  align-items: center;
  border: 1px solid color-mix(in srgb, var(--color-border) 64%, transparent);
  border-radius: 9px;
  overflow: hidden;
  background: color-mix(in srgb, var(--color-bg-hover) 48%, transparent);
}

.segmented__item {
  height: 30px;
  padding: 0 10px;
  border: none;
  border-right: 1px solid color-mix(in srgb, var(--color-border) 54%, transparent);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.14s ease, color 0.14s ease;
}

.segmented__item:last-child {
  border-right: none;
}

.segmented__item:hover {
  color: var(--color-text-primary);
  background: color-mix(in srgb, var(--color-bg-hover) 88%, transparent);
}

.segmented__item--active {
  color: var(--color-text-primary);
  background: color-mix(in srgb, var(--color-bg-primary) 92%, transparent);
  font-weight: 600;
}

.card-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  border: 1px solid color-mix(in srgb, var(--color-border) 66%, transparent);
  background: color-mix(in srgb, var(--color-bg-hover) 90%, transparent);
  border-radius: 999px;
  padding: 4px 10px;
}

.badge--muted {
  opacity: 0.75;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-item {
  border: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
  color: var(--color-text-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.path-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin-top: 10px;
}

.action-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.backup-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid color-mix(in srgb, var(--color-border) 56%, transparent);
  border-radius: 10px;
  padding: 8px 10px;
}

.backup-name {
  font-size: 12px;
  color: var(--color-text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.backup-meta {
  margin-top: 2px;
  font-size: 11px;
  color: var(--color-text-muted);
}

.update-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0 8px;
}

.progress {
  height: 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg-hover) 92%, transparent);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--color-border) 52%, transparent);
  margin-bottom: 8px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #111827 0%, #374151 100%);
  transition: width 200ms ease;
}

.muted {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.about-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.about-item {
  border: 1px solid color-mix(in srgb, var(--color-border) 54%, transparent);
  border-radius: 10px;
  padding: 10px;
  background: color-mix(in srgb, var(--color-bg-hover) 42%, transparent);

  h4 {
    margin: 0 0 4px;
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  p {
    margin: 0;
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-text-muted);
  }
}

.input,
.select,
.btn {
  height: 32px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--color-border) 64%, transparent);
  background: transparent;
  color: var(--color-text-primary);
  font-size: 12px;
}

.dropdown-select {
  position: relative;
  min-width: 116px;
}

.dropdown-select__trigger {
  width: 100%;
  height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--color-border) 64%, transparent);
  background: transparent;
  color: var(--color-text-primary);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  cursor: pointer;
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.dropdown-select__trigger:hover {
  background: var(--color-bg-hover);
}

.dropdown-select__trigger--open {
  border-color: color-mix(in srgb, var(--color-accent) 46%, var(--color-border));
}

.dropdown-select__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-select__caret {
  color: var(--color-text-muted);
  transition: transform 0.14s ease;
}

.dropdown-select__trigger--open .dropdown-select__caret {
  transform: rotate(180deg);
}

.dropdown-select__menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 52000;
  width: 100%;
  min-width: 140px;
  max-height: 240px;
  overflow-y: auto;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--color-border) 64%, transparent);
  background: color-mix(in srgb, var(--color-bg-card) 96%, transparent);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.dropdown-select__item {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 8px 10px;
  text-align: left;
  font-size: 12px;
  color: var(--color-text-primary);
  cursor: pointer;
}

.dropdown-select__item:hover {
  background: var(--color-bg-hover);
}

.dropdown-select__item--active {
  background: color-mix(in srgb, var(--color-accent) 12%, transparent);
  color: color-mix(in srgb, var(--color-accent) 74%, var(--color-text-primary));
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.input {
  padding: 0 10px;
}

.select {
  padding: 0 10px;
  min-width: 100px;
}

.btn {
  padding: 0 12px;
  cursor: pointer;

  &:hover {
    background: var(--color-bg-hover);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn--primary {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(90deg, #111827 0%, #1f2937 100%);

  &:hover {
    opacity: 0.9;
    background: linear-gradient(90deg, #111827 0%, #1f2937 100%);
  }
}

.btn--ghost {
  background: transparent;
}

.switch {
  position: relative;
  width: 40px;
  height: 22px;

  input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  span {
    position: absolute;
    inset: 0;
    border-radius: 999px;
    background: color-mix(in srgb, var(--color-border) 74%, transparent);
    transition: background 0.16s ease;

    &::before {
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #fff;
      transition: transform 0.16s ease;
    }
  }

  input:checked + span {
    background: #111827;

    &::before {
      transform: translateX(18px);
    }
  }
}

@media (max-width: 900px) {
  .settings-modal {
    width: min(100vw, 100vw);
    height: min(100vh, 100vh);
    border-radius: 0;
  }

  .settings-main {
    grid-template-columns: 1fr;
  }

  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
    border-right: none;
    border-bottom: 1px solid color-mix(in srgb, var(--color-border) 58%, transparent);
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .about-grid {
    grid-template-columns: 1fr;
  }

  .settings-row--stackable {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

