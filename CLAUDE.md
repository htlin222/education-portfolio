# EvalBot — Project Instructions

## Overview

Automated teaching evaluation form filler for your hospital's e-portfolio.
BASE_URL is configured in `local_config.yaml`.
Python CLI driven by Claude Code agent via local skill.

## Key Paths

- **Skill**: `.claude/skills/eval-form/SKILL.md` — orchestration guide for `/eval-form`
- **References**: `.claude/skills/eval-form/references/api-endpoints.md` — API docs, form types
- **Profiles**: `profiles/{name}/cookies.json` + `profile.json` — per-user auth & identity
- **Logs**: `log/submissions.jsonl` — JSONL audit trail of all submissions
- **CLI source**: `src/evalbot/` — Python package

## Critical Implementation Details

### POST endpoints use relative URLs (no `manage/` prefix)

The JavaScript in stuform.js uses `$.post('updRadioStuformAjax', ...)` — these are **relative to the form page** (`/eportfolio/oneEvaluate`), resolving to `/eportfolio/updRadioStuformAjax`.

Do NOT prefix with `manage/`. This was a bug that caused "不正確的學員" errors.

### Referer header required on POSTs

All AJAX POSTs must include `Referer: {BASE_URL}oneEvaluate?sfid={sfid}` (BASE_URL from `local_config.yaml`).

### SAID tracking is automatic

Each command re-parses the form HTML to get fresh SAID values. No need to chain SAIDs between commands.

### Completed forms are not readable

Once `finalize` is called, the form is no longer accessible via `oneEvaluate`. Always ensure `log/submissions.jsonl` logging is in place **before** batch operations.

## Profiles

User cookies and identity stored in `profiles/{name}/`:

```
profiles/
├── default/
│   ├── cookies.json      ← EditThisCookie export
│   └── profile.json      ← {"name": "...", "role": "主治醫師", "department": "..."}
```

`role` in profile.json is used to auto-select 評核者身分 radio (主治醫師/住院醫師/護理師/同儕).

## Package Management

- Use `uv` (not pip). `uv sync` to install, `uv run python -m evalbot` to run.
- No `anthropic` dependency — the Claude Code session itself generates all text.

## Workflow

1. `evalbot -u USER profile` — read evaluator identity
2. `evalbot -u USER list` — get pending forms (JSON)
3. `evalbot -u USER parse --sfid=X` — read form structure (JSON)
4. Agent decides fill values, generates comments inline
5. `evalbot radio/text/textarea/checkbox/combo/date/ruler` — submit fields
6. `evalbot finalize --sfid=X` — complete evaluation
7. All submissions logged to `log/submissions.jsonl`

## Common Pitfalls

- Session cookies expire when browser closes — user must re-export
- Ruler blocks with empty `qid` or empty `cells` — skip, don't submit
- Forms with 0 teacher fields (Patient Log, student-only) — just finalize
- Radio "評核者身分" — match against profile role, don't pick last option
- Radio "病歷複雜度" — pick 中 (middle), not last
