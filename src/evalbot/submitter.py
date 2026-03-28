from __future__ import annotations

import time

import requests

from evalbot.config import BASE_URL, ENDPOINTS, POST_DELAY_SECONDS
from evalbot.models import FormMetadata


def _post(session: requests.Session, endpoint: str, data: dict, sfid: str = "") -> dict:
    time.sleep(POST_DELAY_SECONDS)
    headers = {}
    if sfid:
        headers["Referer"] = f"{BASE_URL}oneEvaluate?sfid={sfid}"
    resp = session.post(BASE_URL + endpoint, data=data, headers=headers)
    resp.raise_for_status()
    result = resp.json()
    msg = result.get("msg", "")
    if "ok" not in msg:
        raise RuntimeError(f"伺服器回傳錯誤: {msg}")
    return result


def _base_data(meta: FormMetadata) -> dict:
    return {
        "pid": meta.pid,
        "pcid": meta.pcid,
        "qfid": meta.qfid,
        "sfid": meta.sfid,
    }


def update_radio(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    option_id: str,
) -> str:
    data = _base_data(meta)
    data.update({"qid": qid, "said": said, "qiid": option_id, "othtxt": ""})
    result = _post(session, ENDPOINTS["radio"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def update_text(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    text: str,
) -> str:
    data = _base_data(meta)
    data.update({"qid": qid, "said": said, "txt": text})
    result = _post(session, ENDPOINTS["text"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def update_textarea(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    text: str,
) -> str:
    data = _base_data(meta)
    data.update({"qid": qid, "said": said, "txt": text})
    result = _post(session, ENDPOINTS["textarea"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def update_ruler(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    row_ids: list[str],
    option_ids: list[str],
) -> None:
    data = _base_data(meta)
    data.update(
        {
            "qid": qid,
            "qrids": ",".join(row_ids) + ",",
            "qroids": ",".join(option_ids) + ",",
        }
    )
    _post(session, ENDPOINTS["ruler"], data, sfid=meta.sfid)


def update_checkbox(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    checked_ids: list[str],
    othtxt: str = "",
) -> str:
    """Submit checkbox selections. checked_ids is comma-joined list of checked option value_ids."""
    data = _base_data(meta)
    chkstr = "," + ",".join(checked_ids) + "," if checked_ids else ""
    data.update({"qid": qid, "said": said, "txt": chkstr, "othtxt": othtxt})
    result = _post(session, ENDPOINTS["checkbox"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def update_combo(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    option_id: str,
) -> str:
    """Submit dropdown/combo selection."""
    data = _base_data(meta)
    data.update({"qid": qid, "said": said, "qiid": option_id})
    result = _post(session, ENDPOINTS["combo"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def update_date(
    session: requests.Session,
    meta: FormMetadata,
    qid: str,
    said: str,
    date_str: str,
) -> str:
    """Submit date value (format: YYYY/MM/DD)."""
    data = _base_data(meta)
    data.update({"qid": qid, "said": said, "txt": date_str})
    result = _post(session, ENDPOINTS["date"], data, sfid=meta.sfid)
    return str(result.get("said", said))


def submit_form(session: requests.Session, sfid: str) -> bool:
    time.sleep(POST_DELAY_SECONDS)
    headers = {"Referer": f"{BASE_URL}oneEvaluate?sfid={sfid}"}
    resp = session.post(
        BASE_URL + ENDPOINTS["submit"],
        data={"sfid": sfid, "psnt": 100},
        headers=headers,
    )
    resp.raise_for_status()
    result = resp.json()
    return "ok" in result.get("msg", "")
