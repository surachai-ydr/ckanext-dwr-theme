from __future__ import annotations

from typing import Any, Callable

import ckan.plugins.toolkit as tk


def dwr_theme_no_digits(value: Any) -> Any:
    if any(char.isdigit() for char in value):
        raise tk.Invalid(tk._("Must not contain digits"))
    return value


def get_validators() -> dict[str, Callable[..., Any]]:
    return {
        "dwr_theme_no_digits": dwr_theme_no_digits,
    }
