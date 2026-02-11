<template>
  <!-- Main Container with dynamic position -->
  <div 
    class="agent-container" 
    :style="containerStyle"
    :class="{ 'is-dragging': isDragging, 'is-docked': isDocked && !isOpen, 'agent-container--sidebar': isSidebarMode && isOpen }"
  >
    <!-- Floating Bubble Button -->
    <div
      v-if="!(isSidebarMode && isOpen)"
      class="agent-bubble glass-panel"
      :class="{ 'agent-bubble--active': isOpen }"
      @mousedown="startDrag"
      @click.stop="handleClick"
    >
      <div class="agent-bubble__icon">
        <!-- Origin asterisk logo -->
        <svg v-if="!isOpen" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L13.09 8.26L18 4L14.74 9.91L21 10.91L14.74 12.09L18 18L13.09 13.74L12 20L10.91 13.74L6 18L9.26 12.09L3 10.91L9.26 9.91L6 4L10.91 8.26L12 2Z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </div>
      <div v-if="hasUnread" class="agent-bubble__badge"></div>
    </div>

    <!-- Chat Window -->
    <Transition name="chat-window">
      <div 
        v-if="isOpen" 
        class="agent-chat glass-panel" 
        ref="chatWindowRef"
        :class="{ 
          'maximized': isMaximized,
          'align-left': !isSidebarMode && position.x < windowWidth / 2,
          'sidebar-mode': isSidebarMode
        }"
        @mousedown.stop
      >
        <!-- Header -->
        <div class="agent-chat__header">
          <div class="agent-chat__title" @mousedown="startDrag" style="cursor: grab;">
            <span class="agent-chat__avatar" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L13.09 8.26L18 4L14.74 9.91L21 10.91L14.74 12.09L18 18L13.09 13.74L12 20L10.91 13.74L6 18L9.26 12.09L3 10.91L9.26 9.91L6 4L10.91 8.26L12 2Z"/>
              </svg>
            </span>
            <span>{{ t('agent.title') }}</span>
          </div>
          <div class="agent-chat__actions">
            <button 
              class="header-btn" 
              @click="showModelSettings = true; console.log('Settings toggle')" 
              :title="t('agent.modelSettings')"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="toggleSessionHistory" :title="t('agent.history')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="clearChat" :title="t('agent.newSession')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="toggleSidebarMode" :title="isSidebarMode ? t('agent.exitSidebarMode') : t('agent.sidebarMode')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="16" rx="2"/>
                <line x1="9" y1="4" x2="9" y2="20"/>
              </svg>
            </button>
            <button class="header-btn" @mousedown.stop @click="toggleMaximizeMode" :title="isMaximized ? t('agent.restore') : t('agent.maximize')">
              <svg v-if="!isMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="5" y="5" width="14" height="14" rx="2"/>
                <path d="M9 3h10a2 2 0 0 1 2 2v10"/>
              </svg>
            </button>
            <div class="agent-chat__status">
              <span v-if="isConnected" class="status-dot status-dot--online"></span>
              <span v-else class="status-dot status-dot--offline"></span>
            </div>
          </div>
        </div>

        <!-- Session History Panel -->
        <Transition name="slide-panel">
          <div v-if="showSessionHistory" class="session-history-panel">
            <div class="session-history__header">
              <span>{{ t('agent.history') }}</span>
              <button class="close-btn" @click="showSessionHistory = false">×</button>
            </div>
            <div class="session-history__list">
              <div v-if="sessionList.length === 0" class="session-history__empty">
                {{ t('agent.emptyHistory') }}
              </div>
              <div 
                v-for="session in sessionList" 
                :key="session.id"
                class="session-item"
                :class="{ 'session-item--active': session.id === currentSessionId, 'session-item--pinned': session.pinned }"
                @click="editingSessionId !== session.id && loadSession(session.id)"
              >
                <!-- Normal display mode -->
                <div v-if="editingSessionId !== session.id" class="session-item__preview">
                  <span v-if="session.pinned" class="pin-indicator">
                    <svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="12" height="12">
                      <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
                    </svg>
                  </span>
                  {{ session.preview }}
                </div>
                <!-- Editing mode -->
                <input 
                  v-else
                  v-model="editingTitle"
                  class="session-rename-input"
                  @click.stop
                  @keyup.enter="confirmRename(session.id)"
                  @keyup.escape="cancelRename"
                  @blur="confirmRename(session.id)"
                />
                <div v-if="editingSessionId !== session.id" class="session-item__actions">
                  <button class="session-item__btn" @click.stop="togglePinSession(session.id)" :title="session.pinned ? '取消置顶' : '置顶'">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M16 4l4 4-1.5 1.5-1-1L14 12l1 5-2 2-3-4-4 4-1-1 4-4-4-3 2-2 5 1 3.5-3.5-1-1z"/>
                    </svg>
                  </button>
                  <button class="session-item__btn" @click.stop="renameSession(session.id)" title="重命名">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="session-item__btn session-item__btn--danger" @click.stop="deleteSession(session.id)" title="删除">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Messages -->
        <div class="agent-chat__messages" ref="messagesContainer" @scroll="handleMessagesScroll">
          <div v-if="messages.length === 0" class="agent-chat__empty">
            <div class="agent-chat__welcome">
              <span class="welcome-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L13.09 8.26L18 4L14.74 9.91L21 10.91L14.74 12.09L18 18L13.09 13.74L12 20L10.91 13.74L6 18L9.26 12.09L3 10.91L9.26 9.91L6 4L10.91 8.26L12 2Z"/>
                </svg>
              </span>
              <h3>{{ t('agent.welcomeTitle') }}</h3>
              <p>{{ t('agent.welcomeSubtitle') }}</p>
            </div>
            <div class="agent-chat__empty-hint">
              {{ t('agent.emptyHintNoShortcuts') }}
            </div>
          </div>

          <div
            v-for="(msg, index) in messages.filter(m => m.content.trim() || (m.parts && m.parts.length))"
            :key="index"
            class="message-wrapper"
            :class="[`message--${msg.role}`]">
            <div class="message">
              <div class="message__content">
                <!-- Part-Based Rendering -->
                <template v-if="msg.parts && msg.parts.length">
                  <template v-for="(part, partIndex) in msg.parts" :key="partIndex">
                    <!-- Text Part -->
                    <div v-if="part.type === 'text'" 
                         class="message__text" 
                         v-html="renderMarkdown(part.content)"
                         @contextmenu="handleContextMenu($event, part.content)"></div>
                    
                    <!-- Tool Part -->
                    <div v-else-if="part.type === 'tool'" 
                         class="tool-part"
                         :class="[`tool-part--${part.status}`]">
                      <div class="tool-part__main">
                        <div class="tool-part__line">
                          <span class="tool-part__name" :class="{ 'tool-part__name--running': part.status === 'running' }">{{ part.title || part.tool }}</span>
                          <span v-if="part.status === 'pending'" class="tool-part__pending">{{ t('agent.pendingConfirm') }}</span>
                          <span v-else-if="part.status === 'completed'" class="tool-part__check">✓</span>
                          <span v-else-if="part.status === 'error'" class="tool-part__pending">{{ t('agent.failed') }}</span>
                        </div>
                        <span v-if="part.output" class="tool-part__output">{{ formatToolOutput(part.output) }}</span>
                      </div>
                    </div>
                  </template>
                </template>
                
                <!-- Fallback: Legacy content rendering -->
                <template v-else>
                  <div class="message__text" 
                       v-html="renderMarkdown(msg.content)"
                       @contextmenu="handleContextMenu($event, msg.content)"></div>
                </template>
              </div>
            </div>
          </div>

          <div v-if="displayStatusText" class="status-update">
            <span class="status-update__text">{{ displayStatusText }}</span>
            <span v-if="showStatusDots" class="status-update__dots">...</span>
          </div>

          <div v-if="isTyping && !currentStatus" class="typing-minimal">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- Scroll to bottom button -->
        <Transition name="fade">
          <button 
            v-if="showScrollToBottom" 
            class="scroll-to-bottom-btn"
            @click="forceScrollToBottom"
            :title="t('agent.scrollBottom')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </Transition>

        <!-- Context bar moved into composer footer (shadcn-like layout) -->
        <Transition name="panel-elevate">
          <div v-if="isExecutionAwaitingApproval || pendingApprovals.length > 0" class="agent-approval-bar">
            <template v-if="isExecutionAwaitingApproval && pendingExecutionApproval">
              <span class="agent-approval-bar__label">{{ t('agent.pendingExecution', { operation: pendingExecutionApproval.operation, target: pendingExecutionApproval.noteTitle || pendingExecutionApproval.noteId }) }}</span>
              <div class="agent-approval-bar__actions">
                <button class="agent-approval-btn agent-approval-btn--accept" :disabled="approvalBusy" @click="respondExecutionApproval('approve')">接受</button>
                <button class="agent-approval-btn agent-approval-btn--reject" :disabled="approvalBusy" @click="respondExecutionApproval('reject')">拒绝</button>
                <button class="agent-approval-btn" :disabled="approvalBusy" @click="enableAutoAcceptAndApply()">自动接受</button>
              </div>
            </template>
            <template v-else>
              <span class="agent-approval-bar__label">{{ t('agent.pendingReview', { target: pendingApprovals[0].noteTitle || pendingApprovals[0].noteId }) }}</span>
              <div class="agent-approval-bar__actions">
                <button class="agent-approval-btn" @click="showApprovalPreview = !showApprovalPreview">
                  {{ showApprovalPreview ? t('agent.hideChanges') : t('agent.viewChanges') }}
                </button>
                <button class="agent-approval-btn agent-approval-btn--accept" :disabled="approvalBusy" @click="acceptPendingApproval(pendingApprovals[0].id)">接受</button>
                <button class="agent-approval-btn agent-approval-btn--reject" :disabled="approvalBusy" @click="rejectPendingApproval(pendingApprovals[0].id)">拒绝</button>
                <button class="agent-approval-btn" :disabled="approvalBusy" @click="enableAutoAcceptAndApply()">自动接受</button>
              </div>
            </template>
          </div>
        </Transition>

        <div
          v-if="showOpsPanel && ((((isExecutionAwaitingApproval && pendingExecutionApproval) || currentPendingApproval) && showApprovalPreview) || executionRecords.length > 0)"
          class="agent-ops-grid"
        >
          <Transition name="panel-elevate">
            <div v-if="((isExecutionAwaitingApproval && pendingExecutionApproval) || currentPendingApproval) && showApprovalPreview" class="agent-task-card">
              <div class="agent-task-card__title">任务卡</div>
              <div class="agent-task-card__row"><span>目标</span><span>{{ pendingExecutionApproval ? (pendingExecutionApproval.noteTitle || pendingExecutionApproval.noteId) : (currentPendingApproval?.noteTitle || currentPendingApproval?.noteId) }}</span></div>
              <div class="agent-task-card__row"><span>操作</span><span>{{ pendingExecutionApproval ? pendingExecutionApproval.operation : 'update_note' }}</span></div>
              <div class="agent-task-card__row"><span>影响</span><span>{{ pendingExecutionApproval ? (pendingExecutionApproval.scope || pendingExecutionApproval.message || '写操作') : currentApprovalSummary }}</span></div>
            </div>
          </Transition>

          <Transition name="panel-elevate">
            <div v-if="executionRecords.length > 0" class="agent-execution-panel">
            <div class="agent-execution-panel__head">
              <span class="agent-execution-panel__title">{{ t('agent.executionLog') }}</span>
              <button class="agent-approval-btn" @click="executionExpanded = !executionExpanded">
                {{ executionExpanded ? t('common.collapse') : t('common.expand') }}
              </button>
            </div>
            <TransitionGroup v-if="executionExpanded" name="record-item" tag="div" class="agent-execution-list">
              <div
                v-for="record in executionRecords"
                :key="record.id"
                class="agent-execution-item"
                :class="`agent-execution-item--${record.status}`"
              >
                <span class="agent-execution-item__status">{{ record.statusText }}</span>
                <span class="agent-execution-item__title">{{ record.title }}</span>
                <span class="agent-execution-item__time">{{ record.timeLabel }}</span>
              </div>
            </TransitionGroup>
            </div>
          </Transition>
        </div>

        <div v-if="showApprovalPreview && currentPendingApproval" class="agent-approval-preview">
          <div class="agent-approval-preview__summary">{{ currentApprovalSummary }}</div>
          <div class="agent-approval-preview__title-row">
            <div class="agent-approval-preview__title">结构化差异</div>
            <button class="agent-approval-btn" @click="showUnchangedDiff = !showUnchangedDiff">
              {{ showUnchangedDiff ? t('agent.hideUnchanged') : t('agent.showUnchanged') }}
            </button>
          </div>
          <div class="agent-approval-diff">
            <div
              v-for="block in visibleApprovalDiffBlocks"
              :key="block.id"
              class="agent-diff-block"
              :class="`agent-diff-block--${block.kind}`"
            >
              <div class="agent-diff-block__head">
                <span class="agent-diff-block__label">{{ block.label }}</span>
                <span class="agent-diff-block__kind">{{ block.kind }}</span>
              </div>
              <div class="agent-diff-lines">
                <div
                  v-for="(line, idx) in block.lines"
                  :key="`${block.id}-${idx}`"
                  class="agent-diff-line"
                  :class="`agent-diff-line--${line.op}`"
                >
                  <span class="agent-diff-sign">{{ line.op === 'add' ? '+' : line.op === 'del' ? '-' : ' ' }}</span>
                  <span class="agent-diff-text">{{ line.text || ' ' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Compact Input Area -->
        <div class="agent-chat__footer">
          <div class="chat-input-unified-box">
            <textarea
              v-model="inputText"
              @keydown.enter.exact.prevent="sendMessage()"
              @input="autoResizeInput"
              :placeholder="locale === 'en' ? 'Ask, search, or make anything...' : '提问、搜索或执行任务...'"
              :style="{ height: `${composerInputHeight}px` }"
              rows="1"
              ref="inputRef"
            ></textarea>

            <div class="chat-input-bottom">
              <div class="chat-input-bottom__left">
                <div class="input-menu-wrapper">
                  <button 
                    class="menu-trigger-btn" 
                    @click="showInputMenu = !showInputMenu"
                    :class="{ 'active': showInputMenu }"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </button>
                  
                  <Transition name="menu-fade">
                    <div v-if="showInputMenu" class="input-menu-popup shallow-glass">
                      <div class="menu-item" @click="triggerKnowledgeSearch">
                        <span class="menu-icon">@</span>
                        <span class="menu-label">{{ locale === 'en' ? 'Knowledge base' : '笔记知识库' }}</span>
                      </div>
                      <div class="menu-item" @click="toggleNoteSelector">
                        <span class="menu-icon smaller">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"></path>
                            <circle cx="12" cy="12" r="2.6"></circle>
                          </svg>
                        </span>
                        <span class="menu-label">{{ locale === 'en' ? 'Add note context' : '添加笔记上下文' }}</span>
                      </div>
                      <div class="menu-item" @click="toggleOpsPanel">
                        <span class="menu-icon smaller">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="16" rx="2"/>
                            <line x1="8" y1="9" x2="16" y2="9"/>
                            <line x1="8" y1="13" x2="16" y2="13"/>
                          </svg>
                        </span>
                        <span class="menu-label">{{ showOpsPanel ? (locale === 'en' ? 'Hide task records' : '隐藏任务记录') : (locale === 'en' ? 'Show task records' : '显示任务记录') }}</span>
                      </div>
                    </div>
                  </Transition>
                  
                  <Transition name="menu-fade">
                    <div v-if="showNoteSelector" class="note-selector-dropdown shallow-glass" ref="selectorRef">
                      <div class="selector-header">{{ locale === 'en' ? 'Select note' : '选择笔记' }}</div>
                      <div class="selector-list">
                        <div 
                          v-for="note in noteStore.notes" 
                          :key="note.id" 
                          class="selector-item"
                          @click="selectNoteAsContext(note)"
                        >
                          <span class="item-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                              <path d="M6 3h9l4 4v14H6z"></path>
                              <path d="M15 3v4h4"></path>
                              <line x1="9" y1="13" x2="15" y2="13"></line>
                              <line x1="9" y1="17" x2="13" y2="17"></line>
                            </svg>
                          </span>
                          <span class="item-title">{{ note.title || (locale === 'en' ? 'Untitled' : '无标题') }}</span>
                        </div>
                        <div v-if="noteStore.notes.length === 0" class="selector-empty">{{ locale === 'en' ? 'No notes' : '暂无笔记' }}</div>
                      </div>
                    </div>
                  </Transition>
                </div>

                <button class="composer-mode-btn composer-mode-btn--mode" @click="toggleAgentMode">
                  {{ agentMode === 'agent' ? t('agent.modeAgent') : t('agent.modeAsk') }}
                </button>
                <div class="composer-model-wrapper" ref="modelSelectorRef">
                  <button
                    class="composer-model-btn"
                    :disabled="modelSwitching"
                    @click="toggleModelSelector"
                  >
                    <span class="composer-model-btn__label">{{ currentModelLabel }}</span>
                    <span class="composer-model-btn__caret">▾</span>
                  </button>

                  <Transition name="menu-fade">
                    <div v-if="showModelSelector" class="composer-model-menu input-menu-popup shallow-glass">
                      <div class="menu-item menu-item--disabled">
                        <span class="menu-label">{{ locale === 'en' ? 'Choose model' : '选择模型' }}</span>
                      </div>
                      <div
                        v-for="option in modelMenuOptions"
                        :key="option.key"
                        class="menu-item menu-item--model"
                        @click="selectComposerModel(option.providerId, option.modelName)"
                      >
                        <div class="model-option__main">
                          <span class="model-option__name">{{ option.modelName }}</span>
                          <span class="model-option__provider">{{ option.providerName }}</span>
                        </div>
                        <span v-if="isSelectedModel(option.providerId, option.modelName)" class="model-option__check">✓</span>
                      </div>
                      <div class="menu-divider"></div>
                      <div class="menu-item menu-item--model" @click="openModelSettingsFromComposer">
                        <span class="menu-label">{{ t('agent.modelSettings') }}</span>
                      </div>
                    </div>
                  </Transition>
                </div>
              </div>
              <div class="chat-input-bottom__right">
                <button class="composer-review-btn" @click="toggleAutoAcceptEdits">
                  {{ autoAcceptEdits ? t('agent.autoAccept') : t('agent.manualReview') }}
                </button>
                <button
                  v-if="!isTyping"
                  class="send-btn-compact"
                  :disabled="!inputText.trim()"
                  @click="sendMessage()"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="7 10 12 5 17 10"></polyline>
                  </svg>
                </button>
                <button
                  v-else
                  class="stop-btn-compact"
                  @click="stopGeneration"
                >
                  <div class="stop-icon-small"></div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Model Settings Modal -->
    <Teleport to="body">
      <ModelSettings 
        v-if="showModelSettings" 
        :backend-url="BACKEND_URL" 
        @close="() => { console.log('Closing settings'); showModelSettings = false; }"
        @updated="handleModelSettingsUpdated"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, watch, inject, computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useNoteStore } from '@/stores/noteStore'
import { noteRepository, type Note } from '@/database/noteRepository'
import { useI18n } from '@/i18n'
import ModelSettings from './ModelSettings.vue'

// Inject dependencies

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  parts?: MessagePart[]  // Part-Based: for structured rendering
  timestamp: Date
  isError?: boolean
}

// Part-Based Message Types (OpenCode-style)
interface TextPart {
  type: 'text'
  content: string
}

interface ToolPart {
  type: 'tool'
  tool: string
  toolId?: string  // For precise status matching
  status: 'running' | 'pending' | 'completed' | 'error'
  startedAt?: number
  awaitingTextToComplete?: boolean
  title?: string
  output?: string
  inputPreview?: string
}

type MessagePart = TextPart | ToolPart

// Stores
const noteStore = useNoteStore()
const { t, locale } = useI18n()
const setEditorContent = inject<(html: string) => void>('setEditorContent')

// Config
const BACKEND_URL = 'http://127.0.0.1:8765'

// State
const isOpen = ref(false)
const isConnected = ref(false)
const isTyping = ref(false)
const hasUnread = ref(false)
const inputText = ref('')
const messages = ref<ChatMessage[]>([])
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const isMaximized = ref(false)
const isSidebarMode = ref(localStorage.getItem('origin_agent_sidebar_mode') === '1')
const showModelSettings = ref(false)
const streamingMessage = ref<ChatMessage | null>(null)
const currentStatus = ref('')
const abortController = ref<AbortController | null>(null)
const includeActiveNote = ref(true)
const AUTO_ACCEPT_EDITS_KEY = 'origin_agent_auto_accept_edits'
const autoAcceptEdits = ref(localStorage.getItem(AUTO_ACCEPT_EDITS_KEY) !== '0')
type AgentMode = 'ask' | 'agent'
const AGENT_MODE_KEY = 'origin_agent_mode'
const agentMode = ref<AgentMode>(localStorage.getItem(AGENT_MODE_KEY) === 'ask' ? 'ask' : 'agent')
const THINKING_STATUS_TEXT = 'Thinking...'

// --- Auto-scroll control ---
const userScrolledUp = ref(false)
const showScrollToBottom = ref(false)

// --- Context (@) Selection ---
const showNoteSelector = ref(false)
const selectedContextNote = ref<any>(null)
const selectorRef = ref<HTMLElement | null>(null)

interface NoteSnapshot {
  id: string
  title: string
  content: string
  markdownSource: string | null
}

interface PendingApproval {
  id: string
  noteId: string
  noteTitle: string
  before: NoteSnapshot
  after: NoteSnapshot
  beforePreview: string
  afterPreview: string
  createdAt: number
}

interface PendingExecutionApproval {
  approvalId: string
  tool: string
  noteId: string
  noteTitle: string
  operation: string
  scope: string
  args: Record<string, any>
  message: string
  createdAt: number
}

type DiffOp = 'same' | 'add' | 'del'
type DiffBlockKind = 'unchanged' | 'modified' | 'added' | 'removed'

interface DiffLine {
  op: DiffOp
  text: string
}

interface DiffBlockView {
  id: string
  label: string
  kind: DiffBlockKind
  lines: DiffLine[]
}

interface TextBlock {
  id: string
  label: string
  text: string
  key: string
}

interface PersistedUiState {
  version: 1
  messages: Array<{
    role: ChatMessage['role']
    content: string
    parts?: MessagePart[]
    timestamp: string
    isError?: boolean
  }>
  pendingApprovals: PendingApproval[]
  pendingExecutionApproval?: PendingExecutionApproval | null
  showApprovalPreview: boolean
  executionExpanded?: boolean
}

interface ExecutionRecord {
  id: string
  title: string
  status: 'running' | 'pending' | 'completed' | 'error'
  statusText: string
  timeLabel: string
}

interface ModelProviderOption {
  id: string
  name: string
  baseUrl?: string
  modelName?: string
  models?: string[]
  activeModel?: string
  isActive?: boolean
}

interface ModelMenuOption {
  key: string
  providerId: string
  providerName: string
  modelName: string
  isActive: boolean
}

const preUpdateSnapshots = ref<Record<string, NoteSnapshot>>({})
const pendingApprovals = ref<PendingApproval[]>([])
const pendingExecutionApproval = ref<PendingExecutionApproval | null>(null)
const showApprovalPreview = ref(false)
const showUnchangedDiff = ref(false)
const approvalBusy = ref(false)
const executionExpanded = ref(true)
const SESSION_UI_PREFIX = 'origin_agent_session_ui_v1:'
let persistUiTimer: ReturnType<typeof setTimeout> | null = null

// --- Session History ---
interface SessionInfo {
  id: string
  preview: string
  title?: string
  pinned?: boolean
  updated_at?: string
}
const showSessionHistory = ref(false)
const sessionList = ref<SessionInfo[]>([])
const MODEL_PROVIDER_KEY = 'origin_agent_selected_model_provider'
const MODEL_NAME_KEY = 'origin_agent_selected_model_name'
const modelProviders = ref<ModelProviderOption[]>([])
const selectedModelProviderId = ref<string | null>(localStorage.getItem(MODEL_PROVIDER_KEY))
const selectedModelName = ref<string | null>(localStorage.getItem(MODEL_NAME_KEY))
const showModelSelector = ref(false)
const modelSelectorRef = ref<HTMLElement | null>(null)
const modelSwitching = ref(false)

// Session metadata stored locally (pinned status, custom titles)
const sessionMeta = ref<Record<string, { pinned?: boolean; title?: string }>>({})

function getSessionUiKey(sessionId: string): string {
  return `${SESSION_UI_PREFIX}${sessionId}`
}

function persistSessionUiState(sessionId: string = currentSessionId.value): void {
  try {
    const payload: PersistedUiState = {
      version: 1,
      messages: messages.value.map(msg => ({
        role: msg.role,
        content: msg.content,
        parts: msg.parts,
        timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : new Date(msg.timestamp).toISOString(),
        isError: msg.isError
      })),
      pendingApprovals: pendingApprovals.value,
      pendingExecutionApproval: pendingExecutionApproval.value,
      showApprovalPreview: showApprovalPreview.value,
      executionExpanded: executionExpanded.value
    }
    localStorage.setItem(getSessionUiKey(sessionId), JSON.stringify(payload))
  } catch (e) {
    console.warn('[Agent] Failed to persist UI session state:', e)
  }
}

function schedulePersistUiState(): void {
  if (persistUiTimer) clearTimeout(persistUiTimer)
  persistUiTimer = setTimeout(() => {
    persistSessionUiState()
  }, 80)
}

function loadPersistedUiState(sessionId: string): boolean {
  try {
    const raw = localStorage.getItem(getSessionUiKey(sessionId))
    if (!raw) return false
    const parsed = JSON.parse(raw) as PersistedUiState
    if (!parsed || parsed.version !== 1) return false
    messages.value = (parsed.messages || []).map(m => ({
      role: m.role,
      content: m.content || '',
      parts: m.parts || [],
      timestamp: new Date(m.timestamp || Date.now()),
      isError: m.isError
    }))
    pendingApprovals.value = Array.isArray(parsed.pendingApprovals) ? parsed.pendingApprovals : []
    pendingExecutionApproval.value = parsed.pendingExecutionApproval || null
    showApprovalPreview.value = Boolean(parsed.showApprovalPreview)
    executionExpanded.value = parsed.executionExpanded !== false
    return true
  } catch (e) {
    console.warn('[Agent] Failed to load persisted UI session state:', e)
    return false
  }
}

function clearPersistedUiState(sessionId: string): void {
  localStorage.removeItem(getSessionUiKey(sessionId))
}

// Load session metadata from localStorage
function loadSessionMeta() {
  try {
    const stored = localStorage.getItem('agent_session_meta')
    if (stored) sessionMeta.value = JSON.parse(stored)
  } catch { sessionMeta.value = {} }
}

// Save session metadata to localStorage
function saveSessionMeta() {
  localStorage.setItem('agent_session_meta', JSON.stringify(sessionMeta.value))
}

async function toggleSessionHistory() {
  showSessionHistory.value = !showSessionHistory.value
  if (showSessionHistory.value) {
    loadSessionMeta()
    await loadSessionList()
  }
}

async function loadSessionList() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions`)
    if (response.ok) {
      const data = await response.json()
      // Merge with local metadata (pinned, custom title)
      const sessions = (data.sessions || []).map((s: SessionInfo) => {
        const meta = sessionMeta.value[s.id] || {}
        return {
          ...s,
          preview: meta.title || s.preview,
          pinned: meta.pinned || false
        }
      })
      // Sort: pinned first, then by updated_at
      sessions.sort((a: SessionInfo, b: SessionInfo) => {
        if (a.pinned && !b.pinned) return -1
        if (!a.pinned && b.pinned) return 1
        return 0
      })
      sessionList.value = sessions
    }
  } catch (e) {
    console.error('Failed to load sessions:', e)
  }
}

// Toggle pin status
function togglePinSession(sessionId: string) {
  if (!sessionMeta.value[sessionId]) {
    sessionMeta.value[sessionId] = {}
  }
  sessionMeta.value[sessionId].pinned = !sessionMeta.value[sessionId].pinned
  saveSessionMeta()
  // Update list
  const session = sessionList.value.find(s => s.id === sessionId)
  if (session) {
    session.pinned = sessionMeta.value[sessionId].pinned
    // Re-sort
    sessionList.value.sort((a, b) => {
      if (a.pinned && !b.pinned) return -1
      if (!a.pinned && b.pinned) return 1
      return 0
    })
  }
}

// Rename session - inline editing
const editingSessionId = ref<string | null>(null)
const editingTitle = ref('')

function renameSession(sessionId: string) {
  const session = sessionList.value.find(s => s.id === sessionId)
  if (!session) return
  
  editingSessionId.value = sessionId
  editingTitle.value = session.preview
  
  // Focus input after render
  nextTick(() => {
    const input = document.querySelector('.session-rename-input') as HTMLInputElement
    if (input) {
      input.focus()
      input.select()
    }
  })
}

function confirmRename(sessionId: string) {
  if (editingTitle.value.trim()) {
    if (!sessionMeta.value[sessionId]) {
      sessionMeta.value[sessionId] = {}
    }
    sessionMeta.value[sessionId].title = editingTitle.value.trim()
    saveSessionMeta()
    
    const session = sessionList.value.find(s => s.id === sessionId)
    if (session) {
      session.preview = editingTitle.value.trim()
    }
  }
  editingSessionId.value = null
  editingTitle.value = ''
}

function cancelRename() {
  editingSessionId.value = null
  editingTitle.value = ''
}

async function loadSession(sessionId: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions/${sessionId}/messages`)
    if (response.ok) {
      const data = await response.json()
      // Switch to this session
      currentSessionId.value = sessionId
      localStorage.setItem(SESSION_KEY, sessionId)
      // Load messages (prefer persisted UI state with parts/tool traces)
      const restored = loadPersistedUiState(sessionId)
      if (!restored) {
        messages.value = (data.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          timestamp: new Date()
        }))
      }
      showSessionHistory.value = false
      nextTick(() => scrollToBottom())
    }
  } catch (e) {
    console.error('Failed to load session:', e)
  }
}

async function deleteSession(sessionId: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    })
    if (response.ok) {
      clearPersistedUiState(sessionId)
      sessionList.value = sessionList.value.filter(s => s.id !== sessionId)
      // If deleted current session, start new one
      if (sessionId === currentSessionId.value) {
        clearChat()
      }
    }
  } catch (e) {
    console.error('Failed to delete session:', e)
  }
}

// --- New: Input Menu & Knowledge Search ---
const showInputMenu = ref(false)
const showOpsPanel = ref(false)

function toggleNoteSelector() {
  showInputMenu.value = false  // Close menu first
  showNoteSelector.value = !showNoteSelector.value
  if (showNoteSelector.value) {
    noteStore.loadNotes()
  }
}

function triggerKnowledgeSearch() {
  const triggerText = "@笔记知识库"
  if (!inputText.value.includes(triggerText)) {
    inputText.value = triggerText + inputText.value
  }
  showInputMenu.value = false
  nextTick(() => {
    inputRef.value?.focus()
    // Trigger height adjust
    if (inputRef.value) {
      autoResizeInput({ target: inputRef.value } as any)
    }
  })
}

function toggleOpsPanel() {
  showOpsPanel.value = !showOpsPanel.value
  showInputMenu.value = false
}

function selectNoteAsContext(note: any) {
  selectedContextNote.value = note
  showNoteSelector.value = false
}

function clearContextNote() {
  selectedContextNote.value = null
}

function snapshotFromNote(note: Note): NoteSnapshot {
  return {
    id: note.id,
    title: note.title || '',
    content: note.content || '',
    markdownSource: note.markdownSource ?? null
  }
}

function snapshotsDiffer(a: NoteSnapshot, b: NoteSnapshot): boolean {
  return a.title !== b.title || a.content !== b.content || (a.markdownSource ?? '') !== (b.markdownSource ?? '')
}

function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return (div.textContent || div.innerText || '').trim()
}

function snapshotToText(snapshot: NoteSnapshot): string {
  const raw = (snapshot.markdownSource && snapshot.markdownSource.trim())
    ? snapshot.markdownSource
    : stripHtml(snapshot.content)
  return raw.trim()
}

function previewText(input: string, maxLen = 220): string {
  if (!input) return '(empty)'
  return input.length > maxLen ? `${input.slice(0, maxLen)}...` : input
}

function countByRegex(text: string, regex: RegExp): number {
  const matches = text.match(regex)
  return matches ? matches.length : 0
}

function normalizeKey(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s#-]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function makeLabelFromText(text: string, fallback: string): string {
  const firstLine = text.split('\n').find(line => line.trim())?.trim() || ''
  if (!firstLine) return fallback
  return firstLine.length > 40 ? `${firstLine.slice(0, 40)}...` : firstLine
}

function splitIntoBlocks(text: string): TextBlock[] {
  const normalized = text.replace(/\r\n/g, '\n').trim()
  if (!normalized) return []
  const rawBlocks = normalized
    .split(/\n{2,}/)
    .map(block => block.trim())
    .filter(Boolean)
  return rawBlocks.map((block, idx) => {
    const label = makeLabelFromText(block, `Block ${idx + 1}`)
    const key = normalizeKey(label)
    return {
      id: `b-${idx}`,
      label,
      text: block,
      key
    }
  })
}

function buildLcsIndices(left: string[], right: string[]): Array<[number, number]> {
  const m = left.length
  const n = right.length
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i -= 1) {
    for (let j = n - 1; j >= 0; j -= 1) {
      if (left[i] === right[j]) dp[i][j] = dp[i + 1][j + 1] + 1
      else dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }
  const pairs: Array<[number, number]> = []
  let i = 0
  let j = 0
  while (i < m && j < n) {
    if (left[i] === right[j]) {
      pairs.push([i, j])
      i += 1
      j += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i += 1
    } else {
      j += 1
    }
  }
  return pairs
}

function buildLineDiff(beforeText: string, afterText: string): DiffLine[] {
  const before = beforeText.split('\n')
  const after = afterText.split('\n')
  const pairs = buildLcsIndices(before, after)
  const lines: DiffLine[] = []
  let i = 0
  let j = 0
  for (const [pi, pj] of pairs) {
    while (i < pi) {
      lines.push({ op: 'del', text: before[i] })
      i += 1
    }
    while (j < pj) {
      lines.push({ op: 'add', text: after[j] })
      j += 1
    }
    lines.push({ op: 'same', text: before[pi] })
    i = pi + 1
    j = pj + 1
  }
  while (i < before.length) {
    lines.push({ op: 'del', text: before[i] })
    i += 1
  }
  while (j < after.length) {
    lines.push({ op: 'add', text: after[j] })
    j += 1
  }
  return lines
}

function pairSegments(beforeSeg: TextBlock[], afterSeg: TextBlock[]): DiffBlockView[] {
  const out: DiffBlockView[] = []
  let i = 0
  let j = 0
  while (i < beforeSeg.length && j < afterSeg.length) {
    const b = beforeSeg[i]
    const a = afterSeg[j]
    out.push({
      id: `${b.id}:${a.id}`,
      label: a.label || b.label,
      kind: 'modified',
      lines: buildLineDiff(b.text, a.text)
    })
    i += 1
    j += 1
  }
  while (i < beforeSeg.length) {
    const b = beforeSeg[i]
    out.push({
      id: `${b.id}:removed`,
      label: b.label,
      kind: 'removed',
      lines: b.text.split('\n').map(line => ({ op: 'del' as const, text: line }))
    })
    i += 1
  }
  while (j < afterSeg.length) {
    const a = afterSeg[j]
    out.push({
      id: `added:${a.id}`,
      label: a.label,
      kind: 'added',
      lines: a.text.split('\n').map(line => ({ op: 'add' as const, text: line }))
    })
    j += 1
  }
  return out
}

function buildStructuredDiff(beforeText: string, afterText: string): DiffBlockView[] {
  const beforeBlocks = splitIntoBlocks(beforeText)
  const afterBlocks = splitIntoBlocks(afterText)
  const pairs = buildLcsIndices(beforeBlocks.map(b => b.key), afterBlocks.map(b => b.key))
  const out: DiffBlockView[] = []
  let bi = 0
  let ai = 0
  for (const [pb, pa] of pairs) {
    if (bi < pb || ai < pa) {
      out.push(...pairSegments(beforeBlocks.slice(bi, pb), afterBlocks.slice(ai, pa)))
    }
    const b = beforeBlocks[pb]
    const a = afterBlocks[pa]
    if (b.text === a.text) {
      out.push({
        id: `${b.id}:${a.id}`,
        label: a.label || b.label,
        kind: 'unchanged',
        lines: [{ op: 'same', text: previewText(a.text, 280) }]
      })
    } else {
      out.push({
        id: `${b.id}:${a.id}`,
        label: a.label || b.label,
        kind: 'modified',
        lines: buildLineDiff(b.text, a.text)
      })
    }
    bi = pb + 1
    ai = pa + 1
  }
  if (bi < beforeBlocks.length || ai < afterBlocks.length) {
    out.push(...pairSegments(beforeBlocks.slice(bi), afterBlocks.slice(ai)))
  }
  return out
}

function summarizeChange(before: NoteSnapshot, after: NoteSnapshot): string {
  const beforeText = snapshotToText(before)
  const afterText = snapshotToText(after)
  const beforeHeadings = countByRegex(beforeText, /^#{1,6}\s/mg)
  const afterHeadings = countByRegex(afterText, /^#{1,6}\s/mg)
  const beforeLists = countByRegex(beforeText, /^\s*([-*+]|\d+\.)\s/mg)
  const afterLists = countByRegex(afterText, /^\s*([-*+]|\d+\.)\s/mg)
  const deltaChars = afterText.length - beforeText.length
  return `chars ${beforeText.length} -> ${afterText.length} (${deltaChars >= 0 ? '+' : ''}${deltaChars}), headings ${beforeHeadings} -> ${afterHeadings}, lists ${beforeLists} -> ${afterLists}`
}

async function capturePreUpdateSnapshot(noteId: string | null | undefined): Promise<void> {
  if (!noteId || preUpdateSnapshots.value[noteId]) return
  const note = await noteRepository.getById(noteId)
  if (!note) return
  preUpdateSnapshots.value[noteId] = snapshotFromNote(note)
}

function extractNoteIdFromToolInputPreview(inputPreview?: string): string | null {
  if (!inputPreview) return null
  const uuidMatch = inputPreview.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i)
  if (uuidMatch) return uuidMatch[0]
  const genericIdMatch = inputPreview.match(/(?:note[_-]?id|id)\s*[:=]\s*['"]?([a-zA-Z0-9-]{8,})/i)
  return genericIdMatch?.[1] || null
}

function findToolPartForCompletion(toolId?: string, toolName?: string): ToolPart | null {
  for (let i = messages.value.length - 1; i >= 0; i -= 1) {
    const msg = messages.value[i]
    if (!msg.parts) continue
    for (let j = msg.parts.length - 1; j >= 0; j -= 1) {
      const part = msg.parts[j]
      if (part.type !== 'tool') continue
      const toolPart = part as ToolPart
      if (toolId && toolPart.toolId === toolId) {
        return toolPart
      }
      if (!toolId && toolName && toolPart.tool === toolName && (toolPart.status === 'running' || toolPart.status === 'pending')) {
        return toolPart
      }
    }
  }
  return null
}

function markToolPartCompleted(toolPart: ToolPart, toolName?: string): void {
  if (toolName === 'read_note_content') {
    toolPart.awaitingTextToComplete = true
    return
  }
  // Keep a tiny minimum running window so status doesn't instantly flip.
  const minimumRunningMs = 180
  const startedAt = toolPart.startedAt ?? Date.now()
  const elapsed = Date.now() - startedAt
  const delay = Math.max(0, minimumRunningMs - elapsed)

  const applyComplete = () => {
    if (toolPart.status === 'running') {
      toolPart.status = 'completed'
      messages.value = [...messages.value]
    }
  }

  if (delay === 0) {
    applyComplete()
    return
  }

  setTimeout(applyComplete, delay)
}

function finalizeAwaitingReadTools(): void {
  let changed = false
  for (const message of messages.value) {
    if (!message.parts) continue
    for (const part of message.parts) {
      if (part.type !== 'tool') continue
      const toolPart = part as ToolPart
      if (toolPart.status === 'running' && toolPart.awaitingTextToComplete) {
        toolPart.awaitingTextToComplete = false
        toolPart.status = 'completed'
        changed = true
      }
    }
  }
  if (changed) {
    messages.value = [...messages.value]
  }
}

function markToolPartPendingByApproval(approval: PendingExecutionApproval): void {
  const toolPart = findToolPartForCompletion(approval.approvalId, approval.tool)
  if (!toolPart) return
  if (toolPart.status === 'running') {
    toolPart.status = 'pending'
    messages.value = [...messages.value]
  }
}

function markToolPartRunningByApproval(approval: PendingExecutionApproval): void {
  const toolPart = findToolPartForCompletion(approval.approvalId, approval.tool)
  if (!toolPart) return
  if (toolPart.status === 'pending') {
    toolPart.status = 'running'
    messages.value = [...messages.value]
  }
}

async function refreshUpdatedNoteRealtime(noteId: string | null, previousContent?: string): Promise<void> {
  const targetId = noteId || noteStore.currentNote?.id || null
  if (!targetId) return
  let latest: Note | null = null
  for (let i = 0; i < 12; i += 1) {
    await noteStore.loadNotes()
    latest = (await noteRepository.getById(targetId)) ?? null
    if (!latest) break
    if (!previousContent || latest.content !== previousContent || i === 5) {
      break
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  if (!latest) return
  if (noteStore.currentNote?.id === targetId) {
    noteStore.currentNote = { ...latest }
    if (setEditorContent) {
      setEditorContent(latest.content)
    }
  }
}

function patchStoreWithSnapshot(snapshot: NoteSnapshot): void {
  if (noteStore.currentNote?.id === snapshot.id) {
    noteStore.currentNote = {
      ...noteStore.currentNote,
      title: snapshot.title,
      content: snapshot.content,
      markdownSource: snapshot.markdownSource
    } as any
    if (setEditorContent) {
      setEditorContent(snapshot.content)
    }
  }
  const idx = noteStore.notes.findIndex((n: any) => n.id === snapshot.id)
  if (idx >= 0) {
    noteStore.notes[idx] = {
      ...noteStore.notes[idx],
      title: snapshot.title,
      content: snapshot.content,
      markdownSource: snapshot.markdownSource
    } as any
  }
}

function persistSnapshotAsync(snapshot: NoteSnapshot): Promise<void> {
  return noteRepository.update(snapshot.id, {
    title: snapshot.title,
    content: snapshot.content,
    markdownSource: snapshot.markdownSource
  })
}

function applySnapshot(snapshot: NoteSnapshot): void {
  patchStoreWithSnapshot(snapshot)
  persistSnapshotAsync(snapshot).catch((err) => {
    console.warn('[Agent] Failed to persist approval snapshot:', err)
  })
}

function addPendingApproval(approval: PendingApproval): void {
  pendingApprovals.value = pendingApprovals.value.filter(item => item.noteId !== approval.noteId)
  pendingApprovals.value.unshift(approval)
  showApprovalPreview.value = true
}

function normalizeExecutionApproval(raw: any): PendingExecutionApproval | null {
  if (!raw || typeof raw !== 'object') return null
  const approvalId = String(raw.approval_id || raw.id || '').trim()
  if (!approvalId) return null
  const noteId = String(raw.note_id || noteStore.currentNote?.id || '').trim()
  const noteTitle = String(raw.note_title || noteStore.currentNote?.title || noteId || 'Current note').trim()
  return {
    approvalId,
    tool: String(raw.tool || raw.operation || 'write_tool'),
    noteId,
    noteTitle,
    operation: String(raw.operation || raw.tool || 'write_tool'),
    scope: String(raw.scope || ''),
    args: raw.args && typeof raw.args === 'object' ? raw.args : {},
    message: String(raw.message || ''),
    createdAt: Date.now()
  }
}

async function respondExecutionApproval(action: 'approve' | 'reject'): Promise<void> {
  if (approvalBusy.value || !pendingExecutionApproval.value) return
  const approval = pendingExecutionApproval.value
  const beforeContent = noteStore.currentNote?.id === approval.noteId
    ? (noteStore.currentNote?.content || '')
    : undefined
  approvalBusy.value = true
  if (action === 'approve') {
    markToolPartRunningByApproval(approval)
    currentStatus.value = t('agent.running')
  } else {
    currentStatus.value = t('agent.rejected')
  }
  try {
    await sendMessage('', {
      suppressUserEcho: true,
      resume: {
        action,
        approval_id: approval.approvalId
      }
    })
    if (action === 'approve') {
      await refreshUpdatedNoteRealtime(approval.noteId || null, beforeContent)
    }
    pendingExecutionApproval.value = null
    showApprovalPreview.value = false
  } catch (err) {
    // Keep approval in-place on failure so user can retry without visual jump.
    throw err
  } finally {
    approvalBusy.value = false
  }
}

async function acceptPendingApproval(approvalId: string): Promise<void> {
  if (approvalBusy.value) return
  const approval = pendingApprovals.value.find(item => item.id === approvalId)
  if (!approval) return
  approvalBusy.value = true
  try {
    applySnapshot(approval.after)
    pendingApprovals.value = pendingApprovals.value.filter(item => item.id !== approvalId)
  } finally {
    approvalBusy.value = false
  }
}

async function rejectPendingApproval(approvalId: string): Promise<void> {
  if (approvalBusy.value) return
  const approval = pendingApprovals.value.find(item => item.id === approvalId)
  if (!approval) return
  approvalBusy.value = true
  try {
    applySnapshot(approval.before)
    pendingApprovals.value = pendingApprovals.value.filter(item => item.id !== approvalId)
  } finally {
    approvalBusy.value = false
  }
}

function toggleAutoAcceptEdits(): void {
  autoAcceptEdits.value = !autoAcceptEdits.value
}

function toggleAgentMode(): void {
  agentMode.value = agentMode.value === 'agent' ? 'ask' : 'agent'
}

async function enableAutoAcceptAndApply(): Promise<void> {
  autoAcceptEdits.value = true
  if (pendingExecutionApproval.value) {
    await respondExecutionApproval('approve')
    return
  }
  if (pendingApprovals.value.length === 0) return
  await acceptPendingApproval(pendingApprovals.value[0].id)
}

const currentPendingApproval = computed(() => pendingApprovals.value[0] || null)
const isExecutionAwaitingApproval = computed(
  () => Boolean(pendingExecutionApproval.value) && !approvalBusy.value
)
const hasReviewData = computed(() => Boolean(pendingExecutionApproval.value || currentPendingApproval.value))
const currentApprovalSummary = computed(() => {
  if (!currentPendingApproval.value) return ''
  return summarizeChange(currentPendingApproval.value.before, currentPendingApproval.value.after)
})
const approvalDiffBlocks = computed(() => {
  if (!currentPendingApproval.value) return []
  const beforeText = snapshotToText(currentPendingApproval.value.before)
  const afterText = snapshotToText(currentPendingApproval.value.after)
  return buildStructuredDiff(beforeText, afterText)
})
const visibleApprovalDiffBlocks = computed(() => {
  if (showUnchangedDiff.value) return approvalDiffBlocks.value
  return approvalDiffBlocks.value.filter(block => block.kind !== 'unchanged')
})

function handleReviewPillClick(): void {
  if (!hasReviewData.value) return
  showApprovalPreview.value = !showApprovalPreview.value
}

function formatExecutionTime(input: Date | string): string {
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return '--:--:--'
  return d.toLocaleTimeString([], { hour12: false })
}

const executionRecords = computed<ExecutionRecord[]>(() => {
  const records: ExecutionRecord[] = []
  messages.value.forEach((msg, msgIndex) => {
    if (!msg.parts || msg.parts.length === 0) return
    const timeLabel = formatExecutionTime(msg.timestamp)
    msg.parts.forEach((part, partIndex) => {
      if (part.type !== 'tool') return
      const toolPart = part as ToolPart
      const statusText =
        toolPart.status === 'running'
          ? t('agent.running')
          : toolPart.status === 'pending'
            ? t('agent.pendingConfirm')
            : toolPart.status === 'completed'
            ? t('agent.completed')
            : t('agent.failed')
      if (toolPart.status === 'pending') return
      records.push({
        id: `${msgIndex}-${partIndex}-${toolPart.toolId || toolPart.tool}`,
        title: toolPart.title || toolPart.tool,
        status: toolPart.status,
        statusText,
        timeLabel
      })
    })
  })
  return records.reverse().slice(0, 20)
})

const displayStatusText = computed(() => {
  if (approvalBusy.value && !pendingExecutionApproval.value) {
    return ''
  }
  if (pendingExecutionApproval.value) {
    // Approval state is already displayed in the approval bar.
    // Avoid duplicated standalone status bubble.
    return ''
  }
  if (currentStatus.value === t('agent.running')) {
    return ''
  }
  return currentStatus.value
})

const showStatusDots = computed(() => {
  if (pendingExecutionApproval.value || approvalBusy.value) return false
  return Boolean(displayStatusText.value)
})

function normalizeStatusText(statusText: string): string {
  const trimmed = String(statusText || '').trim()
  if (!trimmed) return ''
  const lowered = trimmed.toLowerCase()
  if (lowered.includes('thinking') || trimmed.includes('思考')) {
    return THINKING_STATUS_TEXT
  }
  return trimmed
}

const COMPOSER_TEXTAREA_MIN_HEIGHT = 28
const COMPOSER_TEXTAREA_MAX_HEIGHT = 220
const composerInputHeight = ref(COMPOSER_TEXTAREA_MIN_HEIGHT)

function resizeComposerInput(el?: HTMLTextAreaElement | null) {
  if (!el) return
  el.style.height = '0px'
  const computed = window.getComputedStyle(el)
  const lineHeight = Number.parseFloat(computed.lineHeight) || 16
  const minHeight = Number.parseFloat(computed.minHeight) || Math.max(COMPOSER_TEXTAREA_MIN_HEIGHT, lineHeight + 2)
  const nextHeight = Math.min(
    COMPOSER_TEXTAREA_MAX_HEIGHT,
    Math.max(minHeight, el.scrollHeight)
  )
  composerInputHeight.value = nextHeight
  el.style.height = `${nextHeight}px`
  el.style.overflowY = el.scrollHeight > COMPOSER_TEXTAREA_MAX_HEIGHT ? 'auto' : 'hidden'
}

// Auto-resize input
function autoResizeInput(e: Event) {
  resizeComposerInput(e.target as HTMLTextAreaElement)
}

// Reset textarea height when chat window opens
watch(isOpen, (newVal) => {
  if (newVal) {
    nextTick(() => {
      resizeComposerInput(inputRef.value)
    })
  }
})

const modelMenuOptions = computed<ModelMenuOption[]>(() => {
  const options: ModelMenuOption[] = []
  for (const provider of modelProviders.value) {
    const models = Array.isArray(provider.models) && provider.models.length
      ? provider.models
      : (provider.modelName ? [provider.modelName] : [])
    const activeModel = provider.activeModel || provider.modelName || models[0]
    for (const model of models) {
      options.push({
        key: `${provider.id}:${model}`,
        providerId: provider.id,
        providerName: provider.name,
        modelName: model,
        isActive: !!provider.isActive && model === activeModel
      })
    }
  }
  return options
})

const currentModelProvider = computed<ModelMenuOption | null>(() => {
  if (!modelMenuOptions.value.length) return null
  if (selectedModelProviderId.value && selectedModelName.value) {
    const selected = modelMenuOptions.value.find(
      (option) =>
        option.providerId === selectedModelProviderId.value &&
        option.modelName === selectedModelName.value
    )
    if (selected) return selected
  }
  return modelMenuOptions.value.find(option => option.isActive) || modelMenuOptions.value[0] || null
})

const currentModelLabel = computed(() => {
  const current = currentModelProvider.value
  if (!current) return locale.value === 'en-US' ? 'No model' : '无模型'
  return current.modelName
})

async function loadComposerModelProviders(): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/models/providers`)
    if (!response.ok) return
    const providers = await response.json()
    const list = Array.isArray(providers) ? providers : []
    modelProviders.value = list

    if (!list.length) {
      selectedModelProviderId.value = null
      selectedModelName.value = null
      localStorage.removeItem(MODEL_PROVIDER_KEY)
      localStorage.removeItem(MODEL_NAME_KEY)
      return
    }

    const options = modelMenuOptions.value
    const storedProviderId = selectedModelProviderId.value
    const storedModelName = selectedModelName.value
    const hasStored = Boolean(
      storedProviderId &&
      storedModelName &&
      options.some(
        (option) =>
          option.providerId === storedProviderId &&
          option.modelName === storedModelName
      )
    )
    const fallback = options.find(option => option.isActive) || options[0]
    selectedModelProviderId.value = hasStored ? storedProviderId! : (fallback?.providerId || null)
    selectedModelName.value = hasStored ? storedModelName! : (fallback?.modelName || null)

    if (selectedModelProviderId.value) localStorage.setItem(MODEL_PROVIDER_KEY, selectedModelProviderId.value)
    else localStorage.removeItem(MODEL_PROVIDER_KEY)
    if (selectedModelName.value) localStorage.setItem(MODEL_NAME_KEY, selectedModelName.value)
    else localStorage.removeItem(MODEL_NAME_KEY)
  } catch (err) {
    console.warn('[Agent] Failed to load model providers:', err)
  }
}

function toggleModelSelector(): void {
  showModelSelector.value = !showModelSelector.value
  if (showModelSelector.value) {
    showInputMenu.value = false
    showNoteSelector.value = false
  }
}

function isSelectedModel(providerId: string, modelName: string): boolean {
  return providerId === selectedModelProviderId.value && modelName === selectedModelName.value
}

async function selectComposerModel(providerId: string, modelName: string): Promise<void> {
  if (!providerId || !modelName || modelSwitching.value) return
  if (isSelectedModel(providerId, modelName)) {
    showModelSelector.value = false
    return
  }

  modelSwitching.value = true
  try {
    const activeProvider = modelProviders.value.find(p => p.isActive)
    if (activeProvider?.id !== providerId) {
      const providerRes = await fetch(`${BACKEND_URL}/api/models/providers/${providerId}/active`, {
        method: 'POST'
      })
      if (!providerRes.ok) {
        throw new Error(`Switch provider failed: ${providerRes.status}`)
      }
    }

    const modelRes = await fetch(`${BACKEND_URL}/api/models/providers/${providerId}/models/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelName })
    })
    if (!modelRes.ok) {
      throw new Error(`Switch model failed: ${modelRes.status}`)
    }

    selectedModelProviderId.value = providerId
    selectedModelName.value = modelName
    localStorage.setItem(MODEL_PROVIDER_KEY, providerId)
    localStorage.setItem(MODEL_NAME_KEY, modelName)
    showModelSelector.value = false
    await loadComposerModelProviders()
    await checkConnection()
  } catch (err) {
    console.error('[Agent] Failed to switch model provider:', err)
  } finally {
    modelSwitching.value = false
  }
}

function openModelSettingsFromComposer(): void {
  showModelSelector.value = false
  showModelSettings.value = true
}

async function handleModelSettingsUpdated(): Promise<void> {
  await checkConnection()
  await loadComposerModelProviders()
}

// Close menus when clicking outside
function handleGlobalClick(e: MouseEvent) {
  const menuWrapper = document.querySelector('.input-menu-wrapper')
  if (menuWrapper && !menuWrapper.contains(e.target as Node)) {
    showInputMenu.value = false
    showNoteSelector.value = false
  }
  if (modelSelectorRef.value && !modelSelectorRef.value.contains(e.target as Node)) {
    showModelSelector.value = false
  }
}

// --- Draggable Logic ---
const position = ref({ x: window.innerWidth - 40, y: window.innerHeight - 100 })
const isDragging = ref(false)
const isDocked = ref(true)
const windowWidth = ref(window.innerWidth)
const dragStartPointer = ref({ x: 0, y: 0 })
const dragStartPosition = ref({ x: 0, y: 0 })
const chatWindowRef = ref<HTMLElement | null>(null)

const containerStyle = computed(() => {
  if (isSidebarMode.value && isOpen.value) {
    return {
      right: '16px',
      top: '16px',
      left: 'auto',
      transition: 'all 0.2s ease'
    }
  }
  return {
    left: `${position.value.x}px`,
    top: `${position.value.y}px`,
    transition: isDragging.value ? 'none' : 'all 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28)'
  }
})

function startDrag(e: MouseEvent) {
  if (isMaximized.value || isSidebarMode.value) return
  e.preventDefault()
  isDragging.value = true
  isDocked.value = false
  dragStartPointer.value = { x: e.clientX, y: e.clientY }
  dragStartPosition.value = { x: position.value.x, y: position.value.y }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  position.value = {
    x: dragStartPosition.value.x + (e.clientX - dragStartPointer.value.x),
    y: dragStartPosition.value.y + (e.clientY - dragStartPointer.value.y)
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  if (isOpen.value) {
    constrainOpenChatPosition()
    isDocked.value = false
  } else {
    snapToEdge()
  }
}

function snapToEdge() {
  const BUBBLE_SIZE = 50
  const screenW = window.innerWidth
  const screenH = window.innerHeight
  
  // Keep vertical within bounds
  if (position.value.y < 0) position.value.y = 10
  if (position.value.y > screenH - BUBBLE_SIZE) position.value.y = screenH - BUBBLE_SIZE - 10
  
  // Snap horizontal to nearest edge
  if (position.value.x > screenW / 2) {
    // Right Edge - Dock half way
    position.value.x = screenW - (BUBBLE_SIZE / 2)
  } else {
    // Left Edge - Dock half way
    position.value.x = -(BUBBLE_SIZE / 2)
  }
  isDocked.value = true
}

// Click handler (distinguish drag from click)
function handleClick() {
  if (!isDragging.value) {
    // If docked, pop out a bit
    if (isDocked.value && !isOpen.value) {
      const BUBBLE_SIZE = 50
      if (position.value.x < 0) position.value.x = 20
      else position.value.x = window.innerWidth - BUBBLE_SIZE - 20
      isDocked.value = false
    }
    toggleChat()
    
    // If closing, dock back? Maybe let user dock manually or auto dock after delay.
    // For now, let's auto-dock if closed
    if (!isOpen.value) {
       setTimeout(() => {
         if (!isOpen.value && !isDragging.value) snapToEdge()
       }, 500)
    }
  }
}

function constrainOpenChatPosition() {
  const EDGE_MARGIN = 12
  const chatWidth = chatWindowRef.value?.offsetWidth || 380
  const minRightEdge = Math.min(chatWidth + EDGE_MARGIN, window.innerWidth - EDGE_MARGIN)
  const maxRightEdge = window.innerWidth - EDGE_MARGIN

  if (position.value.x < minRightEdge) position.value.x = minRightEdge
  if (position.value.x > maxRightEdge) position.value.x = maxRightEdge
}

// Initial Position setup
// Handle window resize - keep bubble within visible bounds
const handleResize = () => {
  const oldWidth = windowWidth.value
  const newWidth = window.innerWidth
  const oldHeight = window.innerHeight // approximate
  
  // Update stored width
  windowWidth.value = newWidth
  
  const BUBBLE_SIZE = 50
  const screenH = window.innerHeight
  
  // Calculate distance from right edge BEFORE update
  const distanceFromRight = oldWidth - position.value.x
  
  // sticky horizontal: favor the side it was closer to
  if (position.value.x > oldWidth / 2) {
    // Right side: Keep same distance from right edge
    position.value.x = newWidth - distanceFromRight
  } else {
    // Left side: Keep same distance from left edge (position.x stays same)
    // But verify it doesn't stay off-screen if it was docked
    // Actually, if it was -25, it stays -25. That's fine.
  }

  // Safety clamps (in case of extreme resize or rounding)
  // 1. Right bound
  if (position.value.x > newWidth - BUBBLE_SIZE / 2) {
     position.value.x = newWidth - BUBBLE_SIZE / 2
  }
  // 2. Left bound
  if (position.value.x < -BUBBLE_SIZE / 2) {
     position.value.x = -BUBBLE_SIZE / 2
  }
  
  // Constrain Y position
  if (position.value.y > screenH - BUBBLE_SIZE) {
    position.value.y = screenH - BUBBLE_SIZE - 10
  }
  if (position.value.y < 0) {
    position.value.y = 10
  }
}

let connectionHeartbeatTimer: ReturnType<typeof setInterval> | null = null

// Initial Position setup
onMounted(() => {
  checkConnection(true) // Start checks with "isStartup = true"
  void loadComposerModelProviders()
  if (connectionHeartbeatTimer) {
    clearInterval(connectionHeartbeatTimer)
  }
  connectionHeartbeatTimer = setInterval(() => checkConnection(false), 30000) // Regular heartbeat
  
  window.addEventListener('resize', handleResize)
  window.addEventListener('origin-agent-sidebar-mode-changed', syncSidebarModeFromExternal as EventListener)
  window.addEventListener('storage', syncSidebarModeFromExternal)
  // Use capture phase so inside-panel @mousedown.stop won't block outside-click detection.
  document.addEventListener('mousedown', handleGlobalClick, true)
  if (isSidebarMode.value) {
    isOpen.value = true
    hasUnread.value = false
  }
  window.dispatchEvent(new CustomEvent('origin-agent-sidebar-mode-changed', { detail: { enabled: isSidebarMode.value } }))
  setTimeout(snapToEdge, 100) // Initial dock
})

onUnmounted(() => {
  if (connectionHeartbeatTimer) {
    clearInterval(connectionHeartbeatTimer)
    connectionHeartbeatTimer = null
  }
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('origin-agent-sidebar-mode-changed', syncSidebarModeFromExternal as EventListener)
  window.removeEventListener('storage', syncSidebarModeFromExternal)
  document.removeEventListener('mousedown', handleGlobalClick, true)
})
// ----------------------

function formatToolOutput(output: string): string {
  const compact = String(output || '')
    .replace(/\s+/g, ' ')
    .trim()
  if (!compact) return ''
  if (compact.length <= 62) return compact
  return `${compact.slice(0, 59)}...`
}

function toggleChat() {
  isOpen.value = !isOpen.value
  hasUnread.value = false
  
  if (isOpen.value) {
    nextTick(() => {
      inputRef.value?.focus()
      checkConnection()
    })
  }
}

function reanchorFloatingBubble(): void {
  const BUBBLE_SIZE = 50
  const EDGE_MARGIN = 20
  const TOP_MIN = 60

  position.value.x = Math.max(
    EDGE_MARGIN,
    Math.min(window.innerWidth - BUBBLE_SIZE - EDGE_MARGIN, position.value.x)
  )
  position.value.y = Math.max(
    TOP_MIN,
    Math.min(window.innerHeight - BUBBLE_SIZE - EDGE_MARGIN, position.value.y)
  )

  // Exiting sidebar mode should start as fully visible floating bubble.
  isDocked.value = false
}

function toggleSidebarMode() {
  isSidebarMode.value = !isSidebarMode.value
  localStorage.setItem('origin_agent_sidebar_mode', isSidebarMode.value ? '1' : '0')
  window.dispatchEvent(new CustomEvent('origin-agent-sidebar-mode-changed', { detail: { enabled: isSidebarMode.value } }))
  if (isSidebarMode.value) {
    isMaximized.value = false
    isOpen.value = true
    hasUnread.value = false
  } else {
    // Exiting right sidebar should collapse directly back to the floating bubble.
    isOpen.value = false
    reanchorFloatingBubble()
    snapToEdge()
  }
}

function syncSidebarModeFromExternal(event?: Event): void {
  let enabled = localStorage.getItem('origin_agent_sidebar_mode') === '1'
  if (event && 'detail' in event) {
    const detail = (event as CustomEvent<{ enabled?: boolean }>).detail
    if (typeof detail?.enabled === 'boolean') enabled = detail.enabled
  }

  const wasSidebarMode = isSidebarMode.value
  if (wasSidebarMode === enabled) return

  isSidebarMode.value = enabled
  if (enabled) {
    isMaximized.value = false
    isOpen.value = true
    hasUnread.value = false
  } else if (wasSidebarMode) {
    // Keep behavior consistent with manual toggle: leave sidebar mode -> bubble.
    isOpen.value = false
    reanchorFloatingBubble()
    snapToEdge()
  }
}

function toggleMaximizeMode() {
  if (isSidebarMode.value) {
    isSidebarMode.value = false
    localStorage.setItem('origin_agent_sidebar_mode', '0')
    window.dispatchEvent(new CustomEvent('origin-agent-sidebar-mode-changed', { detail: { enabled: false } }))
    reanchorFloatingBubble()
  }
  isMaximized.value = !isMaximized.value
}

function clearChat() {
  persistSessionUiState()

  // Rotate to new session first so old session UI snapshot is preserved
  console.log('[Agent] User cleared chat. Rotating Session ID.')
  currentSessionId.value = crypto.randomUUID()
  localStorage.setItem('origin_agent_session_id', currentSessionId.value)

  messages.value = []
  pendingApprovals.value = []
  pendingExecutionApproval.value = null
  preUpdateSnapshots.value = {}
  showApprovalPreview.value = false
  showUnchangedDiff.value = false
  executionExpanded.value = true
  isTyping.value = false
  currentStatus.value = ''
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }

  persistSessionUiState()
  inputRef.value?.focus()
}

const retryCount = ref(0)
const maxRetries = 30 // Wait up to 30s for startup
let healthCheckInFlight: Promise<boolean> | null = null

async function runHealthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/health`)
    return response.ok
  } catch {
    return false
  }
}

async function checkConnection(isStartup = false) {
  if (!healthCheckInFlight) {
    healthCheckInFlight = runHealthCheck().finally(() => {
      healthCheckInFlight = null
    })
  }
  isConnected.value = await healthCheckInFlight

  if (isConnected.value) {
    retryCount.value = 0 // Reset on success
  }

  // Startup Intelligence: If starting up and failed, retry quickly
  if (isStartup && !isConnected.value && retryCount.value < maxRetries) {
    retryCount.value++
    setTimeout(() => checkConnection(true), 1000)
  }
}


// Fix: Reactive Session to prevent Context Locking
const SESSION_KEY = 'origin_agent_session_id'
// Initialize session ID (create if missing)
if (!localStorage.getItem(SESSION_KEY)) {
    localStorage.setItem(SESSION_KEY, crypto.randomUUID())
}
const currentSessionId = ref(localStorage.getItem(SESSION_KEY)!)

// Restore visual UI state for current session on startup
loadPersistedUiState(currentSessionId.value)

// Keep conversation session when switching notes/pages.
// We only persist current UI state, but do NOT rotate session or clear messages.
watch(() => noteStore.currentNote?.id, (newId, oldId) => {
    if (newId !== oldId) {
        persistSessionUiState()
        console.log(`[Agent] Note switched (${oldId} -> ${newId}). Keeping current session.`)
    }
})

async function sendMessage(
  text?: string,
  options?: {
    suppressUserEcho?: boolean
    resume?: Record<string, any> | null
  }
) {
  let streamInterruptedForApproval = false
  let touchedNoteId: string | null = null
  const isResume = Boolean(options?.resume)
  const messageText = (text ?? inputText.value.trim()).trim()
  if (isTyping.value && !isResume) return
  if (!isResume && !messageText) return
  if (!isResume && pendingExecutionApproval.value) {
    messages.value.push({
      role: 'assistant',
      content: '检测到待审批任务，请先点击 Accept 或 Reject 后再继续。',
      timestamp: new Date()
    })
    return
  }

  if (!autoAcceptEdits.value && !isResume) {
    const activeNoteId = includeActiveNote.value ? noteStore.currentNote?.id : null
    if (activeNoteId) {
      await capturePreUpdateSnapshot(activeNoteId)
    }
    if (selectedContextNote.value?.id) {
      await capturePreUpdateSnapshot(selectedContextNote.value.id)
    }
  }
  
  // Optimistic UI update
  if (!options?.suppressUserEcho) {
    messages.value.push({ role: 'user', content: messageText, timestamp: new Date() })
  }
  // Clear state
  if (!options?.suppressUserEcho) {
    inputText.value = ''
  }
  isTyping.value = true
  showInputMenu.value = false
  showNoteSelector.value = false
  showModelSelector.value = false
  
  // Reset scroll state - user sending message means they want to see the response
  userScrolledUp.value = false
  showScrollToBottom.value = false
  
  // Reset to single-line baseline after sending
  nextTick(() => {
    if (inputRef.value) {
      composerInputHeight.value = COMPOSER_TEXTAREA_MIN_HEIGHT
      inputRef.value.style.height = `${COMPOSER_TEXTAREA_MIN_HEIGHT}px`
      inputRef.value.style.overflowY = 'hidden'
    }
  })
  
  currentStatus.value = isResume ? t('agent.running') : THINKING_STATUS_TEXT
  
  // Ensure keyboard on mobile doesn't hide input
  nextTick(() => {
    scrollToBottom(true)
  })

  // Check connection before sending (Deep Check)
  if (!isConnected.value) {
     // Try one last ping
     try {
       const res = await fetch(`${BACKEND_URL}/health`)
       if (res.ok) isConnected.value = true
     } catch {}
     
     if (!isConnected.value) {
        messages.value.push({ 
            role: 'assistant', 
            content: '无法连接到 AI 服务。请确保后端服务 (Port 8765) 正在运行。',
            isError: true,
            timestamp: new Date()
        })
        isTyping.value = false
        currentStatus.value = ''
        return
     }
  }
  
  
  
  abortController.value = new AbortController()
  
  // Don't add assistant message yet - wait for first chunk
  // This prevents the "empty bubble" flash
  let assistantMessageIndex = -1
  
  try {
    const noteContext = includeActiveNote.value ? getCurrentNoteContext() : ""
    const activeNoteId = includeActiveNote.value ? (noteStore.currentNote?.id || null) : null
    
    // Detection for knowledge search in text
    const kbTrigger = "@笔记知识库"
    let finalMessage = messageText
    let explicitKnowledge = false
    
    if (!isResume && messageText.startsWith(kbTrigger)) {
      explicitKnowledge = true
      finalMessage = messageText.substring(kbTrigger.length).trim()
    }

    // Note: We no longer send full history. Backend manages state via session_id.
    const payload: any = {
      message: isResume ? '__resume__' : finalMessage,
      session_id: currentSessionId.value,
      history: [], // Deprecated client-side history
      note_context: noteContext,
      active_note_id: activeNoteId,
      use_knowledge: explicitKnowledge,  // @ knowledge search flag
      auto_accept_writes: autoAcceptEdits.value,
      agent_mode: agentMode.value,
      model_provider_id: selectedModelProviderId.value,
      model_name: selectedModelName.value,
      resume: options?.resume || null
    }

    // Add context info if selected
    if (!isResume && selectedContextNote.value) {
      payload.context_note_id = selectedContextNote.value.id
      payload.context_note_title = selectedContextNote.value.title
    } else if (!isResume && noteStore.currentNote && includeActiveNote.value) {
      // If no context explicitly selected, fallback to current note if applicable
      payload.current_note_id = noteStore.currentNote.id
      payload.active_note_title = noteStore.currentNote.title
    }

    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: abortController.value.signal,
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) throw new Error('请求失败')
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')
    const decoder = new TextDecoder()
    let buffer = ''
    
    // We'll create the assistant message on the first chunk
    let messageIndex = -1
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // SSE events are delimited by double newline
      const parts = buffer.split('\n\n')
      // The last part is either empty (if events ended perfectly) or a partial event
      buffer = parts.pop() || ''
      
      for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          
          const rawData = line.substring(6).trim() // Remove 'data: '
          if (rawData === '[DONE]') continue
          
          try {
              const chunk = JSON.parse(rawData)
              console.log('[SSE] Parsed chunk:', chunk.type || chunk.tool_call || (chunk.text ? 'text' : 'unknown'))
              
              // 1. Status Update
              if (chunk.type === 'status') {
                  const statusText = normalizeStatusText(String(chunk.text || ''))
                  if (pendingExecutionApproval.value) {
                      currentStatus.value = ''
                  } else if (approvalBusy.value) {
                      currentStatus.value = t('agent.running')
                  } else if (isResume && statusText.toLowerCase().includes('thinking')) {
                      currentStatus.value = t('agent.running')
                  } else {
                      currentStatus.value = statusText
                  }
              }
              else if (chunk.type === 'approval_required') {
                  const approval = normalizeExecutionApproval(chunk.approval)
                  if (approval) {
                      pendingExecutionApproval.value = approval
                      showApprovalPreview.value = true
                      touchedNoteId = approval.noteId || touchedNoteId
                      markToolPartPendingByApproval(approval)
                      currentStatus.value = ''
                      streamInterruptedForApproval = true
                  }
              }
              // NEW: Part-Based Events
              else if (chunk.part_type) {
                  console.log('[SSE] Part event:', chunk.part_type)
                  
                  // Ensure message exists
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                      currentStatus.value = ''
                  }
                  
                  const msg = messages.value[messageIndex]
                  if (!msg.parts) msg.parts = []
                  
                  if (chunk.part_type === 'text') {
                      finalizeAwaitingReadTools()
                      // Find or create text part at the end
                      const lastPart = msg.parts[msg.parts.length - 1]
                      if (lastPart && lastPart.type === 'text') {
                          // Append to existing text part
                          lastPart.content += chunk.delta
                      } else {
                          // Create new text part
                          msg.parts.push({ type: 'text', content: chunk.delta })
                      }
                      // Also update legacy content for compatibility
                      msg.content += chunk.delta
                  } 
                  else if (chunk.part_type === 'tool') {
                      if (chunk.status === 'running' || chunk.status === 'pending') {
                          if (!autoAcceptEdits.value && chunk.tool === 'update_note') {
                              const toolNoteId = extractNoteIdFromToolInputPreview(chunk.input_preview)
                              if (toolNoteId) {
                                  touchedNoteId = toolNoteId
                                  await capturePreUpdateSnapshot(toolNoteId)
                              } else if (includeActiveNote.value && noteStore.currentNote?.id) {
                                  touchedNoteId = noteStore.currentNote.id
                                  await capturePreUpdateSnapshot(noteStore.currentNote.id)
                              }
                          }
                          // Add new tool part with toolId
                          msg.parts.push({
                              type: 'tool',
                              tool: chunk.tool,
                              toolId: chunk.tool_id,
                              status: chunk.status === 'pending' ? 'pending' : 'running',
                              startedAt: Date.now(),
                              title: chunk.title,
                              inputPreview: chunk.input_preview
                          } as ToolPart)
                      } 
                      else if (chunk.status === 'completed') {
                          // Update existing tool part globally - completion may arrive in a resumed stream
                          let toolPart: ToolPart | null = null
                          if (chunk.tool_id) {
                              toolPart = findToolPartForCompletion(chunk.tool_id, chunk.tool)
                          }
                          if (!toolPart) {
                              toolPart = findToolPartForCompletion(undefined, chunk.tool)
                          }
                          if (toolPart) {
                              toolPart.output = chunk.output
                              markToolPartCompleted(toolPart, chunk.tool)
                          }
                          if (chunk.tool === 'update_note') {
                              const previousContent =
                                noteStore.currentNote?.id === (pendingExecutionApproval.value?.noteId || noteStore.currentNote?.id)
                                  ? (noteStore.currentNote?.content || '')
                                  : undefined
                              const noteId =
                                extractNoteIdFromToolInputPreview(toolPart?.inputPreview) ||
                                pendingExecutionApproval.value?.noteId ||
                                (includeActiveNote.value ? (noteStore.currentNote?.id || null) : null)
                              touchedNoteId = noteId || touchedNoteId
                              await refreshUpdatedNoteRealtime(noteId, previousContent)
                          } else if (chunk.tool === 'set_note_category') {
                              const noteId =
                                extractNoteIdFromToolInputPreview(toolPart?.inputPreview) ||
                                pendingExecutionApproval.value?.noteId ||
                                (includeActiveNote.value ? (noteStore.currentNote?.id || null) : null)
                              await noteStore.loadNotes({ updateTotalCount: false })
                              if (noteId && noteStore.currentNote?.id === noteId) {
                                const latest = await noteRepository.getById(noteId)
                                if (latest) {
                                  noteStore.currentNote = latest
                                }
                              }
                          }
                      }
                      else if (chunk.status === 'error') {
                          // Update existing tool part globally - error may arrive after a resumed/blocked execution.
                          let toolPart: ToolPart | null = null
                          if (chunk.tool_id) {
                              toolPart = findToolPartForCompletion(chunk.tool_id, chunk.tool)
                          }
                          if (!toolPart) {
                              toolPart = findToolPartForCompletion(undefined, chunk.tool)
                          }
                          if (toolPart) {
                              toolPart.status = 'error'
                              toolPart.output = chunk.output
                          } else {
                              msg.parts.push({
                                  type: 'tool',
                                  tool: chunk.tool,
                                  toolId: chunk.tool_id,
                                  status: 'error',
                                  startedAt: Date.now(),
                                  title: chunk.title,
                                  output: chunk.output,
                                  inputPreview: chunk.input_preview
                              } as ToolPart)
                          }
                      }
                  }
                  
                  messages.value = [...messages.value]
                  scrollToBottom()
              }
              // 2. Legacy Tool Call (for actions like note_created)
              else if (chunk.tool_call) {
                  // Ensure bubble exists
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                  }
                  // Wrap in separate try-catch to not block text processing
                  try {
                      await handleToolCallEvent(chunk, messages.value[messageIndex])
                  } catch (toolErr) {
                      console.warn('[SSE] Tool event handling failed (non-blocking):', toolErr)
                  }
              } 
              // 3. Legacy Text Content (fallback)
              else if (chunk.text) {
                  console.log('[SSE] Legacy text chunk:', chunk.text.substring(0, 20))
                  // Normal text
                  if (messageIndex === -1) {
                      const assistantMessage: ChatMessage = {
                          role: 'assistant',
                          content: '',
                          parts: [],
                          timestamp: new Date()
                      }
                      messages.value.push(assistantMessage)
                      streamingMessage.value = assistantMessage
                      messageIndex = messages.value.length - 1
                      
                      // Clear status
                      currentStatus.value = ''
                  }
                  
                  if (currentStatus.value) currentStatus.value = ''
                  
                  messages.value[messageIndex].content += chunk.text
                  messages.value = [...messages.value]
                  scrollToBottom()
              }
              // 4. Error
              else if (chunk.error) {
                   if (messageIndex === -1) {
                      messages.value.push({ role: 'assistant', content: '', parts: [], timestamp: new Date(), isError: true })
                      messageIndex = messages.value.length - 1
                   }
                   messages.value[messageIndex].content += `错误：${chunk.error}`
              }
          } catch (e) {
              console.warn("Failed to parse SSE JSON:", rawData, e)
          }
      }
    }
    
    // Guard against no message created (edge case)
    if (messageIndex === -1) {
      messages.value.push({ role: 'assistant', content: '*(No response received)*', timestamp: new Date() })
      messageIndex = messages.value.length - 1
    }
    
    const finalMsg = messages.value[messageIndex]
    
    // Improved Tool-Call Detection: Check for JSON embedded anywhere in the message
    // or if the message is purely a JSON tool call.
    const trimmedContent = finalMsg.content.trim()
    let toolData = null
    
    // Case 1: Pure JSON
    if (trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) {
      try { toolData = JSON.parse(trimmedContent) } catch (e) {}
    } 
    // Case 2: Embedded JSON (happens in multi-task scenarios)
    else {
      const jsonMatch = trimmedContent.match(/\{"tool_call":.*\}/s)
      if (jsonMatch) {
        try { 
          toolData = JSON.parse(jsonMatch[0])
          // Remove the raw JSON from the displayed text
          finalMsg.content = finalMsg.content.replace(jsonMatch[0], '').trim()
        } catch (e) {}
      }
    }

    if (toolData) {
      try {
        const data = toolData
        if (data.tool_call === 'note_created') {
          await noteStore.loadNotes()
          if (data.note_id) {
            const newNote = await noteRepository.getById(data.note_id)
            if (newNote) noteStore.currentNote = newNote
          }
          finalMsg.content = data.message || '已成功创建笔记。'
        } else if (data.tool_call === 'note_updated') {
          await noteStore.loadNotes()
          // Refresh editor content if the updated note is currently open
          if (data.note_id && data.note_id !== 'unknown' && noteStore.currentNote?.id === data.note_id) {
            const updatedNote = await noteRepository.getById(data.note_id)
            if (updatedNote) {
              noteStore.currentNote = { ...updatedNote }
              if (setEditorContent) {
                setEditorContent(updatedNote.content)
              }
            }
          }
          finalMsg.content = data.message || '笔记已更新。'
        } else if (data.tool_call === 'note_deleted') {
          await noteStore.loadNotes()
          finalMsg.content = data.message || '笔记已移动到回收站。'
        } else if ((data.tool_call === 'format_apply' || data.tool_call === 'note_updated') && data.formatted_html && setEditorContent) {
          const renderedHtml = await marked.parse(data.formatted_html, { async: true, breaks: true, gfm: true })
          setEditorContent(renderedHtml)
          finalMsg.content = finalMsg.content || data.message || '笔记同步完成。'
        } else if (data.tool_call === 'note_summarized') {
          finalMsg.content = data.message || data.content
        }
        messages.value = [...messages.value]
      } catch (e) {
        console.error('Tool execution error:', e)
      }
    }
    
    if (!isOpen.value) hasUnread.value = true
  } catch (error: any) {
    if (error.name === 'AbortError') {
      if (streamingMessage.value) streamingMessage.value.content += ' \n\n*(已由用户停止生成)*'
    } else {
      if (streamingMessage.value) streamingMessage.value.content = '无法连接到 AI 服务。请确保后端服务 (Port 8765) 正在运行。'
    }
    // Mark all running tools as completed/aborted on error
    finalizeRunningTools(streamingMessage.value, { completeRunning: !streamInterruptedForApproval })
  } finally {
    if (touchedNoteId) {
      try {
        await refreshUpdatedNoteRealtime(touchedNoteId)
      } catch (err) {
        console.warn('[Agent] Final realtime refresh failed:', err)
      }
    }
    // Always finalize any remaining running tools
    finalizeRunningTools(streamingMessage.value, { completeRunning: !streamInterruptedForApproval })
    
    isTyping.value = false
    streamingMessage.value = null
    currentStatus.value = ''
    abortController.value = null
    scrollToBottom()
  }
}

// Helper: Mark all "running" tool parts as completed when stream ends
function finalizeRunningTools(
  msg: ChatMessage | null,
  options?: { completeRunning?: boolean }
) {
  if (!msg || !msg.parts) return
  const completeRunning = options?.completeRunning ?? true
  let changed = false
  for (const part of msg.parts) {
    if (part.type === 'tool' && (part as ToolPart).status === 'running') {
      if (completeRunning) {
        (part as ToolPart).status = 'completed'
        changed = true
      }
    }
  }
  if (changed) {
    messages.value = [...messages.value]
  }
}

async function handleToolCallEvent(data: any, msg: any) {
  try {
    if (data.tool_call === 'note_created') {
      await noteStore.loadNotes()
      if (data.note_id) {
        const newNote = await noteRepository.getById(data.note_id)
        if (newNote) noteStore.currentNote = newNote
      }
    } else if (data.tool_call === 'note_updated') {
      const targetNoteId = data.note_id || noteStore.currentNote?.id || null
      await noteStore.loadNotes()
      const fresh = targetNoteId ? await noteRepository.getById(targetNoteId) : undefined

      if (!autoAcceptEdits.value && targetNoteId && fresh) {
        const before = preUpdateSnapshots.value[targetNoteId]
        const after = snapshotFromNote(fresh)
        if (before && snapshotsDiffer(before, after)) {
          applySnapshot(before)
          addPendingApproval({
            id: crypto.randomUUID(),
            noteId: targetNoteId,
            noteTitle: fresh.title || targetNoteId,
            before,
            after,
            beforePreview: previewText(snapshotToText(before)),
            afterPreview: previewText(snapshotToText(after)),
            createdAt: Date.now()
          })
          delete preUpdateSnapshots.value[targetNoteId]
          messages.value = [...messages.value]
          return
        }
      }

      if (targetNoteId && noteStore.currentNote?.id === targetNoteId) {
        const latest = fresh || await noteRepository.getById(targetNoteId)
        if (latest) {
          noteStore.currentNote = latest
          if (setEditorContent) {
            setEditorContent(latest.content)
          }
        }
      }

      if (targetNoteId) {
        delete preUpdateSnapshots.value[targetNoteId]
      }

    } else if (data.tool_call === 'note_deleted') {
      try {
        await noteStore.loadNotes()
      } catch (e) {
        // Fallback: Remove from local state if DB refresh fails
        console.warn('[Agent] noteStore.loadNotes() failed, using local removal fallback')
        if (data.note_id && noteStore.notes) {
          noteStore.notes = noteStore.notes.filter((n: any) => n.id !== data.note_id)
          // Clear current note if it was deleted
          if (noteStore.currentNote?.id === data.note_id) {
            noteStore.currentNote = noteStore.notes[0] || null
          }
        }
      }
    } else if (data.tool_call === 'note_categorized') {
      const targetNoteId = noteStore.currentNote?.id || null
      await noteStore.loadNotes({ updateTotalCount: false })
      if (targetNoteId && noteStore.currentNote?.id === targetNoteId) {
        const latest = await noteRepository.getById(targetNoteId)
        if (latest) noteStore.currentNote = latest
      }
    } else if (data.tool_call === 'note_renamed') {
      // Refresh note list to show new title
      await noteStore.loadNotes()
      // Also refresh current note to update title in editor header
      if (noteStore.currentNote?.id) {
        const fresh = await noteRepository.getById(noteStore.currentNote.id)
        if (fresh) noteStore.currentNote = fresh
      }
    } else if ((data.tool_call === 'format_apply' || data.tool_call === 'note_updated') && data.formatted_html && setEditorContent) {
      // Fix: 'breaks: false' to prevent double spacing (newlines becoming <br>)
      // Ideally, the editor should handle markdown block spacing naturally.
      const renderedHtml = await marked.parse(data.formatted_html, { async: true, breaks: false, gfm: true })
      setEditorContent(renderedHtml)
      // Silent sync, no change to msg.content
    } else if (data.tool_call === 'note_summarized') {
      msg.content = data.message || data.content
    }
    messages.value = [...messages.value]
  } catch (e) {
    console.error('Real-time tool execution error:', e)
  }
}

function stopGeneration() {
  if (abortController.value) abortController.value.abort()
}

function getCurrentNoteContext(): string | null {
  try {
    const editor = document.querySelector('.tiptap.ProseMirror') as any
    if (editor && editor._tiptap) return editor._tiptap.getHTML()
    const editorContent = document.querySelector('.ProseMirror')?.innerHTML
    return editorContent || null
  } catch { return null }
}

function scrollToBottom(force = false) {
  nextTick(() => {
    if (messagesContainer.value) {
      // Only auto-scroll if user hasn't scrolled up, or if forced
      if (force || !userScrolledUp.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        userScrolledUp.value = false
        showScrollToBottom.value = false
      }
    }
  })
}

// Handle user scroll to detect if they scrolled up
function handleMessagesScroll() {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
  
  if (isAtBottom) {
    userScrolledUp.value = false
    showScrollToBottom.value = false
  } else {
    userScrolledUp.value = true
    showScrollToBottom.value = true
  }
}

// Force scroll to bottom (for button click)
function forceScrollToBottom() {
  userScrolledUp.value = false
  showScrollToBottom.value = false
  scrollToBottom(true)
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  
  try {
    const mathBlocks: string[] = []
    const mathInlines: string[] = []

    // 1. Double escape certain math chars and protect blocks
    let tmp = text
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, f) => {
        mathBlocks.push(f)
        return `__MATH_BLOCK_${mathBlocks.length - 1}__`
      })
      .replace(/\$([^\$\n]+?)\$/g, (_, f) => {
        mathInlines.push(f)
        return `__MATH_INLINE_${mathInlines.length - 1}__`
      })

    // 2. Render Markdown
    const renderer = new marked.Renderer()
    
    // 馃敆 Enterprise Link Handling: Force open in external browser
    // Updated for marked v17+ compatibility
    renderer.link = (token) => {
      const href = token.href || ''
      const title = token.title || ''
      const text = token.text || ''
      const cleanHref = href.replace(/&amp;/g, '&')
      return `<a href="${cleanHref}" title="${title}" target="_blank" rel="noopener noreferrer">${text}</a>`
    }

    renderer.code = (token) => {
      const { text, lang } = token
      const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
      const highlighted = hljs.highlight(text, { language }).value
      return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`
    }
    
    let html = marked.parse(tmp, { renderer, async: false, breaks: true, gfm: true }) as string

    // Helper to decode entities
    const decodeEntities = (s: string) => s
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/<br\s*\/?>/gi, '\n')

    // 3. Restore and render KaTeX
    html = html.replace(/__MATH_BLOCK_(\d+)__/g, (_, i) => {
      try {
        const raw = decodeEntities(mathBlocks[parseInt(i)])
        return `<div class="math-block">${katex.renderToString(raw, { displayMode: true, throwOnError: false })}</div>`
      } catch (e) { return `<div class="math-error">$$${mathBlocks[parseInt(i)]}$$</div>` }
    })

    html = html.replace(/__MATH_INLINE_(\d+)__/g, (_, i) => {
      try {
        const raw = decodeEntities(mathInlines[parseInt(i)])
        return `<span class="math-inline">${katex.renderToString(raw, { displayMode: false, throwOnError: false })}</span>`
      } catch (e) { return `<span class="math-error">$${mathInlines[parseInt(i)]}$</span>` }
    })

    return html
  } catch (e) {
    console.error('Markdown rendering error:', e)
    return text
  }
}


function adjustHeight() {
  if (!inputRef.value) return
  inputRef.value.style.height = 'auto'
  const newHeight = Math.min(inputRef.value.scrollHeight, 150)
  inputRef.value.style.height = `${newHeight}px`
}

function handleContextMenu(event: MouseEvent, content: string) {
  event.preventDefault()

  // Remove existing context menus first
  const existingMenus = document.querySelectorAll('.agent-context-menu')
  existingMenus.forEach((m: Element) => m.remove())
  
  const selection = window.getSelection()
  const selectedText = selection?.toString() || content
  const menu = document.createElement('div')
  menu.className = 'agent-context-menu'
  menu.style.cssText = `position: fixed; left: ${event.clientX}px; top: ${event.clientY}px; background: white; border: 1px solid #E8E4DF; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 4px 0; z-index: 10000; min-width: 120px;`
  const copyItem = document.createElement('div')
  copyItem.textContent = '复制'
  copyItem.style.cssText = `padding: 8px 16px; cursor: pointer; font-size: 14px; color: #2D2A26;`
  copyItem.onmouseover = () => { copyItem.style.background = '#F5F1EC' }
  copyItem.onmouseout = () => { copyItem.style.background = 'transparent' }
  copyItem.onclick = () => { navigator.clipboard.writeText(selectedText); menu.remove() }
  menu.appendChild(copyItem)
  document.body.appendChild(menu)
  const removeMenu = (e: MouseEvent) => { if (!menu.contains(e.target as Node)) { menu.remove(); document.removeEventListener('click', removeMenu) } }
  setTimeout(() => document.addEventListener('click', removeMenu), 0)
}

watch(inputText, () => {
  nextTick(() => resizeComposerInput(inputRef.value))
})

watch(autoAcceptEdits, (enabled) => {
  localStorage.setItem(AUTO_ACCEPT_EDITS_KEY, enabled ? '1' : '0')
  // Keep behavior consistent: when user switches to auto-accept while a write
  // approval is already pending, apply it immediately in the same turn.
  if (enabled && pendingExecutionApproval.value && !approvalBusy.value) {
    void respondExecutionApproval('approve').catch((err) => {
      console.warn('[Agent] Auto-approve on toggle failed:', err)
    })
  }
})

watch(agentMode, (mode) => {
  localStorage.setItem(AGENT_MODE_KEY, mode)
})

watch(isSidebarMode, (enabled) => {
  if (enabled) {
    isOpen.value = true
    hasUnread.value = false
  }
  window.dispatchEvent(new CustomEvent('origin-agent-sidebar-mode-changed', { detail: { enabled } }))
})

watch(messages, () => {
  schedulePersistUiState()
}, { deep: true })

watch(pendingApprovals, () => {
  schedulePersistUiState()
}, { deep: true })

watch(pendingExecutionApproval, () => {
  schedulePersistUiState()
}, { deep: true })

watch(showApprovalPreview, () => {
  schedulePersistUiState()
})

watch(executionExpanded, () => {
  schedulePersistUiState()
})

watch(
  [pendingExecutionApproval, pendingApprovals],
  ([executionApproval, diffApprovals]) => {
    if (executionApproval) {
      showApprovalPreview.value = true
      return
    }
    if (!diffApprovals || diffApprovals.length === 0) {
      showApprovalPreview.value = false
      showUnchangedDiff.value = false
    }
  },
  { deep: true }
)
</script>

<style scoped>
/* ===== 馃帹 Theme: Warm Glass (Claude-Inspired) with Dark Mode Support ===== */
.agent-container {
  /* Light Theme Variables (Default) */
  --theme-bg: rgba(250, 248, 245, 0.72);
  --theme-bg-solid: rgba(255, 255, 255, 0.86);
  --theme-text: #2D2A26;
  --theme-text-secondary: #6B6762;
  --theme-accent: #D97D54;
  --theme-accent-light: rgba(254, 243, 238, 0.7);
  --theme-border: rgba(232, 228, 223, 0.52);
  --theme-input-bg: rgba(0, 0, 0, 0.04);
  --theme-code-bg: #F3F4F6;
  --theme-bubble-bg: rgba(255, 255, 255, 0.54);
  --theme-bubble-active: rgba(255, 255, 255, 0.9);
  --theme-header-bg: rgba(255, 255, 255, 0.38);
  --theme-footer-bg: rgba(255, 255, 255, 0.36);
  --theme-suggestion-bg: rgba(255, 255, 255, 0.58);
  --theme-surface: rgba(255, 255, 255, 0.52);
  --theme-hover: rgba(24, 28, 35, 0.06);
  --theme-bg-secondary: rgba(248, 245, 241, 0.68);
  --theme-bg-hover: rgba(244, 240, 235, 0.76);
  --theme-ring: rgba(217, 125, 84, 0.25);
  --theme-shadow-soft: 0 16px 40px rgba(26, 18, 11, 0.14);
  --theme-shadow-strong: 0 28px 72px rgba(26, 18, 11, 0.22);
  --hero-grad-1: #bf6d43;
  --hero-grad-2: #d99f62;
  --hero-grad-3: #80583f;

  position: fixed;
  z-index: 9999;
}

/* Dark Theme Override */
[data-theme="dark"] .agent-container {
  --theme-bg: rgba(20, 22, 28, 0.74);
  --theme-bg-solid: rgba(30, 33, 40, 0.88);
  --theme-text: #E8E8E6;
  --theme-text-secondary: #A8A8A5;
  --theme-accent: #E8A87C;
  --theme-accent-light: rgba(232, 168, 124, 0.15);
  --theme-border: rgba(126, 132, 150, 0.28);
  --theme-input-bg: rgba(255, 255, 255, 0.06);
  --theme-code-bg: #1E1E22;
  --theme-bubble-bg: rgba(50, 50, 55, 0.64);
  --theme-bubble-active: rgba(60, 60, 65, 0.95);
  --theme-header-bg: rgba(40, 40, 45, 0.52);
  --theme-footer-bg: rgba(35, 35, 38, 0.58);
  --theme-suggestion-bg: rgba(42, 42, 46, 0.62);
  --theme-surface: rgba(42, 45, 54, 0.62);
  --theme-hover: rgba(255, 255, 255, 0.085);
  --theme-bg-secondary: rgba(34, 37, 46, 0.72);
  --theme-bg-hover: rgba(54, 58, 69, 0.78);
  --theme-ring: rgba(232, 168, 124, 0.28);
  --theme-shadow-soft: 0 22px 52px rgba(0, 0, 0, 0.56);
  --theme-shadow-strong: 0 34px 82px rgba(0, 0, 0, 0.66);
  --hero-grad-1: #f1bb8f;
  --hero-grad-2: #f0d5a5;
  --hero-grad-3: #c69266;
}

[data-theme="dark"] .chat-input-unified-box {
  box-shadow:
    0 14px 30px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.28);
}

[data-theme="dark"] .send-btn-compact {
  background: linear-gradient(160deg, rgba(232, 168, 124, 0.24), rgba(69, 55, 47, 0.4));
  color: #f6dcc1;
}

[data-theme="dark"] .agent-chat::before {
  background:
    radial-gradient(140% 60% at 20% 0%, rgba(255, 255, 255, 0.08), transparent 48%),
    radial-gradient(120% 70% at 80% 100%, rgba(255, 255, 255, 0.035), transparent 58%);
}

[data-theme="dark"] .agent-chat__messages {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.015), rgba(255, 255, 255, 0));
}

[data-theme="dark"] .agent-chat__header,
[data-theme="dark"] .agent-chat__footer {
  border-color: rgba(255, 255, 255, 0.08);
}

/* Classic Theme Override */
[data-theme="classic"] .agent-container {
  --theme-bg: rgba(255, 255, 255, 0.84);
  --theme-bg-solid: rgba(255, 255, 255, 0.95);
  --theme-text: #1F1F1F;
  --theme-text-secondary: #666666;
  --theme-accent: #D97D54;
  --theme-accent-light: #FEF3EE;
  --theme-border: rgba(0, 0, 0, 0.06);
  --theme-input-bg: rgba(0, 0, 0, 0.02);
  --theme-code-bg: #FAFAFA;
  --theme-bubble-bg: rgba(255, 255, 255, 0.7);
  --theme-bubble-active: rgba(255, 255, 255, 1);
  --theme-header-bg: rgba(255, 255, 255, 0.74);
  --theme-footer-bg: rgba(255, 255, 255, 0.72);
  --theme-suggestion-bg: rgba(255, 255, 255, 0.8);
  --theme-surface: rgba(255, 255, 255, 0.74);
  --theme-hover: rgba(17, 24, 39, 0.06);
  --theme-bg-secondary: rgba(248, 249, 251, 0.75);
  --theme-bg-hover: rgba(240, 244, 248, 0.85);
  --theme-ring: rgba(217, 125, 84, 0.22);
  --theme-shadow-soft: 0 16px 38px rgba(15, 23, 42, 0.12);
  --theme-shadow-strong: 0 20px 52px rgba(15, 23, 42, 0.18);
  --hero-grad-1: #b76b43;
  --hero-grad-2: #cc8f57;
  --hero-grad-3: #6e4c38;
}

/* Glassmorphism Panel Base */
.glass-panel {
  background: var(--theme-bg);
  backdrop-filter: blur(24px) saturate(1.16);
  -webkit-backdrop-filter: blur(24px) saturate(1.16);
  border: 1px solid var(--theme-border);
  box-shadow: var(--theme-shadow-soft);
}

/* ===== 馃煝 Bubble: Draggable & Dockable ===== */
.agent-bubble {
  width: 50px;
  height: 50px;
  border-radius: 25px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  
  /* Bubble Style */
  background: var(--theme-bubble-bg);
  color: var(--theme-accent);
  border: 1px solid var(--theme-border);
  box-shadow: 0 10px 24px rgba(18, 14, 8, 0.18);
}

/* Dragging State */
.agent-container.is-dragging .agent-bubble {
  cursor: grabbing;
  transform: scale(1.1);
  background: var(--theme-bubble-active);
}

/* Docked State (Idle) */
.agent-container.is-docked .agent-bubble {
  opacity: 0.6;
  border-color: transparent;
  background: var(--theme-bubble-bg);
}
.agent-container.is-docked:hover .agent-bubble {
  opacity: 1;
  background: var(--theme-bubble-active);
}

/* Active State (Chat Open) */
.agent-bubble--active {
  background: var(--theme-accent) !important;
  color: white !important;
  box-shadow: 0 12px 28px rgba(217, 125, 84, 0.45);
}

.agent-bubble:active {
  transform: scale(0.95);
}

.agent-bubble__icon {
  width: 24px;
  height: 24px;
  pointer-events: none;
}
.agent-bubble__icon svg { width: 100%; height: 100%; }

.agent-bubble__badge {
  position: absolute;
  top: 0; right: 0;
  width: 12px; height: 12px;
  background: #EF4444;
  border-radius: 50%;
  border: 2px solid white;
}

/* ===== 馃挰 Chat Window ===== */
.agent-chat {
  position: absolute;
  bottom: 60px;
  right: 0;
  width: 380px;
  height: 520px;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: bottom right;
  z-index: 10000;
  
  /* Warm Texture with theme support */
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 88%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 86%, transparent));
  transition: background 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease, transform 0.2s ease;
  border: 1px solid var(--theme-border);
  box-shadow: var(--theme-shadow-strong);
  isolation: isolate;
}

.agent-chat::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.32), transparent 24%, transparent 72%, rgba(255, 255, 255, 0.14));
  z-index: 0;
}

.agent-chat::after {
  content: "";
  position: absolute;
  inset: 1px;
  pointer-events: none;
  border-radius: calc(18px - 1px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44), inset 0 -1px 0 rgba(0, 0, 0, 0.03);
  z-index: 0;
}

.agent-chat > * {
  position: relative;
  z-index: 1;
}

.agent-container--sidebar {
  z-index: 10000;
}

.agent-chat.sidebar-mode {
  position: fixed;
  top: var(--app-titlebar-height, 32px);
  bottom: 0;
  right: 0;
  width: var(--agent-sidebar-width, 460px);
  height: auto;
  max-height: none;
  left: auto;
  border-radius: 0;
  border-left: 1px solid var(--theme-border);
  box-shadow: none;
  transform-origin: top right;
}

.agent-chat.sidebar-mode::after {
  border-radius: 0;
}

/* Responsive Chat Window - Scale up on larger screens */
@media (min-width: 1200px) {
  .agent-chat:not(.maximized):not(.sidebar-mode) {
    width: 420px;
    height: 580px;
  }
}

@media (min-width: 1600px) {
  .agent-chat:not(.maximized):not(.sidebar-mode) {
    width: 480px;
    height: 650px;
  }
}

@media (min-width: 1920px) {
  .agent-chat:not(.maximized):not(.sidebar-mode) {
    width: 520px;
    height: 720px;
  }
}

/* Maximized State */
.agent-chat.maximized {
  position: fixed;
  top: 50px;
  left: 20px;
  right: 20px;
  bottom: 20px;
  width: auto;
  height: auto;
  transform: none !important;
  max-width: none;
  max-height: none;
  z-index: 10001;
}

/* Flip if on left */
.agent-chat.align-left {
  right: auto;
  left: 0;
  transform-origin: bottom left;
}

/* Animation - 鑻规灉椋庢牸涓濇粦寮瑰嚭 */
.chat-window-enter-active,
.chat-window-leave-active {
  transition: opacity 0.25s cubic-bezier(0.25, 0.1, 0.25, 1),
              transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
  transform: scale(0.92) translateY(16px);
}

/* Header */
.agent-chat__header {
  padding: 11px 14px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--theme-header-bg) 90%, white 10%), color-mix(in srgb, var(--theme-header-bg) 96%, transparent));
  border-bottom: 1px solid var(--theme-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.3s ease, border-color 0.3s ease;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.agent-chat__title {
  display: flex; align-items: center; gap: 8px;
  font-weight: 650;
  font-size: 16px;
}
.agent-chat__title > span:last-child {
  background: linear-gradient(120deg, var(--hero-grad-1), var(--hero-grad-2), var(--hero-grad-3), var(--hero-grad-2), var(--hero-grad-1));
  background-size: 220% 220%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: heroGradientFlow 5.2s ease-in-out infinite;
}
.agent-chat__avatar {
  width: 17px;
  height: 17px;
  color: var(--theme-accent);
  filter: drop-shadow(0 0 6px color-mix(in srgb, var(--theme-accent) 30%, transparent));
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.agent-chat__avatar svg {
  width: 100%;
  height: 100%;
}
.agent-chat__actions { display: flex; gap: 4px; }

/* Header Buttons */
.header-btn {
  width: 29px; height: 29px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 76%, transparent);
  background: color-mix(in srgb, var(--theme-surface) 70%, transparent);
  cursor: pointer; color: var(--theme-text-secondary);
  border-radius: 999px;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s ease, color 0.16s ease, border-color 0.2s ease, transform 0.12s ease, box-shadow 0.2s ease;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
}
.header-btn:hover {
  background: color-mix(in srgb, var(--theme-bg-hover) 74%, transparent);
  border-color: color-mix(in srgb, var(--theme-accent) 18%, var(--theme-border));
  color: var(--theme-text);
  box-shadow: 0 8px 14px color-mix(in srgb, #000 14%, transparent);
}
.header-btn:active {
  transform: scale(0.96);
}
.header-btn svg { width: 16px; height: 16px; }

/* Status */
.agent-chat__status { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--theme-text-secondary); margin-left: 8px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot--online { background: #22C55E; }
.status-dot--offline { background: var(--theme-text-secondary); }

/* Messages Area */
.agent-chat__messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scroll */
  padding: 20px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

/* Readability Fix for Wide Windows */
.agent-chat.maximized .agent-chat__messages {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}
.agent-chat.maximized .agent-chat__input {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

/* Scroll to bottom button */
.scroll-to-bottom-btn {
  position: absolute;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--theme-bg-secondary);
  border: 1px solid var(--theme-border);
  color: var(--theme-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
              background 0.15s cubic-bezier(0.25, 0.1, 0.25, 1),
              box-shadow 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  z-index: 10;
  will-change: transform;
  backface-visibility: hidden;
}
.scroll-to-bottom-btn:hover {
  background: var(--theme-bg-hover);
  color: var(--theme-text);
  transform: translateX(-50%) translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
}
.scroll-to-bottom-btn:active {
  transform: translateX(-50%) translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
.scroll-to-bottom-btn svg {
  width: 18px;
  height: 18px;
}

/* Welcome Screen */
.agent-chat__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  max-width: 500px;
  margin: clamp(30px, 6vh, 72px) auto clamp(34px, 8vh, 96px);
  text-align: center;
  padding: 0 12px;
  box-sizing: border-box;
}

.agent-chat__welcome h3 {
  margin: 0 0 8px;
  font-family: "Segoe UI Variable", "Segoe UI", "PingFang SC", sans-serif;
  font-weight: 580;
  font-size: clamp(24px, 3.2vw, 30px);
  letter-spacing: -0.012em;
  line-height: 1.16;
  background: linear-gradient(120deg, var(--hero-grad-1), var(--hero-grad-2), var(--hero-grad-3), var(--hero-grad-2), var(--hero-grad-1));
  background-size: 240% 240%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  max-width: 460px;
  text-wrap: balance;
  animation: heroGradientFlow 5.2s ease-in-out infinite;
}
.agent-chat__welcome p {
  margin: 0;
  color: color-mix(in srgb, var(--theme-text-secondary) 72%, transparent);
  font-size: 12px;
  line-height: 1.55;
  max-width: 430px;
  text-wrap: pretty;
}
.welcome-icon {
  width: 23px;
  height: 23px;
  color: var(--theme-accent);
  margin-bottom: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0.88;
  filter: drop-shadow(0 0 6px color-mix(in srgb, var(--theme-accent) 22%, transparent));
}
.welcome-icon svg {
  width: 100%;
  height: 100%;
}

@keyframes heroGradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@media (prefers-reduced-motion: reduce) {
  .agent-chat__welcome h3 {
    animation: none;
    background-position: 50% 50%;
  }
  .agent-chat__title > span:last-child {
    animation: none;
    background-position: 50% 50%;
  }
  .tool-part__name--running {
    animation: none;
    background-position: 50% 50%;
  }
}

.agent-chat__hero-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
  margin-top: 18px;
}


.hero-card {
  border: 1px solid var(--theme-border);
  background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
  border-radius: 14px;
  padding: 12px 12px;
  text-align: left;
  min-height: 112px;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}


.hero-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--theme-accent) 40%, var(--theme-border));
  box-shadow: 0 12px 24px color-mix(in srgb, var(--theme-accent) 10%, transparent);
  background: color-mix(in srgb, var(--theme-accent-light) 50%, var(--theme-surface));
}

.hero-card__title {
  font-size: 18px;
  font-weight: 680;
  color: color-mix(in srgb, var(--theme-accent) 78%, var(--theme-text) 22%);
  margin-bottom: 6px;
  letter-spacing: -0.01em;
}


.hero-card__desc {
  font-size: 12px;
  line-height: 1.5;
  color: color-mix(in srgb, var(--theme-text-secondary) 78%, transparent);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}


.hero-action-strip {
  width: 100%;
  margin-top: 8px;
  text-align: left;
}

.hero-action-strip__label {
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-accent) 72%, var(--theme-text) 28%);
  margin-bottom: 6px;
  padding-left: 4px;
  font-weight: 600;
}

.hero-action-strip__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hero-action-btn {
  border: 1px solid color-mix(in srgb, var(--theme-accent) 24%, var(--theme-border));
  background: color-mix(in srgb, var(--theme-accent-light) 58%, var(--theme-surface));
  color: color-mix(in srgb, var(--theme-text) 82%, var(--theme-accent) 18%);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 11px;
  line-height: 1.2;
  cursor: pointer;
  transition: transform 0.14s ease, background 0.14s ease, border-color 0.14s ease;
}

.hero-action-btn:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--theme-accent) 40%, var(--theme-border));
  background: color-mix(in srgb, var(--theme-accent-light) 80%, var(--theme-surface));
}

.agent-chat__hero-list {
  width: 100%;
  margin-top: 10px;
  padding: 2px 2px 2px 12px;
  border: none;
  border-radius: 0;
  background: transparent;
  text-align: left;
  border-left: 3px solid color-mix(in srgb, var(--theme-accent) 70%, transparent);
}


.hero-list__label {
  font-size: 13px;
  color: color-mix(in srgb, var(--theme-accent) 72%, var(--theme-text) 28%);
  font-weight: 620;
  margin-bottom: 8px;
  padding-left: 0;
}

.hero-list__items {
  padding-left: 16px;
  padding-top: 0;
  padding-bottom: 4px;
  margin: 0;
  color: color-mix(in srgb, var(--theme-text-secondary) 80%, transparent);
  display: grid;
  gap: 3px;
  font-size: 12px;
  line-height: 1.48;
  list-style-position: outside;
}


/* Suggestion Chips */
.agent-chat__suggestions {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  grid-template-areas:
    "chip1 chip1 chip1 chip2 chip2 chip2"
    "chip3 chip3 chip4 chip4 chip4 chip4";
  gap: 8px;
  width: 100%;
  margin-top: 10px;
}


.suggestion-chip {
  background: color-mix(in srgb, var(--theme-surface) 94%, transparent);
  border: 1px solid var(--theme-border);
  min-height: 36px;
  padding: 8px 11px;
  border-radius: 12px;
  font-size: 11px;
  line-height: 1.35;
  color: color-mix(in srgb, var(--theme-text-secondary) 78%, transparent);
  cursor: pointer;
  text-align: left;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease, color 0.16s ease;
  display: inline-flex;
  align-items: center;
  text-wrap: balance;
}

.suggestion-chip:hover {
  border-color: color-mix(in srgb, var(--theme-accent) 35%, var(--theme-border));
  color: var(--theme-text);
  background: color-mix(in srgb, var(--theme-accent-light) 45%, var(--theme-surface));
  transform: translateY(-1px);
}

.suggestion-chip:nth-child(1) {
  grid-area: chip1;
  border-radius: 15px 9px 13px 11px;
}

.suggestion-chip:nth-child(2) {
  grid-area: chip2;
  border-radius: 9px 15px 11px 13px;
}

.suggestion-chip:nth-child(3) {
  grid-area: chip3;
  border-radius: 13px 10px 16px 9px;
}

.suggestion-chip:nth-child(4) {
  grid-area: chip4;
  border-radius: 10px 16px 9px 14px;
}

@media (max-width: 720px) {
  .agent-chat__hero-cards {
    grid-template-columns: 1fr;
    width: 100%;
  }
  .agent-chat__suggestions {
    grid-template-columns: 1fr;
    grid-template-areas:
      "chip1"
      "chip2"
      "chip3"
      "chip4";
    width: 100%;
  }
  .hero-card {
    min-height: 102px;
  }
  .hero-card__title {
    font-size: 16px;
  }
}

/* Message Wrapper - Logic for Alignment */
.message-wrapper {
  display: flex;
  width: 100%;
}

.message-wrapper.message--user {
  justify-content: flex-end;
}

.message-wrapper.message--assistant {
  justify-content: flex-start;
}

/* Common Message Container */
.message {
  display: flex;
  gap: 8px;
  position: relative;
  /* Remove fixed width from base class to allow flexibility */
}

/* User Bubble Styles (Slim, Warm, Subtle) - fit-content is KEY */
.message--user .message {
  width: fit-content;
  max-width: 85%;
  background: linear-gradient(160deg, color-mix(in srgb, var(--theme-bg-solid) 60%, transparent), color-mix(in srgb, var(--theme-surface) 62%, transparent));
  color: var(--theme-text);
  border: 1px solid color-mix(in srgb, var(--theme-border) 58%, rgba(255, 255, 255, 0.12));
  padding: 10px 16px;
  border-radius: 20px;
  border-bottom-right-radius: 4px;
  box-shadow:
    0 10px 20px color-mix(in srgb, #000 8%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
  margin-left: auto; /* Ensure it stays right even if flex weirdness happens */
}

/* Assistant Text Styles (Minimalist, Claude-like) */
.message--assistant .message {
  background: transparent;
  width: 100%;
  max-width: 100%;
  padding-left: 0;
}

.message__content {
  flex: 1;
  overflow: hidden; /* Prevent horizontal overflow */
  min-width: 0; /* Required for flex child to shrink properly */
  max-width: 100%;
}

.message__text {
  font-size: 12px;
  line-height: 1.6;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  user-select: text; /* Overrides global user-select: none */
  cursor: text;
  max-width: 100%;
  overflow-x: auto; /* Allow scrolling for very wide content like code */
}

/* Tool Part Styles - layered status card */
.tool-part {
  display: grid;
  grid-template-columns: 28px 1fr;
  align-items: center;
  gap: 8px;
  margin: 4px 0;
  padding: 9px 11px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 48%, rgba(255, 255, 255, 0.1));
  border-radius: 12px;
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 62%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 54%, transparent));
  box-shadow:
    0 8px 18px color-mix(in srgb, #000 8%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.13);
}

.tool-part--running {
  border-color: color-mix(in srgb, var(--theme-accent) 24%, var(--theme-border));
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-accent-light) 36%, var(--theme-surface)), color-mix(in srgb, var(--theme-bg-secondary) 80%, transparent));
}

.tool-part--pending {
  border-color: rgba(194, 124, 0, 0.24);
}

.tool-part--completed {
  border-color: color-mix(in srgb, var(--theme-border) 78%, #55a86a 22%);
}

.tool-part--error {
  border-color: rgba(231, 76, 60, 0.24);
}

.tool-part__icon-wrap {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--theme-accent-light) 52%, var(--theme-surface));
  border: 1px solid color-mix(in srgb, var(--theme-border) 74%, var(--theme-accent) 26%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.tool-part__icon {
  font-size: 11px;
  opacity: 0.85;
}

.tool-part__icon-svg {
  width: 13px;
  height: 13px;
  color: color-mix(in srgb, var(--theme-accent) 68%, var(--theme-text-secondary));
}

.tool-part__main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.tool-part__line {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.tool-part__name {
  font-size: 12px;
  line-height: 1.2;
  font-weight: 530;
  color: var(--theme-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-part__name--running {
  background: linear-gradient(120deg, var(--hero-grad-1), var(--hero-grad-2), var(--hero-grad-3), var(--hero-grad-2), var(--hero-grad-1));
  background-size: 220% 220%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: heroGradientFlow 4.8s ease-in-out infinite;
  font-weight: 560;
}

.tool-part__spinner {
  width: 12px;
  height: 12px;
  border: 1.6px solid color-mix(in srgb, var(--theme-accent) 24%, var(--theme-border));
  border-top-color: var(--hero-grad-2);
  border-radius: 999px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tool-part__check {
  color: #55a86a;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.tool-part__pending {
  font-size: 10px;
  color: #9f6b00;
  border: 1px solid rgba(194, 124, 0, 0.28);
  background: rgba(194, 124, 0, 0.1);
  border-radius: 999px;
  padding: 1px 6px;
  line-height: 1.4;
  flex-shrink: 0;
}

.tool-part__output {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  font-size: 11px;
  line-height: 1.2;
  color: color-mix(in srgb, var(--theme-text-secondary) 90%, transparent);
  border: 1px solid var(--theme-border);
  background: color-mix(in srgb, var(--theme-bg-secondary) 72%, transparent);
  border-radius: 999px;
  padding: 3px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Ensure code blocks don't overflow */
.message__text pre {
  max-width: 100%;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.message__text code {
  word-break: break-all;
}

/* Tables should scroll horizontally if too wide but keep table layout */
.message__text table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--theme-border);
  table-layout: auto; /* Allow content to define width */
}

/* Status Update (Floating & Pulsing) */
.status-update {
  align-self: flex-start;
  margin: 4px 0 10px 34px;
  padding: 5px 11px;
  background: linear-gradient(160deg, color-mix(in srgb, var(--theme-accent-light) 32%, var(--theme-surface)), color-mix(in srgb, var(--theme-bg-secondary) 66%, transparent));
  border: 1px solid color-mix(in srgb, var(--theme-accent) 14%, var(--theme-border));
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--theme-accent);
  opacity: 0.96;
  box-shadow: 0 8px 14px color-mix(in srgb, #000 8%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  animation: shimmer 2s infinite ease-in-out;
}

@keyframes shimmer {
  0% { opacity: 0.4; transform: translateY(0px); }
  50% { opacity: 0.8; transform: translateY(-1px); }
  100% { opacity: 0.4; transform: translateY(0px); }
}

.status-update__dots { opacity: 0.6; }

/* Typing Minimal */
.typing-minimal {
  align-self: flex-start;
  margin-left: 40px;
  padding: 8px 0;
}
.typing-indicator span {
  width: 4px; height: 4px; background: var(--theme-text-secondary); border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* ========== Compact & Unified Input Area (v2) ========== */
.agent-chat__footer {
  padding: 12px 14px 14px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--theme-footer-bg) 62%, transparent) 0%,
    color-mix(in srgb, var(--theme-footer-bg) 86%, transparent) 42%,
    color-mix(in srgb, var(--theme-footer-bg) 96%, transparent) 100%
  );
  border-top: 1px solid var(--theme-border);
  transition: background 220ms ease, border-color 220ms ease;
  backdrop-filter: blur(16px) saturate(1.12);
  -webkit-backdrop-filter: blur(16px) saturate(1.12);
}

/* Responsive footer in maximized mode - match chat area width */
.agent-chat.maximized .agent-chat__footer {
  display: flex;
  justify-content: center;
  padding: 14px 22px 16px;
}

.agent-chat.maximized .agent-chat__footer .chat-input-unified-box {
  width: 100%;
  max-width: 800px;
}

/* Context bar alignment in maximized mode */
.agent-chat.maximized .agent-chat__context-bar {
  display: flex;
  justify-content: flex-start; /* Align content to start (left) */
  width: 100%;
  max-width: 800px; /* Match input box width */
  margin: 0 auto;   /* Center the bar itself in the window */
  padding-left: 6px; /* Align strictly with input content (match input padding) */
}


.chat-input-unified-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--theme-surface) 90%, white 10%),
    color-mix(in srgb, var(--theme-bg-secondary) 88%, transparent)
  );
  border: 1px solid color-mix(in srgb, var(--theme-border) 72%, rgba(255, 255, 255, 0.22));
  border-radius: 20px;
  position: relative;
  transition: background 180ms ease, box-shadow 220ms ease, border-color 180ms ease, transform 160ms ease;
  box-shadow:
    0 14px 30px color-mix(in srgb, #000 13%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -1px 0 rgba(0, 0, 0, 0.07);
}

.chat-input-unified-box::before {
  content: '';
  position: absolute;
  inset: 1px;
  pointer-events: none;
  border-radius: 19px;
  background: linear-gradient(140deg, rgba(255, 255, 255, 0.18), transparent 28%, transparent 72%, rgba(255, 255, 255, 0.06));
}

.chat-input-unified-box:focus-within {
  border-color: color-mix(in srgb, var(--theme-accent) 44%, var(--theme-border));
  box-shadow:
    0 0 0 3px var(--theme-ring),
    0 16px 36px color-mix(in srgb, #000 12%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.52);
  transform: translateY(-1px);
}

/* + Menu Wrapper & Button */
.input-menu-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 0;
  z-index: 2;
}

.menu-trigger-btn {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 68%, transparent);
  background: color-mix(in srgb, var(--theme-surface) 64%, transparent);
  color: var(--theme-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 140ms ease, background 180ms ease, border-color 180ms ease, color 140ms ease, box-shadow 180ms ease;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.menu-trigger-btn:hover, .menu-trigger-btn.active {
  color: var(--theme-accent);
  background: color-mix(in srgb, var(--theme-accent-light) 72%, var(--theme-surface));
  border-color: color-mix(in srgb, var(--theme-accent) 30%, var(--theme-border));
  box-shadow: 0 8px 14px color-mix(in srgb, #000 12%, transparent);
}

.menu-trigger-btn:active {
  transform: scale(0.96);
}

.menu-trigger-btn svg {
  width: 15px;
  height: 15px;
}

/* Redesigned Popup Menu (Smaller) */
.input-menu-popup {
  position: absolute;
  bottom: 42px;
  left: 0;
  min-width: 232px;
  background: linear-gradient(160deg, color-mix(in srgb, var(--theme-surface) 94%, white 6%), color-mix(in srgb, var(--theme-bg-secondary) 90%, transparent));
  border: 1px solid color-mix(in srgb, var(--theme-border) 86%, rgba(255, 255, 255, 0.26));
  border-radius: 14px;
  box-shadow: 0 20px 40px color-mix(in srgb, #000 18%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.44);
  overflow: hidden;
  z-index: 120;
  padding: 6px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 11px;
  cursor: pointer;
  border-radius: 9px;
  transition: background 140ms ease, color 140ms ease, transform 140ms ease;
  font-size: 13px;
  color: var(--theme-text);
  font-weight: 520;
}

.menu-item:hover {
  background: color-mix(in srgb, var(--theme-accent-light) 74%, var(--theme-surface));
  color: var(--theme-accent);
  transform: translateX(1px);
}

.menu-icon {
  width: 15px;
  height: 15px;
  text-align: center;
  color: var(--theme-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
}

.menu-icon svg {
  width: 100%;
  height: 100%;
}

.menu-item:hover .menu-icon {
  color: var(--theme-accent);
}

.menu-icon.smaller {
  width: 14px;
  height: 14px;
}

/* Menu Fade Transition */
.menu-fade-enter-active, .menu-fade-leave-active {
  transition: opacity 180ms ease, transform 200ms cubic-bezier(0.22, 0.68, 0.2, 1), filter 180ms ease;
}
.menu-fade-enter-from, .menu-fade-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
  filter: blur(2px);
}

/* Auto-resize Textarea */
.chat-input-unified-box textarea {
  flex: 1;
  min-height: 30px;
  max-height: 128px;
  padding: 5px 2px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.5;
  resize: none;
  outline: none;
  overflow-y: auto;
  color: var(--theme-text);
  z-index: 2;
}

.chat-input-unified-box textarea::placeholder {
  color: var(--theme-text-secondary);
  opacity: 0.68;
  font-size: 11px;
}

/* Compact Send/Stop Buttons */
.send-btn-compact, .stop-btn-compact {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 140ms ease, box-shadow 180ms ease, background 180ms ease, color 140ms ease;
  flex-shrink: 0;
  margin-bottom: 0;
  z-index: 2;
}

.send-btn-compact {
  border: 1px solid color-mix(in srgb, var(--theme-accent) 28%, var(--theme-border));
  background: linear-gradient(160deg, color-mix(in srgb, var(--theme-accent-light) 72%, white 28%), color-mix(in srgb, var(--theme-surface) 88%, transparent));
  color: color-mix(in srgb, var(--theme-accent) 82%, var(--theme-text));
  box-shadow: 0 8px 14px color-mix(in srgb, var(--theme-accent) 20%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.send-btn-compact:hover:not(:disabled) {
  color: #fff;
  background: linear-gradient(145deg, color-mix(in srgb, var(--hero-grad-1) 92%, white 8%), color-mix(in srgb, var(--hero-grad-2) 90%, var(--hero-grad-3)));
  box-shadow: 0 12px 20px color-mix(in srgb, var(--theme-accent) 40%, transparent);
  transform: translateY(-1px);
}

.send-btn-compact:active:not(:disabled) {
  transform: translateY(0) scale(0.97);
}

.send-btn-compact:disabled {
  opacity: 0.4;
  cursor: default;
}

.send-btn-compact svg {
  width: 14px;
  height: 14px;
}

.stop-btn-compact {
  background: #EF4444;
  box-shadow: 0 10px 18px color-mix(in srgb, #ef4444 35%, transparent);
}

.stop-icon-small {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 1px;
}

/* Note Selector Dropdown (Even smaller) */
.note-selector-dropdown {
  position: absolute;
  bottom: 42px;
  left: 0;
  width: 220px;
  max-height: 200px;
  background: linear-gradient(160deg, color-mix(in srgb, var(--theme-surface) 94%, white 6%), color-mix(in srgb, var(--theme-bg-secondary) 90%, transparent));
  border: 1px solid color-mix(in srgb, var(--theme-border) 86%, rgba(255, 255, 255, 0.26));
  border-radius: 14px;
  box-shadow: 0 20px 40px color-mix(in srgb, #000 18%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.44);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 120;
}

.selector-header {
  padding: 8px 10px;
  font-size: 10px;
  font-weight: 700;
  color: var(--theme-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--theme-border);
}

.selector-list {
  flex: 1;
  overflow-y: auto;
  padding: 3px;
}

.selector-item {
  padding: 8px 9px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.selector-item:hover {
  background: var(--theme-accent-light);
}

.item-icon {
  width: 13px;
  height: 13px;
  color: var(--theme-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.item-icon svg {
  width: 100%;
  height: 100%;
}
.item-title {
  font-size: 12px;
  color: var(--theme-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selector-empty {
  padding: 12px;
  text-align: center;
  color: var(--theme-text-secondary);
  font-size: 11px;
}

/* Context Bar (Mini Pills) */
.agent-chat__context-bar {
  padding: 6px 12px 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.agent-chat__context-bar + .agent-chat__context-bar {
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 4px;
  justify-content: flex-end;
}

.agent-chat__context-left,
.agent-chat__context-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.context-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1.2;
  border: 1px solid color-mix(in srgb, var(--theme-border) 72%, rgba(255, 255, 255, 0.18));
  background: color-mix(in srgb, var(--theme-surface) 68%, transparent);
  color: var(--theme-text-secondary);
  max-width: 220px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.mentioned-pill {
  background: rgba(217, 125, 84, 0.08);
  color: var(--theme-accent);
}

.approval-mode-pill {
  margin-left: auto;
}

.pill-text-btn {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.pill-text-btn:disabled {
  cursor: default;
  opacity: 0.6;
}

.inspecting-pill.inactive {
  opacity: 0.5;
  text-decoration: line-through;
  filter: grayscale(1);
}

.pill-toggle-btn {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  transition: transform 0.2s;
}

.pill-toggle-btn:hover {
  transform: scale(1.1);
}

.eye-svg, .pill-svg {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

.pill-toggle-btn {
  display: flex;
  align-items: center;
}

.pill-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pill-clear {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 10px;
  cursor: pointer;
  opacity: 0.5;
}

.pill-clear:hover { opacity: 1; }

.agent-approval-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--theme-text-secondary);
  margin: 0 12px 8px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 46%, rgba(255, 255, 255, 0.12));
  border-radius: 12px;
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 56%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 58%, transparent));
  flex-wrap: wrap;
  box-shadow: 0 10px 22px color-mix(in srgb, #000 10%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.agent-approval-bar,
.agent-task-card,
.agent-execution-panel {
  transition: border-color 180ms ease, box-shadow 220ms ease, background 180ms ease, transform 180ms ease;
}

.agent-approval-bar:hover,
.agent-task-card:hover,
.agent-execution-panel:hover {
  border-color: color-mix(in srgb, var(--theme-accent) 18%, var(--theme-border));
  box-shadow: 0 12px 24px color-mix(in srgb, #000 14%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.agent-approval-bar__label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-approval-btn {
  border: 1px solid color-mix(in srgb, var(--theme-border) 70%, rgba(255, 255, 255, 0.12));
  background: color-mix(in srgb, var(--theme-surface) 78%, transparent);
  color: var(--theme-text);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.16s ease, border-color 0.16s ease, transform 0.12s ease, box-shadow 0.16s ease;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.agent-approval-btn:hover:not(:disabled) {
  background: var(--theme-hover);
  box-shadow: 0 8px 14px color-mix(in srgb, #000 10%, transparent);
}

.agent-approval-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.agent-approval-btn--accept {
  border-color: rgba(16, 185, 129, 0.42);
  background: rgba(16, 185, 129, 0.08);
}

.agent-approval-btn--reject {
  border-color: rgba(239, 68, 68, 0.42);
  background: rgba(239, 68, 68, 0.08);
}

.agent-approval-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.agent-approval-preview {
  border: 1px solid color-mix(in srgb, var(--theme-border) 72%, rgba(255, 255, 255, 0.16));
  margin: 0 12px 8px;
  padding: 10px;
  border-radius: 14px;
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 72%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 68%, transparent));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.agent-task-card {
  margin: 0 12px 8px;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 44%, rgba(255, 255, 255, 0.12));
  border-radius: 12px;
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 52%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 56%, transparent));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.agent-task-card__title {
  font-size: 12px;
  font-weight: 650;
  color: var(--theme-text);
  margin-bottom: 8px;
}

.agent-task-card__row {
  display: grid;
  grid-template-columns: 78px 1fr;
  gap: 6px;
  font-size: 12px;
  color: var(--theme-text-secondary);
  line-height: 1.45;
}

.agent-task-card__row + .agent-task-card__row {
  margin-top: 3px;
}

.agent-execution-panel {
  margin: 0 12px 8px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 44%, rgba(255, 255, 255, 0.12));
  border-radius: 12px;
  background: linear-gradient(165deg, color-mix(in srgb, var(--theme-surface) 52%, transparent), color-mix(in srgb, var(--theme-bg-secondary) 56%, transparent));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.agent-execution-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--theme-border) 56%, transparent);
}

.agent-execution-panel__title {
  font-size: 12px;
  font-weight: 650;
  color: var(--theme-text);
}

.agent-execution-list {
  max-height: 132px;
  overflow: auto;
}

.agent-execution-item {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: var(--theme-text-secondary);
  padding: 7px 10px;
  border-top: 1px solid color-mix(in srgb, var(--theme-border) 70%, transparent);
  transition: background 140ms ease, color 140ms ease;
}

.agent-execution-item:first-child {
  border-top: none;
}

.agent-execution-item__status {
  font-weight: 600;
}

.agent-execution-item__title {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.agent-execution-item__time {
  opacity: 0.8;
}

.agent-execution-item--running .agent-execution-item__status {
  color: #f59e0b;
}

.agent-execution-item--completed .agent-execution-item__status {
  color: #10b981;
}

.agent-execution-item--error .agent-execution-item__status {
  color: #ef4444;
}

.agent-execution-item:hover {
  background: color-mix(in srgb, var(--theme-bg-hover) 72%, transparent);
}

/* Panel transitions: subtle material lift/fade */
.panel-elevate-enter-active,
.panel-elevate-leave-active {
  transition: opacity 180ms ease, transform 200ms cubic-bezier(0.22, 0.68, 0.2, 1);
}

.panel-elevate-enter-from,
.panel-elevate-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.panel-elevate-enter-to,
.panel-elevate-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* Execution record list motion */
.record-item-enter-active,
.record-item-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.record-item-enter-from,
.record-item-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.record-item-move {
  transition: transform 180ms ease;
}

@media (prefers-reduced-motion: reduce) {
  .panel-elevate-enter-active,
  .panel-elevate-leave-active,
  .record-item-enter-active,
  .record-item-leave-active,
  .record-item-move {
    transition: none;
  }
}

.agent-approval-preview__summary {
  font-size: 12px;
  color: var(--theme-text-secondary);
  margin-bottom: 8px;
}

.agent-approval-preview__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.agent-approval-diff {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 220px;
  overflow: auto;
}

.agent-diff-block {
  border: 1px solid var(--theme-border);
  border-radius: 6px;
  background: var(--theme-bg-solid);
  padding: 6px;
}

.agent-diff-block--added {
  border-color: rgba(16, 185, 129, 0.45);
}

.agent-diff-block--removed {
  border-color: rgba(239, 68, 68, 0.45);
}

.agent-diff-block--modified {
  border-color: rgba(245, 158, 11, 0.45);
}

.agent-diff-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 4px;
}

.agent-diff-block__label {
  font-size: 11px;
  color: var(--theme-text);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-diff-block__kind {
  font-size: 10px;
  color: var(--theme-text-secondary);
  text-transform: capitalize;
}

.agent-diff-lines {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-diff-line {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 6px;
  font-size: 11px;
  line-height: 1.35;
  border-radius: 4px;
  padding: 1px 4px;
}

.agent-diff-line--add {
  background: rgba(16, 185, 129, 0.12);
}

.agent-diff-line--del {
  background: rgba(239, 68, 68, 0.12);
}

.agent-diff-sign {
  color: var(--theme-text-secondary);
  text-align: center;
}

.agent-diff-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.agent-approval-preview__title {
  font-size: 12px;
  color: var(--theme-text-secondary);
}

@media (max-width: 880px) {
  .agent-chat__header {
    padding: 10px 11px;
  }
  .agent-chat__title {
    font-size: 15px;
  }
  .header-btn {
    width: 28px;
    height: 28px;
  }
  .agent-chat__messages {
    padding: 14px 12px;
  }
  .context-pill {
    max-width: 100%;
  }
}

/* Shallow Glass override */
.shallow-glass {
  backdrop-filter: blur(4px);
  background: var(--theme-bg-solid) !important;
}

/* Custom Scrollbar */
.agent-chat__messages::-webkit-scrollbar { width: 4px; }
.agent-chat__messages::-webkit-scrollbar-track { background: transparent; }
.agent-chat__messages::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb, rgba(0,0,0,0.1)); border-radius: 4px; }

/* Markdown Styles Override */
/* Default (Small) Chat Headers */
:deep(.message__text h1) { font-size: 1.2em; margin: 12px 0 6px; }
:deep(.message__text h2) { font-size: 1.1em; margin: 10px 0 5px; }
:deep(.message__text h3) { font-size: 1.05em; margin: 8px 0 4px; }

:deep(.message__text h1), :deep(.message__text h2), :deep(.message__text h3) {
  font-weight: 600;
  line-height: 1.3;
  color: var(--theme-text);
}

/* Maximized Chat Headers */
.maximized :deep(.message__text h1) { font-size: 1.5em; margin: 18px 0 10px; }
.maximized :deep(.message__text h2) { font-size: 1.3em; margin: 16px 0 8px; }
.maximized :deep(.message__text h3) { font-size: 1.2em; margin: 14px 0 6px; }

@keyframes messageSlide {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
:deep(.message__text ul), :deep(.message__text ol) {
  padding-left: 28px; /* High enough to prevent overlap/cutoff */
  margin: 8px 0;
}
:deep(.message__text li) {
  margin-bottom: 4px;
}
:deep(.message__text li::marker) {
  color: var(--theme-accent);
  font-weight: 600;
}
:deep(.message__text pre) { 
  background: var(--theme-code-bg); 
  border-radius: 8px; 
  padding: 12px; 
  margin: 8px 0; 
  overflow-x: auto; /* Internal scroll ONLY */
  max-width: 100%;
}
:deep(.math-block) {
  margin: 12px 0;
  padding: 12px;
  background: var(--theme-input-bg);
  border-radius: 8px;
  overflow-x: auto;
  text-align: center;
}
:deep(.math-inline) {
  padding: 0 4px;
}
:deep(.math-error) {
  color: #EF4444;
  font-family: monospace;
  background: #FEF2F2;
  padding: 2px 4px;
  border-radius: 4px;
}
:deep(.message__text table) {
  display: table; /* Reset to standard table behavior */
  width: max-content;
  min-width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  background: var(--theme-bg-solid);
  border-radius: 8px;
  border: 1px solid var(--theme-border);
  overflow: hidden; /* For radius */
}

/* Wrapping table in a container for horizontal scroll without breaking table layout */
.message__text {
  overflow-x: auto;
}

:deep(.message__text th), :deep(.message__text td) {
  border: 1px solid var(--theme-border);
  padding: 10px 16px;
  text-align: left;
  min-width: 80px;
  white-space: normal;
  word-break: normal;
  line-height: 1.5;
}

:deep(.message__text th) {
  background: var(--theme-accent-light);
  font-weight: 600;
  white-space: nowrap; 
  color: var(--theme-accent);
}

/* Sub-scrollbar for the container */
.message__text::-webkit-scrollbar { height: 4px; }
.message__text::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb, rgba(0,0,0,0.1)); border-radius: 4px; }
:deep(.message__text hr) { border: none; border-top: 1px solid var(--theme-border); margin: 16px 0; }

/* Session History Panel */
.session-history-panel {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--theme-bg-solid);
  z-index: 100;
  display: flex;
  flex-direction: column;
  border-radius: 0 0 16px 16px;
}

.session-history__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--theme-border);
  font-weight: 500;
  color: var(--theme-text);
}

.session-history__header .close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--theme-text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
}

.session-history__header .close-btn:hover {
  background: var(--theme-hover);
}

.session-history__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-history__empty {
  text-align: center;
  color: var(--theme-text-secondary);
  padding: 40px 20px;
  font-size: 13px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 4px;
}

.session-item:hover {
  background: var(--theme-hover);
}

.session-item--active {
  background: var(--theme-accent-light, rgba(var(--accent-rgb), 0.1));
}

.session-item--pinned {
  border-left: 2px solid var(--theme-accent);
}

.session-item__preview {
  flex: 1;
  font-size: 13px;
  color: var(--theme-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pin-indicator {
  color: var(--theme-accent);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pin-indicator svg {
  width: 12px;
  height: 12px;
}

.session-item__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.session-item:hover .session-item__actions {
  opacity: 1;
}

.session-item__btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--theme-text-secondary);
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.session-item__btn:hover {
  background: var(--theme-bg-secondary);
  color: var(--theme-text);
}

.session-item__btn--danger:hover {
  color: var(--color-danger, #ef4444);
}

.session-item__btn svg {
  width: 14px;
  height: 14px;
}

.session-rename-input {
  flex: 1;
  background: var(--theme-bg);
  border: 1px solid var(--theme-accent);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  color: var(--theme-text);
  outline: none;
}

/* Slide Panel Transition */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* ===== Shadcn-like Chat Refinement (UI only, no logic changes) ===== */
.agent-chat {
  --chat-surface: color-mix(in srgb, var(--theme-surface) 94%, #ffffff 6%);
  --chat-surface-soft: color-mix(in srgb, var(--theme-bg-secondary) 82%, #ffffff 18%);
  --chat-border: color-mix(in srgb, var(--theme-border) 84%, #d7dbe2 16%);
  --chat-ring: color-mix(in srgb, var(--theme-accent) 22%, transparent);
  --chat-text-soft: color-mix(in srgb, var(--theme-text-secondary) 86%, transparent);
  background: var(--chat-surface);
  border: 1px solid var(--chat-border);
  box-shadow:
    0 14px 30px color-mix(in srgb, #0f172a 10%, transparent),
    0 2px 10px color-mix(in srgb, #0f172a 7%, transparent);
}

.agent-chat::before,
.agent-chat::after {
  display: none;
}

.agent-chat__header {
  background: color-mix(in srgb, var(--chat-surface) 96%, white 4%);
  border-bottom: 1px solid var(--chat-border);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.agent-chat__title {
  font-size: 15px;
  font-weight: 620;
  letter-spacing: -0.01em;
}

.header-btn {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 78%, transparent);
  box-shadow: none;
  color: var(--chat-text-soft);
}

.header-btn:hover {
  background: color-mix(in srgb, var(--theme-bg-hover) 72%, var(--chat-surface) 28%);
  border-color: color-mix(in srgb, var(--theme-accent) 26%, var(--chat-border));
  box-shadow: 0 0 0 2px var(--chat-ring);
  color: var(--theme-text);
  transform: none;
}

.agent-chat__messages {
  padding: 18px 14px 14px;
  gap: 14px;
}

.message--assistant .message {
  padding-right: 4px;
}

.message--user .message {
  border-radius: 14px;
  border-bottom-right-radius: 6px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--theme-accent-light) 40%, var(--chat-surface));
  box-shadow: 0 1px 2px color-mix(in srgb, #0f172a 8%, transparent);
  padding: 8px 12px;
}

.message__text {
  line-height: 1.55;
  color: color-mix(in srgb, var(--theme-text) 96%, transparent);
}

.tool-part {
  border-radius: 12px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 70%, var(--chat-surface) 30%);
  box-shadow: 0 1px 2px color-mix(in srgb, #0f172a 7%, transparent);
  padding: 8px 10px;
}

.tool-part--running {
  border-color: color-mix(in srgb, var(--theme-accent) 22%, var(--chat-border));
  background: color-mix(in srgb, var(--theme-accent-light) 34%, var(--chat-surface) 66%);
}

.tool-part__icon-wrap {
  background: color-mix(in srgb, var(--chat-surface) 86%, white 14%);
  border: 1px solid var(--chat-border);
  box-shadow: none;
}

.tool-part__output {
  border-radius: 8px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 86%, var(--chat-surface-soft) 14%);
}

.status-update {
  margin-left: 0;
  border-radius: 10px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 72%, var(--chat-surface) 28%);
  box-shadow: none;
  color: var(--chat-text-soft);
  animation: none;
}

.agent-chat__footer {
  background: color-mix(in srgb, var(--chat-surface) 96%, white 4%);
  border-top: 1px solid var(--chat-border);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.chat-input-unified-box {
  border-radius: 12px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 96%, white 4%);
  box-shadow: 0 1px 2px color-mix(in srgb, #0f172a 8%, transparent);
}

.chat-input-unified-box::before {
  display: none;
}

.chat-input-unified-box:focus-within {
  border-color: color-mix(in srgb, var(--theme-accent) 30%, var(--chat-border));
  box-shadow: 0 0 0 3px var(--chat-ring);
  transform: none;
}

.menu-trigger-btn,
.send-btn-compact,
.stop-btn-compact {
  border-radius: 10px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 80%, var(--chat-surface) 20%);
  box-shadow: none;
}

.agent-task-card,
.agent-execution-panel,
.agent-approval-preview {
  border-radius: 12px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 64%, var(--chat-surface) 36%);
  box-shadow: 0 1px 2px color-mix(in srgb, #0f172a 7%, transparent);
}

.agent-task-card:hover,
.agent-execution-panel:hover {
  box-shadow: 0 3px 10px color-mix(in srgb, #0f172a 8%, transparent);
  transform: none;
}

.agent-execution-item {
  border-bottom: 1px solid color-mix(in srgb, var(--chat-border) 80%, transparent);
}

/* ===== C mode: full shadcn-style revamp (light + dark) ===== */
.agent-chat {
  border-radius: 14px;
}

.agent-chat__title > span:last-child,
.tool-part__name--running,
.agent-chat__welcome h3 {
  background: none !important;
  color: var(--theme-text) !important;
  animation: none !important;
}

.agent-chat__avatar {
  color: var(--theme-text-secondary);
  filter: none;
}

.agent-chat__welcome p,
.hero-card__desc,
.hero-list__items,
.suggestion-chip,
.agent-execution-item__time,
.tool-part__output,
.status-update {
  color: var(--chat-text-soft);
}

.agent-chat__hero-cards,
.agent-chat__hero-list,
.agent-chat__suggestions {
  max-width: 560px;
}

.hero-card {
  border-radius: 12px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 94%, white 6%);
  min-height: 96px;
}

.hero-card:hover {
  background: color-mix(in srgb, var(--chat-surface-soft) 80%, var(--chat-surface) 20%);
  box-shadow: 0 2px 10px color-mix(in srgb, #0f172a 8%, transparent);
  transform: translateY(-1px);
}

.hero-card__title {
  color: var(--theme-text);
  font-size: 16px;
  font-weight: 620;
}

.hero-action-strip {
  border: 1px dashed color-mix(in srgb, var(--chat-border) 70%, transparent);
  border-radius: 12px;
  padding: 10px;
  background: color-mix(in srgb, var(--chat-surface-soft) 54%, transparent);
}

.hero-action-strip__label {
  color: var(--chat-text-soft);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.hero-action-btn {
  border-radius: 8px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 98%, transparent);
  color: var(--theme-text);
  font-size: 11px;
}

.hero-action-btn:hover {
  background: color-mix(in srgb, var(--chat-surface-soft) 78%, transparent);
  transform: translateY(-1px);
}

.suggestion-chip {
  border-radius: 10px !important;
  min-height: 34px;
  background: color-mix(in srgb, var(--chat-surface) 98%, transparent);
  border-color: var(--chat-border);
}

.suggestion-chip:hover {
  background: color-mix(in srgb, var(--chat-surface-soft) 76%, transparent);
  border-color: color-mix(in srgb, var(--theme-accent) 18%, var(--chat-border));
}

.message--assistant .message {
  padding: 0 2px;
}

.message--user .message {
  background: color-mix(in srgb, var(--chat-surface-soft) 80%, var(--theme-accent-light) 20%);
}

.tool-part {
  grid-template-columns: auto 1fr;
  gap: 10px;
  border-radius: 10px;
}

.tool-part__icon-wrap {
  width: 22px;
  height: 22px;
}

.tool-part__name {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.tool-part__pending {
  border-radius: 999px;
  font-size: 10px;
  border-color: color-mix(in srgb, #f59e0b 35%, var(--chat-border));
  background: color-mix(in srgb, #f59e0b 14%, transparent);
  color: color-mix(in srgb, #b45309 84%, var(--theme-text));
}

.tool-part__spinner {
  width: 11px;
  height: 11px;
}

.status-update {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 10.5px;
  letter-spacing: 0.01em;
}

.agent-chat__context-bar {
  padding: 0 14px 8px;
}

.context-pill {
  border-radius: 999px;
  border-color: var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 76%, var(--chat-surface) 24%);
  box-shadow: none;
}

.agent-approval-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  margin: 0 14px 10px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface-soft) 74%, var(--chat-surface) 26%);
}

.agent-approval-bar > *:not(.agent-approval-bar__label) {
  justify-self: end;
  margin-left: 6px;
}

.agent-approval-bar__label {
  font-size: 11px;
  color: var(--theme-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-approval-btn {
  border-radius: 8px;
  border: 1px solid var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 96%, transparent);
  font-size: 11px;
  height: 30px;
  padding: 0 10px;
}

.agent-approval-btn:hover:not(:disabled) {
  box-shadow: 0 0 0 2px var(--chat-ring);
}

.agent-approval-btn--accept {
  border-color: color-mix(in srgb, #10b981 32%, var(--chat-border));
  color: color-mix(in srgb, #047857 84%, var(--theme-text));
}

.agent-approval-btn--reject {
  border-color: color-mix(in srgb, #ef4444 30%, var(--chat-border));
  color: color-mix(in srgb, #b91c1c 84%, var(--theme-text));
}

.agent-ops-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  padding: 0 14px 10px;
}

.agent-task-card,
.agent-execution-panel {
  margin: 0;
}

.agent-task-card__title,
.agent-execution-panel__title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--chat-text-soft);
}

.agent-task-card__row {
  grid-template-columns: 64px minmax(0, 1fr);
  font-size: 11px;
}

.agent-execution-list {
  max-height: 180px;
  overflow: auto;
}

.agent-execution-item {
  grid-template-columns: auto 1fr auto;
  gap: 8px;
  font-size: 11px;
  min-height: 34px;
}

.agent-execution-item__status {
  border-radius: 999px;
  padding: 2px 8px;
  background: color-mix(in srgb, var(--chat-surface) 88%, var(--chat-surface-soft) 12%);
  border: 1px solid var(--chat-border);
  min-width: 58px;
  text-align: center;
}

.agent-execution-item--completed .agent-execution-item__status {
  color: color-mix(in srgb, #047857 84%, var(--theme-text));
  border-color: color-mix(in srgb, #10b981 30%, var(--chat-border));
  background: color-mix(in srgb, #10b981 12%, transparent);
}

.agent-execution-item--running .agent-execution-item__status {
  color: color-mix(in srgb, #1d4ed8 84%, var(--theme-text));
  border-color: color-mix(in srgb, #3b82f6 30%, var(--chat-border));
  background: color-mix(in srgb, #3b82f6 12%, transparent);
}

.agent-chat__footer {
  padding: 10px 12px 12px;
}

.chat-input-unified-box {
  border-radius: 14px;
  padding: 10px;
  min-height: 54px;
}

.menu-trigger-btn,
.send-btn-compact,
.stop-btn-compact {
  width: 34px;
  height: 34px;
}

.send-btn-compact {
  border-color: color-mix(in srgb, var(--theme-accent) 26%, var(--chat-border));
}

.input-menu-popup {
  border-radius: 12px;
  border-color: var(--chat-border);
  background: color-mix(in srgb, var(--chat-surface) 95%, white 5%);
  box-shadow: 0 12px 30px color-mix(in srgb, #0f172a 16%, transparent);
}

.input-menu-item {
  border-radius: 8px;
  font-size: 12px;
}

@media (min-width: 1180px) {
  .agent-ops-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 780px) {
  .agent-chat {
    border-radius: 10px;
  }
  .agent-chat__header,
  .agent-chat__messages,
  .agent-chat__footer {
    padding-left: 10px;
    padding-right: 10px;
  }
  .agent-approval-bar {
    margin-left: 10px;
    margin-right: 10px;
    grid-template-columns: 1fr;
  }
  .agent-approval-bar > *:not(.agent-approval-bar__label) {
    justify-self: start;
    margin-left: 0;
  }
  .agent-ops-grid {
    padding-left: 10px;
    padding-right: 10px;
  }
}

[data-theme="dark"] .agent-chat {
  --chat-surface: color-mix(in srgb, var(--theme-surface) 88%, #020617 12%);
  --chat-surface-soft: color-mix(in srgb, var(--theme-bg-secondary) 76%, #020617 24%);
  --chat-border: color-mix(in srgb, var(--theme-border) 70%, #334155 30%);
  --chat-text-soft: color-mix(in srgb, var(--theme-text-secondary) 84%, transparent);
  box-shadow:
    0 18px 40px color-mix(in srgb, #000 35%, transparent),
    0 2px 12px color-mix(in srgb, #000 24%, transparent);
}

[data-theme="dark"] .header-btn,
[data-theme="dark"] .menu-trigger-btn,
[data-theme="dark"] .send-btn-compact,
[data-theme="dark"] .stop-btn-compact,
[data-theme="dark"] .agent-approval-btn {
  background: color-mix(in srgb, var(--chat-surface-soft) 80%, #0b1220 20%);
}

[data-theme="dark"] .message--user .message,
[data-theme="dark"] .tool-part,
[data-theme="dark"] .agent-task-card,
[data-theme="dark"] .agent-execution-panel,
[data-theme="dark"] .agent-approval-preview,
[data-theme="dark"] .input-menu-popup {
  background: color-mix(in srgb, var(--chat-surface-soft) 74%, #0b1220 26%);
}

/* Composer: compact shadcn-like layout */
.agent-chat__footer {
  padding: 8px 10px 9px;
}

.chat-input-unified-box {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  border-radius: 16px;
  padding: 10px 10px 8px;
  min-height: 94px;
}

.context-attach-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 34px;
  padding: 0 12px;
  border-radius: 12px;
  border: none;
  background: color-mix(in srgb, var(--chat-surface-soft) 90%, transparent);
  color: var(--theme-text);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 180ms ease, transform 120ms ease, box-shadow 180ms ease;
}

.context-attach-btn:hover {
  background: color-mix(in srgb, var(--chat-surface-soft) 78%, var(--theme-bg-secondary) 22%);
  box-shadow: 0 3px 10px color-mix(in srgb, #000 10%, transparent);
  transform: translateY(-1px);
}

.context-attach-btn__icon {
  color: var(--chat-text-soft);
  font-weight: 700;
  font-size: 15px;
  line-height: 1;
}

.context-attach-btn__text {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-input-unified-box textarea {
  flex: 1;
  min-height: 40px;
  max-height: 120px;
  padding: 2px 0;
  font-size: 14px;
  line-height: 1.4;
}

.chat-input-unified-box textarea::placeholder {
  font-size: 13px;
  opacity: 0.7;
}

.chat-input-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.chat-input-bottom__left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.menu-trigger-btn {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: none;
  box-shadow: none;
}

.composer-mode-btn {
  height: 34px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--theme-text);
  font-size: 13px;
  font-weight: 500;
  padding: 0 4px;
  cursor: pointer;
}

.composer-source-pill {
  color: var(--chat-text-soft);
  font-size: 13px;
  white-space: nowrap;
}

.send-btn-compact,
.stop-btn-compact {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: none;
  box-shadow: none;
}

.send-btn-compact {
  background: #0f0f10;
  color: #ffffff;
  border: none;
}

.send-btn-compact:hover:not(:disabled) {
  background: #1d1d20;
  border-color: #1d1d20;
  box-shadow: 0 6px 16px rgba(15, 15, 16, 0.25);
}

.send-btn-compact:disabled {
  opacity: 0.35;
}

.send-btn-compact svg {
  width: 16px;
  height: 16px;
}

.input-menu-popup {
  bottom: 42px;
  min-width: 230px;
  border-radius: 14px;
  padding: 8px;
}

.menu-item {
  padding: 9px 10px;
  font-size: 14px;
  border-radius: 10px;
  gap: 9px;
  border: none;
}

.menu-icon {
  width: 14px;
  height: 14px;
}

.agent-ops-grid {
  margin-bottom: 6px;
}

@media (max-width: 780px) {
  .chat-input-unified-box {
    min-height: 84px;
    gap: 7px;
  }

  .context-attach-btn__text {
    max-width: 180px;
  }

  .chat-input-unified-box textarea {
    min-height: 34px;
    font-size: 13px;
  }

  .chat-input-unified-box textarea::placeholder {
    font-size: 12px;
  }

  .composer-source-pill {
    display: none;
  }
}

[data-theme="dark"] .send-btn-compact {
  background: #f8fafc;
  color: #0f172a;
  border-color: #f8fafc;
}

[data-theme="dark"] .send-btn-compact:hover:not(:disabled) {
  background: #ffffff;
  border-color: #ffffff;
}

/* ===== Right-reference full chat redesign override ===== */
.agent-chat {
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 70%, transparent);
  background: color-mix(in srgb, var(--theme-surface) 97%, transparent);
  box-shadow: 0 10px 28px color-mix(in srgb, #000 10%, transparent);
}

.agent-chat__header {
  min-height: 52px;
  padding: 10px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--theme-border) 65%, transparent);
  background: transparent;
}

.agent-chat__title {
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.agent-chat__avatar {
  width: 14px;
  height: 14px;
  background: transparent;
  border: none;
  color: var(--theme-accent);
  opacity: 0.95;
}

.agent-chat__actions {
  gap: 2px;
}

.header-btn {
  width: 28px;
  height: 28px;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 8px;
  color: color-mix(in srgb, var(--theme-text) 72%, transparent);
}

.header-btn:hover {
  background: color-mix(in srgb, var(--theme-bg-secondary) 86%, transparent) !important;
  color: var(--theme-text);
}

.header-btn svg {
  width: 15px;
  height: 15px;
}

.agent-chat__status {
  margin-left: 4px;
}

.agent-chat__messages {
  padding: 10px 14px;
  gap: 10px;
}

.message-wrapper {
  margin-bottom: 8px;
}

.message {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.message--assistant .message__text {
  font-size: 14px;
  line-height: 1.58;
  color: color-mix(in srgb, var(--theme-text) 94%, transparent);
}

.message--user .message {
  display: inline-flex;
  background: color-mix(in srgb, var(--theme-surface-soft, var(--theme-bg-secondary)) 92%, transparent) !important;
  border: 1px solid color-mix(in srgb, var(--theme-border) 55%, transparent) !important;
  border-radius: 999px;
  padding: 8px 14px !important;
}

.message--user .message__text {
  font-size: 14px;
  line-height: 1.45;
}

.tool-part {
  margin-top: 8px;
  border: none;
  border-radius: 10px;
  padding: 8px 10px;
  background: color-mix(in srgb, var(--theme-bg-secondary) 92%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 45%, transparent);
}

.tool-part__name {
  font-size: 12.5px;
  font-weight: 620;
}

.tool-part__output {
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-text-secondary) 90%, transparent);
}

.agent-approval-bar {
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 8px !important;
  margin: 2px 14px 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border: none;
  background: color-mix(in srgb, var(--theme-bg-secondary) 90%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 45%, transparent);
}

.agent-approval-bar__label {
  display: block !important;
  font-size: 12.5px;
}

.agent-approval-bar__actions {
  display: flex !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 8px !important;
  overflow-x: auto;
}

.agent-approval-btn {
  flex: 0 0 auto !important;
  border: none !important;
  border-radius: 999px;
  background: color-mix(in srgb, var(--theme-bg-secondary) 78%, transparent);
  box-shadow: none !important;
  font-size: 12px;
  height: 28px;
  padding: 0 11px;
}

.agent-approval-btn--accept {
  background: color-mix(in srgb, #10b981 16%, var(--theme-bg-secondary));
  color: color-mix(in srgb, #065f46 82%, var(--theme-text));
}

.agent-approval-btn--reject {
  background: color-mix(in srgb, #ef4444 13%, var(--theme-bg-secondary));
  color: color-mix(in srgb, #7f1d1d 84%, var(--theme-text));
}

.agent-task-card,
.agent-execution-panel,
.agent-approval-preview {
  border: none;
  border-radius: 10px;
  background: color-mix(in srgb, var(--theme-bg-secondary) 88%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 42%, transparent);
}

.agent-task-card__title,
.agent-execution-panel__title {
  font-size: 12.5px;
  font-weight: 650;
}

.agent-task-card__row,
.agent-execution-item {
  font-size: 12px;
}

/* Composer */
.agent-chat__footer {
  padding: 6px 10px 8px !important;
  border-top: 1px solid color-mix(in srgb, var(--theme-border) 58%, transparent) !important;
}

.chat-input-unified-box {
  gap: 6px !important;
  border-radius: 14px !important;
  padding: 8px 10px 6px !important;
  min-height: 0 !important;
  height: auto !important;
  border: none !important;
  background: color-mix(in srgb, var(--theme-bg-secondary) 90%, transparent) !important;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 42%, transparent) !important;
}

.chat-input-unified-box::before {
  display: none;
}

.context-attach-btn {
  height: 30px !important;
  padding: 0 10px !important;
  border-radius: 11px !important;
  border: none !important;
  background: color-mix(in srgb, var(--theme-surface) 88%, var(--theme-bg-secondary)) !important;
  font-size: 12px !important;
}

.context-attach-btn__icon {
  font-size: 14px !important;
}

.chat-input-unified-box textarea {
  flex: none !important;
  min-height: 28px !important;
  max-height: 220px !important;
  font-size: 12px !important;
  line-height: 1.38 !important;
  overflow-y: hidden;
}

.chat-input-unified-box textarea::placeholder {
  font-size: 12px !important;
}

.chat-input-bottom {
  gap: 6px !important;
}

.chat-input-bottom__left {
  gap: 6px !important;
}

.menu-trigger-btn,
.send-btn-compact,
.stop-btn-compact {
  border: none !important;
  box-shadow: none !important;
}

.menu-trigger-btn {
  width: 30px !important;
  height: 30px !important;
  background: color-mix(in srgb, var(--theme-surface) 88%, var(--theme-bg-secondary)) !important;
}

.composer-mode-btn,
.composer-source-pill {
  font-size: 12px !important;
}

.composer-model-wrapper {
  position: relative;
}

.composer-model-btn {
  height: 30px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--theme-text);
  font-size: 12px;
  font-weight: 520;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.composer-model-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.composer-model-btn__label {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-model-btn__caret {
  font-size: 10px;
  color: var(--chat-text-soft);
}

.composer-model-menu {
  left: 0;
  right: auto;
  min-width: 250px !important;
}

.menu-item--model {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.menu-item--disabled {
  opacity: 0.72;
  cursor: default;
  pointer-events: none;
}

.model-option__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.model-option__name {
  font-size: 12px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-option__provider {
  font-size: 10.5px;
  color: var(--chat-text-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-option__check {
  font-size: 12px;
  color: color-mix(in srgb, #10b981 72%, var(--theme-text));
  flex-shrink: 0;
}

.menu-divider {
  margin: 4px 2px;
  height: 1px;
  background: color-mix(in srgb, var(--theme-border) 68%, transparent);
}

.send-btn-compact,
.stop-btn-compact {
  width: 32px !important;
  height: 32px !important;
}

.input-menu-popup {
  min-width: 220px !important;
  padding: 6px !important;
  border-radius: 12px !important;
  border: none !important;
  box-shadow:
    0 14px 34px color-mix(in srgb, #000 14%, transparent),
    inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 46%, transparent) !important;
}

.menu-item {
  border: none !important;
  font-size: 12px !important;
  border-radius: 10px !important;
}

@media (max-width: 780px) {
  .agent-chat__header {
    padding: 8px 10px;
  }

  .agent-chat__messages {
    padding: 8px 10px;
  }

  .agent-chat__footer {
    padding: 6px 8px !important;
  }

  .chat-input-unified-box {
    min-height: 0 !important;
    padding: 7px 8px 6px !important;
  }

  .context-attach-btn {
    height: 28px !important;
    font-size: 11px !important;
  }

  .chat-input-unified-box textarea {
    min-height: 24px !important;
    font-size: 11.5px !important;
  }

  .composer-model-btn__label {
    max-width: 96px;
  }

  .composer-source-pill {
    display: none;
  }
}

[data-theme="dark"] .agent-chat {
  background: color-mix(in srgb, #0f172a 70%, var(--theme-surface) 30%);
  border-color: color-mix(in srgb, #334155 56%, transparent);
  box-shadow: 0 16px 38px color-mix(in srgb, #000 42%, transparent);
}

[data-theme="dark"] .chat-input-unified-box,
[data-theme="dark"] .tool-part,
[data-theme="dark"] .agent-approval-bar,
[data-theme="dark"] .agent-task-card,
[data-theme="dark"] .agent-execution-panel,
[data-theme="dark"] .agent-approval-preview,
[data-theme="dark"] .input-menu-popup {
  background: color-mix(in srgb, #0b1220 68%, var(--theme-bg-secondary) 32%);
}

/* Flat cleanup: remove irregular blotchy shadows from translucent layers */
.agent-chat,
.agent-chat__header,
.agent-chat__messages,
.agent-chat__footer {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  background-image: none !important;
}

.agent-chat::before,
.agent-chat::after {
  display: none !important;
  background: none !important;
  box-shadow: none !important;
}

.agent-chat {
  background: #fdfdfd !important;
  box-shadow: none !important;
}

.agent-chat__messages {
  background: #fdfdfd !important;
  box-shadow: none !important;
}

[data-theme="dark"] .agent-chat {
  background: #0b1220 !important;
  box-shadow: none !important;
}

[data-theme="dark"] .agent-chat__messages {
  background: #0b1220 !important;
  box-shadow: none !important;
}

/* Tool status row: text-first execution style */
.tool-part {
  grid-template-columns: 1fr !important;
  gap: 0 !important;
}

.tool-part__icon-wrap,
.tool-part__spinner {
  display: none !important;
}

/* Cyber execution gradient (blue-purple) for running state text */
.tool-part__name--running,
.status-update__text {
  background-image: linear-gradient(
    120deg,
    #59b0ff 0%,
    #7d87ff 35%,
    #9a6dff 62%,
    #c98dff 82%,
    #59b0ff 100%
  ) !important;
  background-size: 240% 240% !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  color: transparent !important;
  animation: heroGradientFlow 3.8s linear infinite !important;
  font-weight: 560 !important;
}

[data-theme="dark"] .tool-part__name--running,
[data-theme="dark"] .status-update__text {
  background-image: linear-gradient(
    120deg,
    #7bc6ff 0%,
    #93a0ff 34%,
    #b28cff 62%,
    #dba6ff 84%,
    #7bc6ff 100%
  ) !important;
}

@media (prefers-reduced-motion: reduce) {
  .tool-part__name--running,
  .status-update__text {
    animation: none !important;
    background-size: 100% 100% !important;
  }
}

/* ===== Session history: shadcn-style refresh ===== */
.session-history-panel {
  top: 52px;
  background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
  border-top: 1px solid color-mix(in srgb, var(--theme-border) 56%, transparent);
  border-radius: 0;
}

.session-history__header {
  min-height: 40px;
  padding: 8px 12px;
  border-bottom: 1px solid color-mix(in srgb, var(--theme-border) 52%, transparent);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: color-mix(in srgb, var(--theme-text-secondary) 88%, transparent);
}

.session-history__header .close-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: color-mix(in srgb, var(--theme-text-secondary) 86%, transparent);
  font-size: 16px;
  line-height: 1;
}

.session-history__header .close-btn:hover {
  background: color-mix(in srgb, var(--theme-bg-secondary) 85%, transparent);
  color: var(--theme-text);
}

.session-history__list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-history__empty {
  border: 1px dashed color-mix(in srgb, var(--theme-border) 65%, transparent);
  border-radius: 10px;
  padding: 18px 12px;
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-text-secondary) 84%, transparent);
}

.session-item {
  min-height: 34px;
  margin: 0;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  padding: 7px 8px;
}

.session-item:hover {
  border-color: color-mix(in srgb, var(--theme-border) 60%, transparent);
  background: color-mix(in srgb, var(--theme-bg-secondary) 78%, transparent);
}

.session-item--active {
  border-color: color-mix(in srgb, var(--theme-accent) 36%, var(--theme-border));
  background: color-mix(in srgb, var(--theme-accent) 12%, var(--theme-bg-secondary));
}

.session-item--pinned {
  border-left: 1px solid color-mix(in srgb, var(--theme-accent) 34%, var(--theme-border));
}

.session-item__preview {
  font-size: 12.5px;
  line-height: 1.3;
  color: color-mix(in srgb, var(--theme-text) 92%, transparent);
  gap: 6px;
}

.pin-indicator {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--theme-accent) 14%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: color-mix(in srgb, var(--theme-accent) 84%, transparent);
}

.pin-indicator svg {
  width: 9px;
  height: 9px;
}

.session-item__actions {
  gap: 4px;
}

.session-item__btn {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: color-mix(in srgb, var(--theme-text-secondary) 82%, transparent);
}

.session-item__btn:hover {
  background: color-mix(in srgb, var(--theme-bg-secondary) 85%, transparent);
  color: var(--theme-text);
}

.session-item__btn--danger:hover {
  background: color-mix(in srgb, #ef4444 11%, var(--theme-bg-secondary));
  color: #b91c1c;
}

.session-item__btn svg {
  width: 12px;
  height: 12px;
}

.session-rename-input {
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 34%, var(--theme-border));
  background: color-mix(in srgb, var(--theme-bg-secondary) 76%, var(--theme-surface) 24%);
  font-size: 12.5px;
  height: 28px;
  padding: 0 9px;
}

/* Ask/Agent + compact composer controls */
.agent-chat__empty-hint {
  margin-top: 4px;
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-text-secondary) 86%, transparent);
}

.chat-input-bottom__right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.composer-mode-btn--mode {
  padding: 0 10px !important;
  border-radius: 999px !important;
  border: 1px solid color-mix(in srgb, var(--theme-border) 60%, transparent) !important;
  background: color-mix(in srgb, var(--theme-surface) 84%, transparent) !important;
  font-weight: 600 !important;
  min-width: 62px;
  justify-content: center;
}

.composer-mode-btn--mode:hover {
  background: color-mix(in srgb, var(--theme-bg-secondary) 78%, transparent) !important;
}

.composer-review-btn {
  height: 24px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--chat-text-soft);
  font-size: 11px;
  font-weight: 520;
  padding: 0 4px;
  cursor: pointer;
  white-space: nowrap;
}

.composer-review-btn:hover {
  color: var(--theme-text);
}

@media (max-width: 780px) {
  .composer-mode-btn--mode {
    min-width: 56px;
    padding: 0 8px !important;
  }
  .composer-review-btn {
    font-size: 10.5px;
  }
}

</style>

