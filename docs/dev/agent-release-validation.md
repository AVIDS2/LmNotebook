# Agent Release Validation Checklist

Date: 2026-02-07
Owner: Engineering

## Goal

Provide a deterministic, repeatable validation flow for the agent runtime before release.

## Runtime Scenarios

- [ ] `CHAT` intent: greeting/qa returns direct response, no tool calls.
- [ ] `TASK` read intent: summary/query calls read tools and returns structured answer.
- [ ] `TASK` write intent + `auto_accept_writes=true`: write tool executes directly.
- [ ] `TASK` write intent + `auto_accept_writes=false`: write tool enters approval first.
- [ ] Approval `Accept`: state transitions `pending -> running -> completed`.
- [ ] Approval `Reject`: no note mutation, assistant returns explicit rejection outcome.
- [ ] Session reload with pending approval: pending card and execution context restore correctly.
- [ ] Resume with missing/invalid `approval_id`: action rejected safely.
- [ ] Resume with mismatched `approval_id`: action rejected safely.

## Frontend UX Contracts

- [ ] Pending approval does not appear as running execution.
- [ ] `currentStatus` text does not stay stale after completion.
- [ ] Execution records show final states (`完成/失败`) and no duplicate running rows.
- [ ] Approval card hides when no pending execution or diff approval exists.
- [ ] No `SYSTEM_LOG` text leaks into model-visible assistant history.
- [ ] Chinese copy stays UTF-8 clean in placeholder/status/context menu/history labels.

## Data/State Safety

- [ ] No destructive auto-cleanup of checkpoint state on uncertain errors.
- [ ] Invalid checkpoint/resume path returns explicit error message, not silent reset.
- [ ] Note content refreshes after write tool completion without note-switch workaround.

## Release Commands

Run from repo root:

```powershell
npm run build
python -m py_compile src/backend/main.py src/backend/api/chat.py src/backend/agent/graph.py src/backend/agent/supervisor.py src/backend/agent/stream_adapter.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/release_check.ps1
```

## Residual Risks & Guardrails

- Risk: Third-party model latency spikes can delay stream completion.
  Guardrail: Keep UI immediate-state transitions local (`pending/running`) and surface timeout errors.
- Risk: Interrupt/resume edge cases from stale local storage UI state.
  Guardrail: Persist only minimal approval state and clear stale card when no pending approvals exist.
- Risk: Future mixed-language copy regressions.
  Guardrail: keep status strings centralized and run UTF-8 smoke checks in release flow.
