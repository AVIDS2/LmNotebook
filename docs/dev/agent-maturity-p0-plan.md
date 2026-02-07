# Agent Maturity P0 Plan

## Goal
Stabilize the agent from "chat-first" to "action-trustable":
- tool execution is explicit
- write actions require deterministic approval
- first request can execute reliably without "ask again"

## Scope (P0)

1. Backend Human-in-the-loop approval with LangGraph `interrupt/resume`
2. Standardized pre-execution card payload (target note / operation / scope)
3. Execution stream separation (chat text vs execution events)
4. Session persistence for execution records and approval state

## Out of Scope (for P0)

- Full workspace-side panel mode (P1)
- Complex diff UX (fold by headings, advanced filtering)
- Cross-device sync of execution logs

## Work Breakdown

### Step 1 - Backend approval gate (`interrupt/resume`)
Status: `done`

- Add approval gate for write tools:
  - `update_note`
  - `create_note`
  - `delete_note`
  - `rename_note`
  - `set_note_category`
- Emit interrupt payload with:
  - `operation`
  - `target_note_id`
  - `target_note_title` (if known)
  - `scope`
  - `args_preview`
- Resume via explicit command path:
  - approve => execute tool
  - reject => cancel tool and return clear assistant message

Acceptance:
- First request can stop at approval without silent noop.
- Confirm can resume and execute same tool call deterministically.
- Reject does not mutate note data.

### Step 2 - API contract for approval
Status: `done`

- Extend `/api/chat/stream` request model for approval resume payload.
- Keep backward compatibility with existing frontend.

Acceptance:
- Old calls still work.
- New calls with resume payload work.

### Step 3 - Stream adapter alignment
Status: `done`

- Add explicit event types:
  - `approval_required`
  - `approval_resolved`
- Keep existing `part_type=text/tool` behavior intact.

Acceptance:
- Frontend can render approval cards from backend event directly.
- No duplicate "tool running/completed" for same action.

### Step 4 - Frontend wiring cleanup
Status: `done`

- Replace heuristic draft-only flow with backend-backed approval event.
- Keep optimistic UI only for local affordance, not source of truth.

Acceptance:
- Approve/Reject latency under 300ms local feedback.
- Source of truth from backend stream.

## Risks

1. Existing `chat-tool-chat` loop may re-enter unexpectedly.
2. Checkpointer state may keep stale tool calls.
3. Frontend/backed mixed legacy events can duplicate UI rows.

Mitigation:
- Add strict state transition checks in graph nodes.
- Sanitize orphaned tool calls before resume.
- Deduplicate tool events by `tool_id`.

## Validation Checklist

- [x] `npm run build` passes
- [x] backend files compile (`python -m py_compile ...`)
- [x] "整理当前笔记格式" first request shows approval-required event
- [x] clicking approve executes once
- [x] clicking reject produces no note mutation
- [x] session reload restores pending/finished execution state

## P1 Extension (Completed in this branch)

- [x] Right-sidebar mode (`AgentBubble` large-screen panel toggle)
- [x] Structured diff review flow restored for manual-review mode after execution approval
