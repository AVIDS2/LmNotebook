# Stability Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove release-time configuration pitfalls and restore deterministic local test signals for the vector sync scheduler path.

**Architecture:** Keep runtime behavior unchanged unless necessary; prioritize contract alignment between tests and implementation, then align packaging/config artifacts with what CI and local release flows actually consume. Add low-cost guardrails in pre-release checks to fail fast when required assets are missing.

**Tech Stack:** Node.js test runner, Electron Builder config, PowerShell release script, Python/FastAPI env template.

---

### Task 1: Align Vector Sync Scheduler Contract Tests

**Files:**
- Modify: `scripts/vector-sync-scheduler.test.mjs`

**Step 1: Write/update failing contract test cases for current scheduler API**

```javascript
test('schedules one batch after debounce delay', async () => {
  const calls = []
  const scheduler = createVectorSyncScheduler(async (batch) => {
    calls.push(batch)
  }, { debounceMs: 25, flushIntervalMs: 5 })

  scheduler.schedule({ noteId: 'n1', title: 'A', content: 'hello' })
  await sleep(45)

  assert.equal(calls.length, 1)
  assert.equal(calls[0].length, 1)
  assert.equal(calls[0][0].noteId, 'n1')
})
```

**Step 2: Run test to verify current status**

Run: `node scripts/vector-sync-scheduler.test.mjs`
Expected: PASS with all subtests green after contract alignment.

**Step 3: If any assertion still fails, apply minimal test/implementation adjustment**

```javascript
// Keep assertions on batch arrays and option-object signature.
```

**Step 4: Re-run to confirm deterministic pass**

Run: `node scripts/vector-sync-scheduler.test.mjs`
Expected: `# pass 3` and `# fail 0`.

**Step 5: Commit**

```bash
git add scripts/vector-sync-scheduler.test.mjs
git commit -m "test: align vector sync scheduler contract tests"
```

### Task 2: Refresh Backend Environment Template

**Files:**
- Modify: `src/backend/.env.example`

**Step 1: Update template keys to match active backend config and docs**

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini

DASHSCOPE_API_KEY=your_dashscope_key_here
EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_MODE=api

GOOGLE_API_KEY=
GLM_API_KEY=
```

**Step 2: Validate no stale/contradictory keys remain**

Run: `rg -n "GLM_API_KEY|OPENAI_API_KEY|DASHSCOPE_API_KEY|EMBEDDING_MODEL|EMBEDDING_MODE" src/backend/.env.example`
Expected: all active keys present exactly once.

**Step 3: Commit**

```bash
git add src/backend/.env.example
git commit -m "docs: refresh backend env example"
```

### Task 3: Make Release Icon Requirements Explicit and Verifiable

**Files:**
- Modify: `.gitignore`
- Modify: `scripts/release_check.ps1`

**Step 1: Unignore required build icon assets while keeping build outputs ignored**

```gitignore
build/
!build/
build/*
!build/icon.ico
!build/icon.png
```

**Step 2: Add hard checks for icon files in release preflight script**

```powershell
$iconIco = Join-Path $RepoRoot "build\icon.ico"
$iconPng = Join-Path $RepoRoot "build\icon.png"
Test-PathRequired $iconIco "Windows icon"
Test-PathRequired $iconPng "PNG icon"
```

**Step 3: Verify preflight output**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/release_check.ps1`
Expected: no icon-related errors when files exist.

**Step 4: Commit**

```bash
git add .gitignore scripts/release_check.ps1
git commit -m "build: enforce tracked icon assets and preflight checks"
```

### Task 4: Verification Gate

**Files:**
- Modify: `docs/plans/2026-02-14-stability-hardening.md` (mark verification outcomes)

**Step 1: Run focused regression checks**

Run: `node scripts/vector-sync-scheduler.test.mjs`
Expected: pass.

Run: `python -m pytest -q tests`
Workdir: `src/backend`
Expected: pass (existing baseline).

**Step 2: Capture evidence and residual risks**

- Confirm tracked state for icons: `git ls-files build/icon.ico build/icon.png`
- Note any remaining non-blocking backlog (branding rename, single-instance lock, i18n completion).

**Step 3: Commit plan evidence update (optional)**

```bash
git add docs/plans/2026-02-14-stability-hardening.md
git commit -m "docs: record stability hardening verification evidence"
```
