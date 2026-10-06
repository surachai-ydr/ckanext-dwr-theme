from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan.types import Schema


def dwr_theme_hello() -> Schema:
    not_empty = tk.get_validator("not_empty")
    unicode_safe = tk.get_validator("unicode_safe")
    dwr_theme_no_digits = tk.get_validator("dwr_theme_no_digits")

    return {
        "name": [not_empty, unicode_safe, dwr_theme_no_digits],
    }
