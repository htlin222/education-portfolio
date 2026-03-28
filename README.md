# EvalBot — Automated Teaching Evaluation Form Filler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://docs.astral.sh/uv/)
[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-orange)](https://claude.com/claude-code)
[![Agent-Driven](https://img.shields.io/badge/architecture-agent--driven-brightgreen)](https://github.com/htlin222/education-portfolio)
[![zh-TW](https://img.shields.io/badge/lang-繁體中文-red)](README.zh-TW.md)

> *"The purpose of evaluation is to improve, not to prove."* — Daniel Stufflebeam

## Why This Exists

Medical education demands that attending physicians complete dozens of evaluation forms for each trainee rotation — DOPS, Mini-CEX, CbD, 360-degree assessments, EPA checklists, meeting logs, and more. Each form requires careful scoring across multiple dimensions, written feedback on strengths, suggestions for improvement, and signatures.

In practice, most of these evaluations become **performative formalism** (形式主義的表演) — the act of filling forms to satisfy an audit trail rather than to genuinely advance a trainee's clinical growth. The evaluator already gave real-time feedback at the bedside. The form is paperwork after the fact.

This tool acknowledges that reality. It automates the mechanical parts — selecting competency levels, scoring rubrics, generating contextually appropriate written feedback — so that physicians can redirect their finite time toward what actually matters: teaching at the bedside, discussing difficult cases, and mentoring the next generation of doctors.

**This is not about cutting corners.** It's about recognizing that a system designed to document teaching quality has, through bureaucratic accumulation, become an obstacle to it.

## How It Works

```
evalbot CLI (Python)          Claude Code Agent
  ├── list    → JSON    ←──  Read pending evaluations
  ├── parse   → JSON    ←──  Analyze form structure
  ├── profile → JSON    ←──  Read evaluator identity
  ├── radio   ← submit  ──→  Select best option
  ├── text    ← submit  ──→  Generate positive feedback
  ├── textarea← submit  ──→  Generate positive feedback
  ├── checkbox← submit  ──→  Check options
  ├── combo   ← submit  ──→  Select dropdown option
  ├── date    ← submit  ──→  Fill date
  ├── ruler   ← submit  ──→  Score rubrics
  └── finalize← submit  ──→  Complete evaluation
```

Python handles HTTP/HTML parsing. Claude Code understands form semantics and generates feedback. No external API key needed — the agent running this tool IS the LLM.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.com/claude-code)

## Setup

```bash
make setup
```

## Cookie & Profile Configuration

Multi-user profiles under `profiles/`:

```
profiles/
├── default/
│   ├── cookies.json      ← browser-exported cookies
│   └── profile.json      ← identity (name, role, department)
├── user2/
│   ├── cookies.json
│   └── profile.json
└── ...
```

### Steps

1. `mkdir -p profiles/yourname`
2. Login to the evaluation system in browser → export cookies via browser extension → save as `profiles/yourname/cookies.json`
3. Create `profiles/yourname/profile.json`:

```json
{
  "name": "Your Name",
  "role": "主治醫師",
  "department": "Your Department"
}
```

> `role` is used to auto-select "evaluator identity" radio buttons (attending/resident/nurse/peer)

## Usage

### Via Claude Code Skill (recommended)

```
/eval-form
/eval-form --user user2
```

The agent will: read profile → list pending forms → parse each → generate feedback → fill & submit

### Manual CLI

```bash
make list                    # list pending evaluations
make list USER=user2        # specific user
make parse SFID=88492        # parse a single form

uv run python -m evalbot radio --sfid=88492 110443 113734
uv run python -m evalbot textarea --sfid=88492 110446 "Excellent technique"
uv run python -m evalbot ruler --sfid=88492 106503 8
uv run python -m evalbot finalize --sfid=88492
```

## Notes

- Session cookies expire when the browser closes — re-export when needed
- 0.5s delay between AJAX requests to be gentle on the server
- All submissions logged to `log/submissions.jsonl`
- Use `make parse SFID=XXX` to inspect form structure before filling

---

## How to Build Your Own Eval-Fill System

This project targets one hospital's e-portfolio, but the **pattern is universal**. If your institution uses any web-based evaluation system, you can clone this repo and adapt it.

### The Pattern

```
Browser (manual)          →  .har file  →  Claude Code analyzes  →  Python CLI  →  Claude Code skill
     ↓                         ↓                  ↓                     ↓                ↓
Login + fill 1 form    Capture traffic    Reverse-engineer API    Build parser+submitter  Orchestrate
```

### Step 1: Capture a HAR File

1. Open your evaluation system in Chrome/Edge
2. Open DevTools (`F12`) → **Network** tab → check **Preserve log**
3. Login, navigate to an evaluation form, **fill it out manually** for one student (touch every field type)
4. Right-click in the Network panel → **Save all as HAR with content**
5. Save as `your-system.har` in the project root

> This single HAR file captures every endpoint, request format, response structure, and authentication mechanism.

### Step 2: Let Claude Code Analyze the HAR

```
Analyze the HAR file at ./your-system.har and figure out:

1. Authentication: how does the session work? (cookies, tokens, headers)
2. Form listing: what URL lists pending evaluations? What's the HTML structure?
3. Form loading: what URL loads a single form? How are fields structured?
4. Field submission: what AJAX endpoints handle each field type? What params do they send?
5. Form finalization: how is the evaluation marked as complete?

For each AJAX endpoint, document:
- HTTP method and URL
- Request parameters (with examples from the HAR)
- Response format
- How the JavaScript triggers it (function name, event handler)

Output a structured reference document I can use to build a CLI tool.
```

### Step 3: Build the Python CLI

```bash
uv init --name evalbot
uv add requests beautifulsoup4
mkdir -p src/evalbot
```

Follow the subcommand pattern: `list`, `parse`, `radio`, `text`, `textarea`, `ruler`, `checkbox`, `combo`, `date`, `finalize`, `profile`.

Key principles:
- **All output is JSON** — the CLI is a tool for Claude Code to drive, not for humans
- **Each command re-parses the form** — gets fresh token/session values
- **Add `Referer` header** on POSTs — many systems validate this
- **Log every submission** to `log/submissions.jsonl`

### Step 4: Create a Claude Code Skill

Create `.claude/skills/eval-form/SKILL.md` that teaches Claude Code:

1. `evalbot profile` → know the evaluator's role
2. `evalbot list` → get pending forms
3. `evalbot parse --sfid=X` → read form structure
4. Decide what to fill based on field type and label semantics
5. **Generate comments inline** — no API call, Claude Code IS the LLM
6. Submit via `evalbot radio/text/textarea/ruler/...`
7. `evalbot finalize` to complete

The skill file encodes domain knowledge: what score to pick, how to write comments, which fields to skip.

### Step 5: Test

```bash
uv run python -m evalbot list              # verify connection
uv run python -m evalbot parse --sfid=123  # inspect form structure
# Then: /eval-form in Claude Code
```

### Tips

- **Start with one form type** (e.g., DOPS). Get it working, then add others.
- **The HAR file is your Rosetta Stone.** Endpoints, params, JS source, HTML — it's all there.
- **Watch for CSRF tokens.** Some systems embed them in hidden fields.
- **Keep `log/submissions.jsonl`** — your audit trail.

### Starter Prompt for a New System

```
I have a HAR file from my hospital's teaching evaluation system.
I want to build a CLI tool that can:
1. List pending evaluations
2. Parse form structure
3. Fill fields (radio, text, ruler, etc.)
4. Submit completed evaluations

Please analyze the HAR file, reverse-engineer the API,
and help me build a Python CLI following the evalbot pattern
in this repo. Start by reading the HAR file.
```

Claude Code will take it from there.

---

[中文版 README](README.zh-TW.md)
