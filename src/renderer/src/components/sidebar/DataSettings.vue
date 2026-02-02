<template>
  <Teleport to="body">
    <div class="settings-overlay" @click.self="$emit('close')">
      <div class="settings-modal" @click.stop>
        <div class="settings-header">
          <h2>数据设置</h2>
          <button class="close-btn" @click="$emit('close')">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="settings-content">
          <!-- 数据统计 -->
          <section class="settings-section">
            <h3>数据统计</h3>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-value">{{ stats.noteCount }}</span>
                <span class="stat-label">笔记数量</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ stats.categoryCount }}</span>
                <span class="stat-label">分类数量</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatSize(stats.dbSize) }}</span>
                <span class="stat-label">数据库大小</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ imageStats.count }}</span>
                <span class="stat-label">分离图片</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatSize(imageStats.totalSize) }}</span>
                <span class="stat-label">图片占用</span>
              </div>
            </div>
            <p class="section-hint" v-if="imageStats.count > 0">
              大于 100KB 的图片会自动分离存储到 images 目录
            </p>
          </section>

          <!-- 数据目录 -->
          <section class="settings-section">
            <h3>数据存储位置</h3>
            <p class="section-desc">将数据目录设置到云盘文件夹（如 OneDrive、Dropbox）可实现自动云同步</p>
            <div class="path-input">
              <input type="text" :value="config.dataDirectory" readonly class="input" />
              <button class="btn btn--secondary" @click="selectDataDirectory">更改</button>
            </div>
            <div class="path-actions">
              <button class="btn btn--link" @click="openDataDirectory">在文件管理器中打开</button>
              <button class="btn btn--link btn--warning" @click="resetToDefault" v-if="!isDefaultDirectory">恢复默认目录</button>
            </div>
          </section>

          <!-- 自动备份 -->
          <section class="settings-section">
            <h3>自动备份</h3>
            <div class="toggle-row">
              <span>启用自动备份</span>
              <label class="toggle">
                <input type="checkbox" v-model="config.autoBackup" @change="saveConfig" />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="form-row" v-if="config.autoBackup">
              <label>最大备份数量</label>
              <select v-model.number="config.maxBackups" @change="saveConfig" class="select">
                <option :value="5">5 个</option>
                <option :value="10">10 个</option>
                <option :value="20">20 个</option>
                <option :value="50">50 个</option>
              </select>
            </div>
          </section>

          <!-- 备份管理 -->
          <section class="settings-section">
            <h3>备份管理</h3>
            <div class="backup-actions">
              <button class="btn btn--primary" @click="createBackup" :disabled="isCreatingBackup">
                {{ isCreatingBackup ? '备份中...' : '立即备份' }}
              </button>
            </div>
            
            <div class="backup-list" v-if="backups.length > 0">
              <div class="backup-item" v-for="backup in backups" :key="backup.filename">
                <div class="backup-info">
                  <span class="backup-name">{{ backup.filename }}</span>
                  <span class="backup-meta">{{ formatSize(backup.size) }} · {{ formatDate(backup.createdAt) }}</span>
                </div>
                <button class="btn btn--sm btn--secondary" @click="restoreBackup(backup)">恢复</button>
              </div>
            </div>
            <p class="empty-text" v-else>暂无备份</p>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const emit = defineEmits<{
  close: []
}>()

interface AppConfig {
  dataDirectory: string
  autoBackup: boolean
  backupDirectory: string
  maxBackups: number
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

const config = ref<AppConfig>({
  dataDirectory: '',
  autoBackup: true,
  backupDirectory: '',
  maxBackups: 10
})

const stats = ref<DbStats>({
  noteCount: 0,
  categoryCount: 0,
  dbSize: 0
})

const imageStats = ref<ImageStats>({
  count: 0,
  totalSize: 0
})

const backups = ref<BackupInfo[]>([])
const isCreatingBackup = ref(false)
const defaultDirectory = ref('')

// 计算是否为默认目录
const isDefaultDirectory = computed(() => {
  return config.value.dataDirectory === defaultDirectory.value
})

onMounted(async () => {
  await loadConfig()
  await loadStats()
  await loadImageStats()
  await loadBackups()
  // 获取默认目录路径
  defaultDirectory.value = await window.electronAPI.db.getDefaultDataPath()
})

async function loadConfig() {
  config.value = await window.electronAPI.config.get()
}

async function loadStats() {
  stats.value = await window.electronAPI.db.getStats()
}

async function loadImageStats() {
  imageStats.value = await window.electronAPI.image.getStats()
}

async function loadBackups() {
  backups.value = await window.electronAPI.backup.list()
}

async function saveConfig() {
  await window.electronAPI.config.save(config.value)
}

async function selectDataDirectory() {
  const result = await window.electronAPI.dialog.selectDirectory({
    title: '选择数据存储目录',
    defaultPath: config.value.dataDirectory
  })
  
  if (result.success && result.path) {
    const confirmMove = confirm(
      `确定要将数据迁移到新目录吗？\n\n新目录: ${result.path}\n\n迁移后应用将重启。`
    )
    
    if (confirmMove) {
      const migrateResult = await window.electronAPI.data.migrate(result.path)
      if (!migrateResult.success) {
        alert(`迁移失败: ${migrateResult.error}`)
      }
    }
  }
}

async function openDataDirectory() {
  await window.electronAPI.shell.openPath(config.value.dataDirectory)
}

async function resetToDefault() {
  const confirmed = confirm(
    `确定要恢复到默认目录吗？\n\n默认目录: ${defaultDirectory.value}\n\n数据将迁移回默认位置，应用将重启。`
  )
  
  if (confirmed) {
    const result = await window.electronAPI.data.migrate(defaultDirectory.value)
    if (!result.success) {
      alert(`恢复失败: ${result.error}`)
    }
  }
}

async function createBackup() {
  isCreatingBackup.value = true
  try {
    const result = await window.electronAPI.backup.create()
    if (result) {
      await loadBackups()
      alert('备份创建成功!')
    } else {
      alert('备份创建失败')
    }
  } finally {
    isCreatingBackup.value = false
  }
}

async function restoreBackup(backup: BackupInfo) {
  const confirmed = confirm(
    `确定要从此备份恢复吗？\n\n${backup.filename}\n\n当前数据将被覆盖，恢复后需要重启应用。`
  )
  
  if (confirmed) {
    const success = await window.electronAPI.backup.restore(backup.path)
    if (success) {
      alert('备份恢复成功！\n\n请关闭并重新打开应用以加载恢复的数据。')
      // 关闭设置弹窗
      emit('close')
    } else {
      alert('备份恢复失败，请重试。')
    }
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleString('zh-CN', {
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
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.settings-modal {
  background: var(--color-bg-card);
  border-radius: 12px;
  width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-light);
  
  h2 {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  
  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.settings-section {
  margin-bottom: 28px;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  h3 {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 12px;
  }
}

.section-desc {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
  line-height: 1.5;
}

.section-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
  border-left: 3px solid var(--color-accent, #6366F1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.path-input {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  
  .input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid var(--color-border-dark);
    border-radius: 8px;
    background: var(--color-bg-secondary);
    color: var(--color-text-primary);
    font-size: 13px;
  }
}

.path-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  
  input {
    opacity: 0;
    width: 0;
    height: 0;
  }
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--color-border-dark);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
  
  &::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    left: 3px;
    top: 3px;
    background: white;
    border-radius: 50%;
    transition: transform 0.2s;
  }
  
  input:checked + & {
    background: #10B981;
    
    &::before {
      transform: translateX(20px);
    }
  }
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  
  label {
    color: var(--color-text-secondary);
    font-size: 14px;
  }
}

.select {
  padding: 8px 12px;
  border: 1px solid var(--color-border-dark);
  border-radius: 8px;
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 13px;
  cursor: pointer;
}

.backup-actions {
  margin-bottom: 16px;
}

.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.backup-name {
  font-size: 13px;
  color: var(--color-text-primary);
  font-family: monospace;
}

.backup-meta {
  font-size: 12px;
  color: var(--color-text-muted);
}

.empty-text {
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: center;
  padding: 20px;
}

// 按钮样式
.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &--primary {
    background: var(--color-accent, #6366F1);
    color: white;
    
    &:hover:not(:disabled) {
      opacity: 0.9;
    }
  }
  
  &--secondary {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
    
    &:hover:not(:disabled) {
      background: var(--color-bg-active);
    }
  }
  
  &--link {
    background: transparent;
    color: var(--color-accent, #6366F1);
    padding: 4px 0;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  &--warning {
    color: #F59E0B;
  }
  
  &--sm {
    padding: 6px 12px;
    font-size: 13px;
  }
}
</style>
