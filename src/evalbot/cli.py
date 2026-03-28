"""
evalbot CLI — JSON-oriented tool for Claude Code agent to drive.

Subcommands:
  list                        List pending evaluations (JSON)
  parse   --sfid ID           Parse form structure (JSON)
  radio   --sfid ID QID OID   Submit radio selection
  text    --sfid ID QID TXT   Submit text value
  textarea --sfid ID QID TXT  Submit textarea value
  ruler   --sfid ID QID SCORE Submit all ruler rows at given score
  checkbox --sfid ID QID IDS  Submit checkbox selections
  combo   --sfid ID QID OID   Submit combo/dropdown selection
  date    --sfid ID QID DATE  Submit date value
  finalize --sfid ID          Submit/complete the evaluation
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evalbot.session import load_session, validate_session, SessionExpiredError
from evalbot.listing import fetch_pending
from evalbot.parser import fetch_and_parse
from evalbot import submitter
from evalbot.logger import log as _log


def main() -> None:
    p = argparse.ArgumentParser(prog="evalbot")
    p.add_argument("--cookies", default="cookies.json")
    p.add_argument("--user", "-u", default=None, help="Profile name under profiles/ (e.g. user1)")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list")
    sub.add_parser("profile")

    sp = sub.add_parser("parse")
    sp.add_argument("--sfid", required=True)

    sp = sub.add_parser("radio")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("option_id")

    sp = sub.add_parser("text")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("value")

    sp = sub.add_parser("textarea")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("value")

    sp = sub.add_parser("ruler")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("score", type=int)

    sp = sub.add_parser("checkbox")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("checked_ids", help="Comma-separated option IDs to check")

    sp = sub.add_parser("combo")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("option_id")

    sp = sub.add_parser("date")
    sp.add_argument("--sfid", required=True)
    sp.add_argument("qid")
    sp.add_argument("value", help="Date in YYYY/MM/DD format")

    sp = sub.add_parser("finalize")
    sp.add_argument("--sfid", required=True)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        sys.exit(1)

    if args.cmd == "profile":
        _do_profile(args.user, args.cookies)
        return

    try:
        session = load_session(args.cookies, user=args.user)
        validate_session(session)
    except (SessionExpiredError, FileNotFoundError) as e:
        _err(str(e))
        sys.exit(1)

    try:
        if args.cmd == "list":
            _do_list(session)
        elif args.cmd == "parse":
            _do_parse(session, args.sfid)
        elif args.cmd == "radio":
            _do_radio(session, args.sfid, args.qid, args.option_id)
        elif args.cmd == "text":
            _do_text(session, args.sfid, args.qid, args.value)
        elif args.cmd == "textarea":
            _do_textarea(session, args.sfid, args.qid, args.value)
        elif args.cmd == "ruler":
            _do_ruler(session, args.sfid, args.qid, args.score)
        elif args.cmd == "checkbox":
            _do_checkbox(session, args.sfid, args.qid, args.checked_ids)
        elif args.cmd == "combo":
            _do_combo(session, args.sfid, args.qid, args.option_id)
        elif args.cmd == "date":
            _do_date(session, args.sfid, args.qid, args.value)
        elif args.cmd == "finalize":
            _do_finalize(session, args.sfid)
    except Exception as e:
        _err(str(e))
        sys.exit(1)


def _out(data: dict | list) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _err(msg: str) -> None:
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)


def _do_profile(user: str | None, cookies_arg: str) -> None:
    from evalbot.session import resolve_cookies_path
    try:
        cookies_path = resolve_cookies_path(cookies_arg, user)
    except FileNotFoundError:
        cookies_path = None

    profile_dir = cookies_path.parent if cookies_path else Path(f"profiles/{user or 'default'}")
    profile_file = profile_dir / "profile.json"

    if profile_file.exists():
        with profile_file.open() as f:
            data = json.load(f)
        data["cookies_path"] = str(cookies_path) if cookies_path else None
        data["profile_dir"] = str(profile_dir)
        _out(data)
    else:
        _out({
            "name": None,
            "role": None,
            "department": None,
            "cookies_path": str(cookies_path) if cookies_path else None,
            "profile_dir": str(profile_dir),
            "note": "No profile.json found. Create one with name, role, department.",
        })


def _do_list(session) -> None:
    items = fetch_pending(session)
    _out([
        {
            "sfid": i.sfid,
            "student_name": i.student_name,
            "passport_name": i.passport_name,
            "form_name": i.form_name,
        }
        for i in items
    ])


def _do_parse(session, sfid: str) -> None:
    from evalbot.models import RadioField, TextField, TextareaField, CheckboxField, ComboField, DateField

    form = fetch_and_parse(session, sfid)

    fields = []
    for f in form.fields:
        d: dict = {
            "type": f.field_type,
            "qid": f.question_id,
            "label": f.label,
            "said": f.said,
            "required": f.is_required,
        }
        if isinstance(f, RadioField):
            d["options"] = [
                {"id": o.value_id, "label": o.label, "is_other": o.is_other}
                for o in f.options
            ]
        elif isinstance(f, TextField):
            d["current_value"] = f.current_value
            d["readonly"] = f.is_readonly
        elif isinstance(f, TextareaField):
            d["current_value"] = f.current_value
        elif isinstance(f, CheckboxField):
            d["options"] = [
                {"id": o.value_id, "label": o.label, "is_other": o.is_other}
                for o in f.options
            ]
        elif isinstance(f, ComboField):
            d["options"] = [
                {"id": o.value_id, "label": o.label}
                for o in f.options
            ]
        elif isinstance(f, DateField):
            d["current_value"] = f.current_value
        fields.append(d)

    rulers = []
    for blk in form.ruler_blocks:
        rulers.append({
            "qid": blk.question_id,
            "label": blk.label,
            "scale_description": blk.scale_description,
            "headers": blk.headers,
            "rows": [
                {"row_id": r.row_id, "label": r.label, "cells": {str(k): v for k, v in r.cells.items()}}
                for r in blk.rows
            ],
        })

    _out({
        "sfid": form.metadata.sfid,
        "pid": form.metadata.pid,
        "pcid": form.metadata.pcid,
        "qfid": form.metadata.qfid,
        "title": form.title,
        "student_name": form.student_name,
        "fields": fields,
        "ruler_blocks": rulers,
    })


def _do_radio(session, sfid: str, qid: str, option_id: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    # find label for log
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    from evalbot.models import RadioField
    opt_label = ""
    for f in form.fields:
        if f.question_id == qid and isinstance(f, RadioField):
            opt_label = next((o.label for o in f.options if o.value_id == option_id), "")
    new_said = submitter.update_radio(session, meta, qid, said, option_id)
    _log("radio", sfid, qid=qid, label=label, option_id=option_id, option_label=opt_label, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _do_text(session, sfid: str, qid: str, value: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    new_said = submitter.update_text(session, meta, qid, said, value)
    _log("text", sfid, qid=qid, label=label, value=value, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _do_textarea(session, sfid: str, qid: str, value: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    new_said = submitter.update_textarea(session, meta, qid, said, value)
    _log("textarea", sfid, qid=qid, label=label, value=value, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _do_ruler(session, sfid: str, qid: str, score: int) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata

    blk = None
    for b in form.ruler_blocks:
        if b.question_id == qid:
            blk = b
            break
    if not blk:
        raise ValueError(f"Ruler block qid={qid} not found")

    # Find colidx for desired score
    target_colidx = None
    for i, h in enumerate(blk.headers):
        if h == str(score):
            target_colidx = i + 1
            break
    if target_colidx is None:
        target_colidx = min(score + 1, len(blk.headers))

    row_ids = [r.row_id for r in blk.rows]
    option_ids = [r.cells.get(target_colidx, "0") for r in blk.rows]

    submitter.update_ruler(session, meta, qid, row_ids, option_ids)
    _log("ruler", sfid, qid=qid, score=score, rows=len(row_ids), title=form.title)
    _out({"ok": True, "qid": qid, "rows_filled": len(row_ids), "score": score})


def _do_finalize(session, sfid: str) -> None:
    ok = submitter.submit_form(session, sfid)
    _log("finalize", sfid, ok=ok)
    _out({"ok": ok, "sfid": sfid})


def _do_checkbox(session, sfid: str, qid: str, checked_ids_str: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    checked_ids = [x.strip() for x in checked_ids_str.split(",") if x.strip()]
    new_said = submitter.update_checkbox(session, meta, qid, said, checked_ids)
    _log("checkbox", sfid, qid=qid, label=label, checked_ids=checked_ids, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _do_combo(session, sfid: str, qid: str, option_id: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    new_said = submitter.update_combo(session, meta, qid, said, option_id)
    _log("combo", sfid, qid=qid, label=label, option_id=option_id, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _do_date(session, sfid: str, qid: str, value: str) -> None:
    form = fetch_and_parse(session, sfid)
    meta = form.metadata
    said = _find_said(form, qid)
    label = next((f.label for f in form.fields if f.question_id == qid), "")
    new_said = submitter.update_date(session, meta, qid, said, value)
    _log("date", sfid, qid=qid, label=label, value=value, title=form.title)
    _out({"ok": True, "qid": qid, "new_said": new_said})


def _find_said(form, qid: str) -> str:
    for f in form.fields:
        if f.question_id == qid:
            return f.said
    return ""
