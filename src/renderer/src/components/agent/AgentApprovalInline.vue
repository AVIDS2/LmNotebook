<template>
  <div>
    <Transition name="panel-elevate">
      <div v-if="showCard" class="agent-approval-card agent-approval-card--inline">
        <div class="agent-approval-card__head">
          <span class="agent-approval-card__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="9"></circle>
              <path d="M12 7v6"></path>
              <path d="M12 16h.01"></path>
            </svg>
          </span>
          <div class="agent-approval-card__meta">
            <div class="agent-approval-card__title">{{ approvalCardTitle }}</div>
            <div class="agent-approval-card__target">{{ approvalCardTarget }}</div>
            <div class="agent-approval-card__scope">{{ approvalCardScope }}</div>
          </div>
          <button class="agent-approval-card__dismiss" :disabled="approvalBusy" @click="$emit('dismiss')">×</button>
        </div>
        <div class="agent-approval-card__foot">
          <span class="agent-approval-card__hint">{{ approvalCardHint }}</span>
          <div class="agent-approval-card__actions">
            <button
              v-if="!isExecutionAwaitingApproval && hasCurrentPendingApproval"
              class="agent-approval-btn"
              @click="$emit('toggle-preview')"
            >
              {{ showApprovalPreview ? hideChangesLabel : viewChangesLabel }}
            </button>
            <button class="agent-approval-btn agent-approval-btn--accept" :disabled="approvalBusy" @click="$emit('approve')">
              {{ allowOnceLabel }}
            </button>
            <button class="agent-approval-btn agent-approval-btn--reject" :disabled="approvalBusy" @click="$emit('dismiss')">
              {{ rejectLabel }}
            </button>
            <button class="agent-approval-btn" :disabled="approvalBusy" @click="$emit('enable-auto-accept')">
              {{ autoAllowLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <div v-if="showPreview" class="agent-approval-preview agent-approval-preview--inline">
      <div class="agent-approval-preview__summary">{{ currentApprovalSummary }}</div>
      <div class="agent-approval-preview__title-row">
        <div class="agent-approval-preview__title">{{ structuredDiffTitle }}</div>
        <button class="agent-approval-btn" @click="$emit('toggle-unchanged')">
          {{ showUnchangedDiff ? hideUnchangedLabel : showUnchangedLabel }}
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
            <div v-for="(line, idx) in block.lines" :key="`${block.id}-${idx}`" class="agent-diff-line" :class="`agent-diff-line--${line.op}`">
              <span class="agent-diff-sign">{{ line.op === 'add' ? '+' : line.op === 'del' ? '-' : ' ' }}</span>
              <span class="agent-diff-text">{{ line.text || ' ' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DiffBlockView } from './approvalDiff'

interface Props {
  showCard: boolean
  showPreview: boolean
  approvalBusy: boolean
  isExecutionAwaitingApproval: boolean
  hasCurrentPendingApproval: boolean
  showApprovalPreview: boolean
  showUnchangedDiff: boolean
  approvalCardTitle: string
  approvalCardTarget: string
  approvalCardScope: string
  approvalCardHint: string
  currentApprovalSummary: string
  visibleApprovalDiffBlocks: DiffBlockView[]
  structuredDiffTitle: string
  viewChangesLabel: string
  hideChangesLabel: string
  showUnchangedLabel: string
  hideUnchangedLabel: string
  allowOnceLabel: string
  rejectLabel: string
  autoAllowLabel: string
}

defineProps<Props>()

defineEmits<{
  (e: 'approve'): void
  (e: 'dismiss'): void
  (e: 'enable-auto-accept'): void
  (e: 'toggle-preview'): void
  (e: 'toggle-unchanged'): void
}>()
</script>

<style scoped lang="scss">
.panel-elevate-enter-active,
.panel-elevate-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.panel-elevate-enter-from,
.panel-elevate-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.agent-approval-card {
  margin: 8px 0 6px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--theme-border) 66%, transparent);
  background: color-mix(in srgb, var(--theme-bg-secondary) 92%, transparent);
  box-shadow: 0 4px 18px color-mix(in srgb, #000 7%, transparent),
    inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 36%, transparent);
  overflow: hidden;
}

.agent-approval-card--inline {
  max-width: 100%;
}

.agent-approval-card__head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: 10px;
  padding: 10px 12px;
}

.agent-approval-card__icon {
  display: inline-flex;
  width: 18px;
  height: 18px;
  margin-top: 1px;
  color: color-mix(in srgb, var(--theme-accent) 88%, transparent);
}

.agent-approval-card__icon svg {
  width: 18px;
  height: 18px;
}

.agent-approval-card__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.agent-approval-card__title {
  font-size: 13px;
  font-weight: 650;
  color: color-mix(in srgb, var(--theme-text) 98%, transparent);
}

.agent-approval-card__target,
.agent-approval-card__scope {
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-text-secondary) 90%, transparent);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-approval-card__dismiss {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: color-mix(in srgb, var(--theme-text-secondary) 80%, transparent);
  line-height: 1;
  font-size: 16px;
  cursor: pointer;
}

.agent-approval-card__dismiss:hover {
  background: color-mix(in srgb, var(--theme-bg-hover) 78%, transparent);
  color: var(--theme-text);
}

.agent-approval-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px 10px;
  border-top: 1px solid color-mix(in srgb, var(--theme-border) 55%, transparent);
}

.agent-approval-card__hint {
  font-size: 12px;
  color: color-mix(in srgb, var(--theme-text-secondary) 88%, transparent);
}

.agent-approval-card__actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.agent-approval-btn {
  flex: 0 0 auto !important;
  border: none !important;
  border-radius: 8px;
  background: color-mix(in srgb, var(--theme-bg-secondary) 78%, transparent);
  box-shadow: none !important;
  font-size: 12px;
  height: 30px;
  padding: 0 12px;
  font-weight: 560;
  cursor: pointer;
}

.agent-approval-btn--accept {
  background: color-mix(in srgb, #10b981 16%, var(--theme-bg-secondary));
  color: color-mix(in srgb, #065f46 82%, var(--theme-text));
}

.agent-approval-btn--reject {
  background: color-mix(in srgb, #ef4444 13%, var(--theme-bg-secondary));
  color: color-mix(in srgb, #7f1d1d 84%, var(--theme-text));
}

.agent-approval-preview--inline {
  margin: 8px 0 6px;
}

.agent-approval-preview {
  border: none;
  border-radius: 10px;
  background: color-mix(in srgb, var(--theme-bg-secondary) 88%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--theme-border) 42%, transparent);
  padding: 10px;
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

.agent-approval-preview__title {
  font-size: 12px;
  color: var(--theme-text-secondary);
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

@media (max-width: 640px) {
  .agent-approval-card__foot {
    flex-direction: column;
    align-items: flex-start;
  }

  .agent-approval-card__actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
}

[data-theme="dark"] .agent-approval-btn {
  background: color-mix(in srgb, var(--chat-surface-soft) 80%, #0b1220 20%);
}

[data-theme="dark"] .agent-approval-preview {
  background: color-mix(in srgb, var(--chat-surface-soft) 74%, #0b1220 26%);
}
</style>
