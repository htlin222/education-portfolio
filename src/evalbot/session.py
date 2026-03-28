from __future__ import annotations

import json
from http.cookiejar import Cookie
from pathlib import Path

import requests

from evalbot.config import BASE_URL, COOKIE_DOMAIN


class SessionExpiredError(Exception):
    pass


def resolve_cookies_path(cookies_arg: str = "cookies.json", user: str | None = None) -> Path:
    """Resolve cookies file: --user takes priority, then --cookies, then profiles/default."""
    if user:
        p = Path("profiles") / user / "cookies.json"
        if p.exists():
            return p
        raise FileNotFoundError(f"Profile 不存在: {p}")

    # If explicit --cookies was passed and exists, use it
    explicit = Path(cookies_arg)
    if explicit.exists():
        return explicit

    # Fallback to profiles/default
    default_profile = Path("profiles/default/cookies.json")
    if default_profile.exists():
        return default_profile

    raise FileNotFoundError(
        f"找不到 cookies: 嘗試了 {explicit} 與 {default_profile}\n"
        "請將 cookies.json 放在 profiles/default/ 或用 --user 指定 profile"
    )


def load_session(cookies_path: str = "cookies.json", user: str | None = None) -> requests.Session:
    path = resolve_cookies_path(cookies_path, user)
    with path.open() as f:
        raw_cookies = json.load(f)

    session = requests.Session()

    for c in raw_cookies:
        if COOKIE_DOMAIN not in c.get("domain", ""):
            continue
        cookie = Cookie(
            version=0,
            name=c["name"],
            value=c["value"],
            port=None,
            port_specified=False,
            domain=c["domain"],
            domain_specified=True,
            domain_initial_dot=c["domain"].startswith("."),
            path=c.get("path", "/"),
            path_specified=True,
            secure=c.get("secure", False),
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": str(c.get("httpOnly", False))},
        )
        session.cookies.set_cookie(cookie)

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
    )

    return session


def validate_session(session: requests.Session) -> bool:
    resp = session.get(BASE_URL + "Evaluate", allow_redirects=False)
    if resp.status_code == 302 or "login" in resp.text.lower():
        raise SessionExpiredError(
            "Session 已過期，請重新從瀏覽器匯出 cookies.json"
        )
    if resp.status_code != 200:
        raise SessionExpiredError(f"無法連線，HTTP {resp.status_code}")
    return True


def get(session: requests.Session, path: str, **kwargs) -> requests.Response:
    return session.get(BASE_URL + path, **kwargs)


def post(session: requests.Session, path: str, data: dict) -> dict:
    resp = session.post(BASE_URL + path, data=data)
    resp.raise_for_status()
    return resp.json()
