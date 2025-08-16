"""
AI Daily App - ./constants/constants.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains constants used throughout the AI Daily App.
You may modify these values to configure app behavior, directories, categories. etc.

Usage:
    from AIDaily import constants
    print(constants.CATEGORIES)
"""

import json
import os
from pathlib import Path

# ---------------------------
# Base paths
# ---------------------------
# Use environment variable for data directory with fallback to default
DATA_DIR = Path(os.getenv('DATA_DIR', './data')).resolve()
PAPER_DIR = DATA_DIR / 'papers'
INDEX_PATH = DATA_DIR / 'index.json'
ROTATION_FILE = DATA_DIR / 'rotation.txt'

# ---------------------------
# Ensure directories exist
# ---------------------------
DATA_DIR.mkdir(parents=True, exist_ok=True)
PAPER_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------
# Ensure index.json exists
# ---------------------------
if not INDEX_PATH.exists():
	INDEX_PATH.write_text(json.dumps({}, indent=2), encoding='utf-8')

# ---------------------------
# Ensure rotation.txt exists
# ---------------------------
if not ROTATION_FILE.exists():
	ROTATION_FILE.write_text('0', encoding='utf-8')

# ---------------------------
# External API
# ---------------------------
ARXIV_API = 'https://export.arxiv.org/api/query'

# ---------------------------
# Categories to fetch papers from
# ---------------------------
CATEGORIES = [
	'cat:cs.AI',  # Artificial Intelligence
	'cat:cs.LG',  # Machine Learning
	'cat:cs.CL',  # Natural Language Processing
	'cat:cs.CV',  # Computer Vision
]
