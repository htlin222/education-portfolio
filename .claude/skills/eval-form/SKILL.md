---
name: eval-form
description: Fill your hospital's e-portfolio evaluation forms with positive zh-TW comments. Use when user wants to fill, list, or manage teaching evaluation forms, or mentions evalbot/評估/evaluation.
---

# 教學評估表單自動填寫

Drive the `evalbot` CLI to list, parse, fill, and finalize teaching evaluation forms on your hospital's e-portfolio. You (Claude Code) generate all text comments directly — no external API needed.

## Prerequisites

Run `make setup` (or `uv sync`) if not already done.

## User Profiles

Cookies are stored per-user under `profiles/`:

```
profiles/
├── default/cookies.json    ← fallback profile
├── user1/cookies.json
├── user2/cookies.json
└── ...
```

Use `--user NAME` (or `-u NAME`) on any command to select a profile:
```bash
uv run python -m evalbot -u user1 list
uv run python -m evalbot -u user2 fill --sfid=12345
```

If `--user` is omitted, resolution order: `./cookies.json` → `profiles/default/cookies.json`.

When the user says `/eval-form --user someone`, pass `-u someone` to every evalbot command.

Each profile can optionally have a `profile.json` with metadata:
```json
{
  "name": "Your Name",
  "role": "主治醫師",
  "department": "Your Department"
}
```

Use `role` to auto-select 評核者身分 radio when present. If no profile.json exists, ask the user on first encounter.

## Workflow

### 1. List pending evaluations

```bash
uv run python -m evalbot list              # default profile
uv run python -m evalbot -u user1 list     # specific user
```

Returns JSON array of `{sfid, student_name, passport_name, form_name}`.

### 2. Parse a form

```bash
uv run python -m evalbot parse --sfid=SFID
```

Returns JSON with `fields[]` and `ruler_blocks[]`. Each field has:
- `type`: `radio` | `text` | `textarea` | `checkbox` | `combo` | `date`
- `qid`: question ID (used in submit commands)
- `label`: question label (zh-TW)
- `said`: student answer ID
- `options[]`: (radio only) `{id, label}`
- `current_value`: (text/textarea) existing value — **skip if non-empty**
- `readonly`: (text) — **skip if true**

### 3. Decide values for each field

For each teacher-editable field, decide what to fill:

| Type | Strategy |
|------|----------|
| **radio** | Pick the **last option** (highest competency). Use its `id`. |
| **text** (numeric: label contains 分鐘/次數/時間) | Use sensible defaults: 觀察分鐘→`30`, 回饋分鐘→`10`, 次數→`5`, otherwise `15` |
| **text** (other) | Generate 1-2 sentence positive zh-TW comment |
| **textarea** | Generate 1-2 sentence positive zh-TW comment |
| **checkbox** | Check all non-"other" options, or pick the most positive/appropriate ones. Pass comma-separated IDs. |
| **combo** (dropdown) | Pick the best/last option. Use its `id`. |
| **date** | Use today's date in `YYYY/MM/DD` format unless context suggests otherwise. |
| **ruler_blocks** | Submit with score `8` (or user-specified) |

**Comment generation rules:**
- 繁體中文 (zh-TW), 正向積極, 100-200 字
- 具體且與該臨床技能/表單主題相關
- 如果 label 含「建議加強」or「改進」→ 溫和鼓勵語氣，提出小建議
- 如果 label 含「表現良好」or「優點」→ 肯定具體表現
- 如果 label 含「會談紀錄」→ 寫成師生會談紀要，討論訓練進度與學習狀況
- 如果 label 含「(不公開)」or「(隱藏)」→ 可稍微坦率但仍正向
- 不要用 emoji
- 填充題（text）上限 300 字，問答題（textarea）上限 60,000 字

**Special field handling:**
- **Signature fields** (label 含「簽章」or「簽名」, readonly=true): skip — server auto-signs via putUsername
- **Auto-score fields** (label 含「分數計算」or has auto-calc): skip — server auto-calculates from rulers
- **Ruler blocks with empty qid or empty cells**: skip — these are display-only or student-filled
- **0 teacher fields**: just finalize directly (e.g. Patient Log, student-only forms)
- **Radio "評核者身分"**: ask user which role they are (主治醫師/同儕/護理師/住院醫師), or infer from profile context. Do NOT default to last option.
- **Radio "病歷複雜度"**: pick 中 (middle option), not last
- **Combo EPA trust levels**: pick Level 4 (可獨立執行), not last (Level 5 is rare)

### 4. Submit field values

```bash
# Radio
uv run python -m evalbot radio --sfid=SFID QID OPTION_ID

# Text
uv run python -m evalbot text --sfid=SFID QID "評語內容"

# Textarea
uv run python -m evalbot textarea --sfid=SFID QID "評語內容"

# Checkbox (comma-separated checked option IDs)
uv run python -m evalbot checkbox --sfid=SFID QID "ID1,ID2,ID3"

# Combo (dropdown)
uv run python -m evalbot combo --sfid=SFID QID OPTION_ID

# Date
uv run python -m evalbot date --sfid=SFID QID "2026/03/28"

# Ruler (all rows in block filled at given score)
uv run python -m evalbot ruler --sfid=SFID QID 8
```

Each returns `{"ok": true, ...}`.

### 5. Finalize the evaluation

```bash
uv run python -m evalbot finalize --sfid=SFID
```

### 6. Repeat for all pending forms

Loop through all sfids from step 1.

## Batch Execution Pattern

For efficiency, process one form at a time:

1. `evalbot list` → get all sfids
2. For each sfid:
   a. `evalbot parse --sfid=X` → read structure
   b. Submit radios (can batch multiple in one shell command with `&&`)
   c. Generate and submit text/textarea comments
   d. Submit rulers
   e. `evalbot finalize --sfid=X`
3. Report summary

## Error Handling

- `{"error": "Session 已過期..."}` → Ask user to re-export cookies.json from browser
- Any `{"error": ...}` → Report to user, skip that form, continue with next

## Cookie Refresh

If session expired, tell user:
1. Login to your hospital's e-portfolio in browser
2. Export cookies with browser extension
3. Save as `profiles/{username}/cookies.json`
