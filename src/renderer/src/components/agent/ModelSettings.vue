<template>
  <div class="settings-overlay" @click.self="$emit('close')">
    <div class="settings-modal glass-panel">
      <!-- Sidebar -->
      <div class="settings-sidebar">
        <div class="sidebar-header">
          <h3>模型设置</h3>
          <p>配置 AI 服务提供商</p>
        </div>
        <div class="provider-list">
          <div 
            v-for="p in providers" 
            :key="p.id"
            class="provider-item"
            :class="{ 
              'active': selectedProvider?.id === p.id,
              'dragging': draggedId === p.id,
              'dragover': dragOverId === p.id && !p.isActive
            }"
            draggable="true"
            @click="selectedProvider = p"
            @dragstart="handleDragStart($event, p.id, p.isActive)"
            @dragover.prevent="handleDragOver($event, p.id, p.isActive)"
            @dragleave="handleDragLeave"
            @drop="handleDrop($event, p.id, p.isActive)"
            @dragend="handleDragEnd"
          >
            <div class="provider-icon">
              {{ p.name ? p.name.charAt(0).toUpperCase() : '?' }}
            </div>
            <div class="provider-info">
              <span class="provider-name">{{ p.name }}</span>
              <span v-if="p.isActive" class="active-badge">使用中</span>
            </div>
          </div>
            <button class="add-btn" @mousedown.stop @click.stop="addNewProvider">
            <span>+ 添加提供商</span>
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="settings-content" v-if="selectedProvider" @mousedown.stop>
        <div class="content-header">
          <h2>{{ isNew ? '添加提供商' : '配置提供商' }}</h2>
          <div class="header-actions" v-if="!isNew">
            <button 
              class="action-btn use-btn" 
              :disabled="selectedProvider.isActive"
              @click.stop="setActiveProvider(selectedProvider.id)"
            >
              {{ selectedProvider.isActive ? '正在使用' : '设为活动' }}
            </button>
            <button class="action-btn delete-btn" @click.stop="deleteProvider(selectedProvider.id)">
              删除
            </button>
          </div>
        </div>

        <div class="settings-form">
          <div class="form-group">
            <label>提供商名称</label>
            <input v-model="selectedProvider.name" placeholder="例如: DeepSeek, OpenAI..." />
          </div>
          
          <div class="form-group">
            <label>API 地址 (Base URL)</label>
            <input v-model="selectedProvider.baseUrl" placeholder="https://api.openai.com/v1" />
            <span class="hint">必须符合 OpenAI 兼容协议</span>
          </div>

          <div class="form-group">
            <label>API 密钥</label>
            <div class="password-input">
              <input 
                :type="showKey ? 'text' : 'password'" 
                v-model="selectedProvider.apiKey" 
                placeholder="sk-..." 
              />
              <button @click="showKey = !showKey" class="toggle-btn">
                {{ showKey ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>模型名称</label>
            <input v-model="selectedProvider.modelName" placeholder="例如: deepseek-chat, gpt-4o..." />
          </div>
        </div>

        <div class="content-footer">
          <button class="save-btn" @click="saveProvider" :disabled="!isValid">
            保存配置
          </button>
        </div>
      </div>
      <div v-else class="empty-state">
        <span class="empty-icon">✦</span>
        <p>请选择或添加一个提供商</p>
      </div>
      
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const props = defineProps<{
  backendUrl: string
}>()

const emit = defineEmits(['close', 'updated'])

interface Provider {
  id: string
  name: string
  baseUrl: string
  apiKey: string
  modelName: string
  isActive: boolean
}

const providers = ref<Provider[]>([])
const selectedProvider = ref<Provider | null>(null)
const isNew = ref(false)
const showKey = ref(false)

// Drag and Drop state
const draggedId = ref<string | null>(null)
const dragOverId = ref<string | null>(null)

const isValid = computed(() => {
  if (!selectedProvider.value) return false
  const p = selectedProvider.value
  return p.name && p.baseUrl && p.apiKey && p.modelName
})

async function fetchProviders() {
  try {
    const res = await fetch(`${props.backendUrl}/api/models/providers`)
    if (!res.ok) {
      console.error('Failed to fetch providers, status:', res.status)
      providers.value = []
      return
    }
    const data = await res.json()
    let rawProviders = Array.isArray(data) ? data : []
    
    // 🔝 Sticky Active: Ensure active provider is ALWAYS at the top
    // For non-active items, preserve original order (stable sort)
    providers.value = rawProviders.sort((a, b) => {
      if (a.isActive && !b.isActive) return -1
      if (!a.isActive && b.isActive) return 1
      return 0
    })

    if (providers.value.length > 0 && !selectedProvider.value) {
      selectedProvider.value = JSON.parse(JSON.stringify(providers.value.find(p => p.isActive) || providers.value[0]))
    }
  } catch (e) {
    console.error('Failed to fetch providers:', e)
    providers.value = []
  }
}

function addNewProvider() {
  console.log('Adding new provider...')
  isNew.value = true
  selectedProvider.value = {
    id: '',
    name: '新建提供商',
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '',
    modelName: 'gpt-4o-mini',
    isActive: false
  }
}

async function saveProvider() {
  if (!selectedProvider.value) return
  
  const url = isNew.value 
    ? `${props.backendUrl}/api/models/providers` 
    : `${props.backendUrl}/api/models/providers/${selectedProvider.value.id}`
  
  const method = isNew.value ? 'POST' : 'PUT'

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(selectedProvider.value)
    })
    
    if (res.ok) {
      isNew.value = false
      await fetchProviders()
      emit('updated')
    }
  } catch (e) {
    console.error('Failed to save provider:', e)
  }
}

async function setActiveProvider(id: string) {
  try {
    await fetch(`${props.backendUrl}/api/models/providers/${id}/active`, { method: 'POST' })
    await fetchProviders()
    emit('updated')
  } catch (e) {
    console.error('Failed to set active provider:', e)
  }
}

async function deleteProvider(id: string) {
  if (!confirm('确定要删除此提供商吗？')) return
  try {
    await fetch(`${props.backendUrl}/api/models/providers/${id}`, { method: 'DELETE' })
    selectedProvider.value = null
    await fetchProviders()
    emit('updated')
  } catch (e) {
    console.error('Failed to delete provider:', e)
  }
}

// Drag and Drop Handlers
function handleDragStart(e: DragEvent, id: string, isActive: boolean) {
  if (isActive) {
    e.preventDefault()
    return
  }

  draggedId.value = id
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', id)
  }
}

function handleDragOver(e: DragEvent, id: string, isActive: boolean) {
  if (draggedId.value === id || isActive) return
  dragOverId.value = id
}

function handleDragLeave() {
  dragOverId.value = null
}

async function handleDrop(e: DragEvent, targetId: string, isActive: boolean) {
  if (!draggedId.value || draggedId.value === targetId || isActive) return
  
  try {
    const res = await fetch(`${props.backendUrl}/api/models/providers/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draggedId: draggedId.value,
        targetId: targetId
      })
    })
    
    if (res.ok) {
      await fetchProviders()
    }
  } catch (err) {
    console.error('Failed to reorder providers:', err)
  }
}

function handleDragEnd() {
  draggedId.value = null
  dragOverId.value = null
}

onMounted(fetchProviders)
</script>

<style scoped>
.settings-overlay {
  /* Light Theme Variables (Default) */
  --theme-bg: #FAF8F5;
  --theme-bg-secondary: rgba(245, 241, 236, 0.5);
  --theme-bg-card: #FFFFFF;
  --theme-text: #2D2A26;
  --theme-text-secondary: #6B6762;
  --theme-accent: #D97D54;
  --theme-border: #E8E4DF;
  --theme-input-bg: rgba(255, 255, 255, 0.8);

  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  animation: fadeIn 0.2s ease-out;
}

/* Dark Theme Override */
[data-theme="dark"] .settings-overlay {
  --theme-bg: #2A2A2E;
  --theme-bg-secondary: rgba(35, 35, 38, 0.8);
  --theme-bg-card: #333338;
  --theme-text: #E8E8E6;
  --theme-text-secondary: #A8A8A5;
  --theme-accent: #E8A87C;
  --theme-border: #3A3A3E;
  --theme-input-bg: rgba(50, 50, 55, 0.8);
}

/* Classic Theme Override */
[data-theme="classic"] .settings-overlay {
  --theme-bg: #FFFFFF;
  --theme-bg-secondary: rgba(255, 255, 255, 1);
  --theme-bg-card: #FFFFFF;
  --theme-text: #1F1F1F;
  --theme-text-secondary: #666666;
  --theme-accent: #555555;
  --theme-border: #F0F0F0;
  --theme-input-bg: rgba(0, 0, 0, 0.02);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.settings-modal {
  width: 800px;
  height: 600px;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  overflow: hidden;
  position: relative;
  background: var(--theme-bg);
  border: 1px solid var(--theme-border);
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.15);
  transition: background 0.3s ease, border-color 0.3s ease;
}

/* Sidebar */
.settings-sidebar {
  width: 240px;
  border-right: 1px solid var(--theme-border);
  display: flex;
  flex-direction: column;
  background: var(--theme-bg-secondary);
  transition: background 0.3s ease, border-color 0.3s ease;
}

.sidebar-header {
  padding: 24px;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--theme-text);
}

.sidebar-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--theme-text-secondary);
}

.provider-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.provider-item:hover {
  background: var(--theme-border);
}

.provider-item.active {
  background: var(--theme-bg-card);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.provider-item.dragging {
  opacity: 0.5;
  background: rgba(217, 125, 84, 0.1);
}

.provider-item.dragover {
  border-top: 2px solid var(--theme-accent);
  background: rgba(217, 125, 84, 0.05);
}

.provider-icon {
  width: 32px;
  height: 32px;
  background: var(--theme-accent);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.provider-info {
  display: flex;
  flex-direction: column;
}

.provider-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--theme-text);
}

.active-badge {
  font-size: 10px;
  color: #5BA37B;
  background: #E6F4EA;
  padding: 1px 6px;
  border-radius: 4px;
  width: fit-content;
  margin-top: 2px;
}

[data-theme="dark"] .active-badge {
  color: #70B870;
  background: rgba(112, 184, 112, 0.15);
}

.add-btn {
  width: 100%;
  padding: 12px;
  margin-top: 8px;
  background: transparent;
  border: 1px dashed var(--theme-text-secondary);
  border-radius: 8px;
  color: var(--theme-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  border-color: var(--theme-accent);
  color: var(--theme-accent);
}

/* Content */
.settings-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-right: 40px; /* Avoid overlap with close button */
}

.content-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--theme-text);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid var(--theme-border);
  background: var(--theme-bg-card);
  color: var(--theme-text);
  transition: all 0.2s;
}

.use-btn:not(:disabled):hover {
  background: #5BA37B;
  color: white;
  border-color: #5BA37B;
}

.delete-btn:hover {
  background: rgba(229, 62, 62, 0.1);
  color: #e53e3e;
  border-color: #e53e3e;
}

.settings-form {
  flex: 1;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--theme-text-secondary);
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--theme-input-bg);
  color: var(--theme-text);
  outline: none;
  transition: border-color 0.2s, background 0.3s ease;
}

.form-group input:focus {
  border-color: var(--theme-accent);
}

.form-group input::placeholder {
  color: var(--theme-text-secondary);
  opacity: 0.6;
}

.hint {
  display: block;
  font-size: 12px;
  color: var(--theme-text-secondary);
  margin-top: 4px;
}

.password-input {
  position: relative;
}

.toggle-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 12px;
  color: var(--theme-accent);
  cursor: pointer;
}

.save-btn {
  margin-top: 24px;
  width: 100%;
  padding: 14px;
  background: var(--theme-accent);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  font-size: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--theme-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: var(--theme-border);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--theme-text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--theme-accent);
}
</style>
