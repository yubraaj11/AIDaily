"""
AI Daily App - utils/category_shuffler
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains function to shuffle the categories for uniqueness.

Usage:
    from utils import next_category
"""

from AIDaily.constants import CATEGORIES, ROTATION_FILE


def next_category() -> str:
	idx = int(ROTATION_FILE.read_text().strip())
	category = CATEGORIES[idx % len(CATEGORIES)]
	ROTATION_FILE.write_text(str((idx + 1) % len(CATEGORIES)))
	return category
