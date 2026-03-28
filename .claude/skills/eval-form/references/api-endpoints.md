# API Endpoints Reference

Base URL: Configured in `local_config.yaml`

## Pages

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `Evaluate` | GET | Listing page — HTML table of pending evaluations |
| `oneEvaluate?sfid={ID}` | GET | Single form — HTML with fields, rulers, hidden metadata |
| `histEvaluate` | GET | Historical/completed evaluations |

## AJAX Submission Endpoints (POST)

All under `manage/` prefix. All return `{"msg": "ok"}` on success.

| Endpoint | Purpose | Key Params |
|----------|---------|------------|
| `updRadioStuformAjax` | Radio selection | pid, pcid, qfid, sfid, qid, said, qiid, othtxt |
| `updTextStuformAjax` | Text input | pid, pcid, qfid, sfid, qid, said, txt |
| `updText2StuformAjax` | Textarea | pid, pcid, qfid, sfid, qid, said, txt |
| `updRuler2StuformAjax` | Ruler scale | pid, pcid, qfid, sfid, qid, qrids, qroids |
| `updCheckboxStuformAjax` | Checkbox | pid, pcid, qfid, sfid, qid, chkid, chked |
| `EvaluateAjax` | Finalize form | sfid, psnt=100 |

## Hidden Fields (FormMetadata)

Extracted from `<input type="hidden">` in form HTML:

| Field | ID | Purpose |
|-------|-----|---------|
| `stvo.pid` | `pid` | Passport ID |
| `stvo.pcid` | `pcid` | Passport Category ID |
| `stvo.qfid` | `qfid` | Question Form ID |
| `sfid` | `sfid` | Student Form ID |

## SAID (Student Answer ID)

- Stored in `<span class="hsaid">` next to each field
- Server returns updated SAID after each POST
- The CLI re-parses the form for each command, so SAID tracking is automatic

## Form Field Detection

- Teacher-editable: div has class `myown`
- Required: div has class `mustkey`
- Radio QID: from `onclick="updAradio(this, {QID})"`
- Checkbox QID: from `onclick="updAcheck(this, {QID})"`
- Combo QID: from `onchange="updCombo(this, {QID})"`
- Text QID: from `onblur="updAtext(this, {QID})"` or `data-qid`
- Textarea QID: from `onblur="updAtext2(this, {QID})"`
- Date QID: from `onblur="updAdate(this, {QID})"` or class `datepicker`
- Ruler QID: from `<button onclick="tmpSaveRuler2(this, {QID})">`
- Signature: `<span onclick="putUsername(this, '{name}', {QID})">` → treated as readonly text

## Form Types (from eportfolio guide v1.3)

| Form Type | Field Types Used | Notes |
|-----------|-----------------|-------|
| DOPS | radio, text, textarea, ruler | Standard procedure evaluation |
| Mini-CEX | radio, text, textarea, ruler | Clinical encounter evaluation |
| CbD | radio, text, textarea, ruler | Case-based discussion |
| 360度評量 | radio, textarea, ruler | Multi-source feedback |
| EPA | combo, textarea, text | Entrustable Professional Activities |
| 六大核心能力 | radio, textarea, ruler | Core competency evaluation |
| 會談紀錄 | text, textarea, ruler(display-only) | Meeting record — ruler may have no qid |
| Patient Log | (none) | Student-only, teacher just finalizes |
| 教學評量 | (student fills) | Teacher just finalizes |
| 雙向回饋 | radio | Student rates teacher — rarely in teacher queue |
| 多重審核 | varies | Multi-reviewer chain, server manages flow |

## Field Limits

- Text (填充題): 300 characters max
- Textarea (問答題): 60,000 characters max
