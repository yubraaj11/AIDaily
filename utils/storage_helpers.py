"""
AI Daily App - utils/storage_helpers.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains functions used to load and store index used to check unique papers everyday.

Usage:
    from utils import load_index, save_index, norm
"""
import re
from typing import Dict, Any
import json

from AIDaily.constants import INDEX_PATH

def load_index() -> Dict[str, Any]:
    try:
        return json.loads(INDEX_PATH.read_text())
    except json.decoder.JSONDecodeError as jde:
        return {"Error": str(jde)}


def save_index(idx: Dict[str, Any]) -> None:
    INDEX_PATH.write_text(json.dumps(idx, indent=2))


def norm(s: str) -> str:
    return re.sub(r'[^a-zA-Z0-9._-]', '_', s).lower()