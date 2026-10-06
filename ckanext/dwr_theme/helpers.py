from __future__ import annotations

import logging
from typing import Any, Callable

import ckan.plugins.toolkit as tk
from ckan.lib.search import SearchError

log = logging.getLogger(__name__)


def dwr_theme_greeting() -> str:
    """Greeting prefix configured via ``ckanext.dwr_theme.greeting``."""
    return tk.config.get("ckanext.dwr_theme.greeting")


def dwr_theme_show_dataset_count() -> bool:
    return tk.asbool(tk.config.get("ckanext.dwr_theme.show_dataset_count"))


def dwr_theme_dataset_count() -> int:
    """Total number of public datasets, or 0 if the search index is down."""
    try:
        result = tk.get_action("package_search")({}, {"rows": 0})
    except SearchError:
        log.warning("Search index unavailable, cannot count datasets")
        return 0
    return result["count"]


def get_helpers() -> dict[str, Callable[..., Any]]:
    return {
        "dwr_theme_greeting": dwr_theme_greeting,
        "dwr_theme_show_dataset_count": dwr_theme_show_dataset_count,
        "dwr_theme_dataset_count": dwr_theme_dataset_count,
    }
