from __future__ import annotations

import sys
from pathlib import Path

import yaml

_CONFIG_FILE = Path("local_config.yaml")
_EXAMPLE_FILE = Path("local_config.example.yaml")


def _load_local_config() -> dict:
    if _CONFIG_FILE.exists():
        with _CONFIG_FILE.open() as f:
            return yaml.safe_load(f) or {}
    print(
        f"ERROR: {_CONFIG_FILE} not found.\n"
        f"Copy {_EXAMPLE_FILE} to {_CONFIG_FILE} and fill in your hospital's details.",
        file=sys.stderr,
    )
    sys.exit(1)


_cfg = _load_local_config()

BASE_URL: str = _cfg["base_url"]
COOKIE_DOMAIN: str = _cfg["cookie_domain"]

ENDPOINTS = {
    "listing": "Evaluate",
    "form": "oneEvaluate",
    "radio": "updRadioStuformAjax",
    "text": "updTextStuformAjax",
    "textarea": "updText2StuformAjax",
    "ruler": "updRuler2StuformAjax",
    "checkbox": "updCheckboxStuformAjax",
    "combo": "updComboStuformAjax",
    "date": "updDateStuformAjax",
    "ruler_group": "updRulerGroupStuformAjax",
    "done": "updDoneStuformAjax",
    "sign": "updSignEvaluateAjax",
    "sign_all": "signallEvaluateAjax",
    "submit": "EvaluateAjax",
}

DEFAULT_RULER_SCORE = 8
POST_DELAY_SECONDS = 0.5
