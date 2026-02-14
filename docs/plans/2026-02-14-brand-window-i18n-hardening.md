# Brand / Window / i18n Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete batch 1/2/3 hardening by unifying visible branding to LmNotebook, enforcing predictable window lifecycle (single-instance + explicit quit), and removing key hardcoded UI text in agent components via i18n.

**Architecture:** Add static contract tests under `scripts/` first to lock requirements, then apply minimal runtime changes in Electron main process and Vue components. Keep backward-compatible identifiers (appId, local data folder names) unchanged to avoid migration breakage.

**Tech Stack:** Electron main process, Vue 3 SFCs, custom i18n catalog, Node.js `node:test` scripts.

---

### Task 1: Add Failing Contract Tests

**Files:**
- Create: `scripts/branding-window-contract.test.mjs`
- Create: `scripts/agent-i18n-hardcoded.test.mjs`

**Step 1: Brand/window contract test**

```javascript
test('package and shell branding should use LmNotebook', ...)
test('main process should enforce single-instance and explicit close-to-quit', ...)
```

**Step 2: Agent i18n hardcoded text test**

```javascript
test('agent/session/model settings components should not keep selected hardcoded labels', ...)
```

**Step 3: Verify both tests fail before implementation**

Run: `node scripts/branding-window-contract.test.mjs`
Expected: FAIL

Run: `node scripts/agent-i18n-hardcoded.test.mjs`
Expected: FAIL

### Task 2: Implement Branding + Window Governance

**Files:**
- Modify: `package.json`
- Modify: `src/main/index.ts`
- Modify: `src/renderer/index.html`
- Modify: `src/renderer/src/App.vue`
- Modify: `src/renderer/src/components/common/StartupPage.vue`
- Modify: `src/renderer/src/components/sidebar/DataSettings.vue`
- Modify: `src/renderer/src/services/exportService.ts`
- Modify: `src/renderer/src/i18n/messages.json`

**Step 1: Visible branding rename**
- Replace visible `Origin Notes` strings with `LmNotebook` in app title bar/startup/page title/tray tooltip/settings fallback/export header.

**Step 2: Single-instance lock + second-instance focus behavior**
- Add `app.requestSingleInstanceLock()` gate and `second-instance` handler to focus/restore existing window.

**Step 3: Close semantics**
- Replace close-to-tray interception with explicit quit path on `window-close` IPC.
- Keep tray entrypoint and quit action intact.

### Task 3: Implement i18n Cleanup in Agent UI

**Files:**
- Modify: `src/renderer/src/components/agent/SessionHistoryPanel.vue`
- Modify: `src/renderer/src/components/agent/ModelSettings.vue`
- Modify: `src/renderer/src/components/agent/AgentBubble.vue`
- Modify: `src/renderer/src/i18n/messages.json`

**Step 1: SessionHistoryPanel cleanup**
- Replace action button `title` hardcoded text with props (already localized by parent).

**Step 2: ModelSettings localization**
- Integrate `useI18n()` and replace UI labels/placeholders/confirm prompt with i18n keys.

**Step 3: AgentBubble key hardcoded UI text cleanup**
- Replace composer/menu/note selector/model selector strings and approval card labels with i18n keys.
- Replace context-menu copy label with i18n key.
- Keep knowledge trigger backward compatible by accepting both localized trigger and legacy `@笔记知识库`.

### Task 4: Verification Gate

**Files:**
- Modify: `docs/plans/2026-02-14-brand-window-i18n-hardening.md` (append verification evidence if needed)

**Step 1: Run contract tests**

Run: `node scripts/branding-window-contract.test.mjs`
Expected: PASS

Run: `node scripts/agent-i18n-hardcoded.test.mjs`
Expected: PASS

**Step 2: Run existing regression checks**

Run: `node scripts/i18n.test.mjs`
Expected: PASS

Run: `node scripts/vector-sync-scheduler.test.mjs`
Expected: PASS

Run (workdir `src/backend`): `python -m pytest -q tests`
Expected: PASS

**Step 3: Report residual risks**
- Remaining scope outside this batch (full repository-wide brand/doc/backend naming migration).
