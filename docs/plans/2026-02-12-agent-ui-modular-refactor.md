# Agent UI Modular Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split oversized agent UI component into maintainable modules without changing behavior.

**Architecture:** Keep `AgentBubble.vue` as orchestration container, move independent concerns (attachments parsing, session panel rendering, approval UI, composer controls) into focused modules/components. Preserve existing backend contract and streaming behavior.

**Tech Stack:** Vue 3 (`<script setup lang="ts">`), Electron renderer, TypeScript, existing fetch/SSE pipeline.

---

### Task 1: Extract attachment domain helpers

**Files:**
- Create: `src/renderer/src/components/agent/attachmentUtils.ts`
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Test: `npm run build`

**Step 1: Move attachment types and pure helper functions**
- `ComposerAttachment` type
- file type detection
- text/image/docx extraction
- `buildComposerAttachment`

**Step 2: Keep UI behavior unchanged**
- `AgentBubble.vue` keeps merge/remove/open handlers and DnD logic.

**Step 3: Run build**
- Command: `npm run build`
- Expected: pass without TS/Vite errors.

### Task 2: Extract session history panel as presentational component

**Files:**
- Create: `src/renderer/src/components/agent/SessionHistoryPanel.vue`
- Create: `src/renderer/src/components/agent/sessionTypes.ts`
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Test: `npm run build`

**Step 1: Move panel template and events to child component**
- Parent retains loading, rename, pin, delete business logic.

**Step 2: Keep styles and interaction parity**
- No visual regression target.

**Step 3: Run build**
- Command: `npm run build`
- Expected: pass.

### Task 3: Split approval/task UI

**Files:**
- Create: `src/renderer/src/components/agent/ApprovalInlineCard.vue`
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Test: `npm run build`

**Step 1: Extract pending approval rendering only**
- Keep parent state and actions.

**Step 2: Keep shadcn-like compact style**
- Remove duplicate style conflicts in parent.

**Step 3: Build validation**
- Command: `npm run build`

### Task 4: Split composer footer

**Files:**
- Create: `src/renderer/src/components/agent/ComposerBar.vue`
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Test: `npm run build`

**Step 1: Move input + mode + review + upload menu**
- Parent keeps send/stop callbacks.

**Step 2: Add unit-level event contracts**
- Emit typed events for send/stop/upload/mode switches.

**Step 3: Build validation**
- Command: `npm run build`

### Task 5: Regression checks and cleanup

**Files:**
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Test: `npm run build`, `pytest src/backend/tests/test_chat_session_content_format.py src/backend/tests/test_supervisor_attachments.py src/backend/tests/test_graph_fast_chat_mode.py`

**Step 1: Remove dead CSS and duplicate selectors in parent**

**Step 2: Verify core flows**
- ask/agent mode
- approval flow
- image/docx/file attachment path
- session history load/rename/pin/delete

**Step 3: Commit**
- Message suggestion: `refactor(agent-ui): split bubble into focused modules`
