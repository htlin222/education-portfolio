from __future__ import annotations

import re

from bs4 import BeautifulSoup

import requests

from evalbot.models import EvalListing
from evalbot.session import get


def fetch_pending(session: requests.Session) -> list[EvalListing]:
    resp = get(session, "Evaluate")
    resp.raise_for_status()
    return parse_listing_html(resp.text)


def parse_listing_html(html: str) -> list[EvalListing]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[EvalListing] = []

    table = soup.find("table", class_="table")
    if not table:
        return results

    tbody = table.find("tbody")
    rows = (tbody if tbody else table).find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        link = cells[3].find("a", href=True)
        if not link:
            continue

        href = link["href"]
        m = re.search(r"sfid=(\d+)", href)
        if not m:
            continue

        results.append(
            EvalListing(
                sfid=m.group(1),
                student_name=cells[1].get_text(strip=True),
                passport_name=cells[2].get_text(strip=True),
                form_name=link.get_text(strip=True),
            )
        )

    return results
