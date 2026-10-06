from __future__ import annotations

import datetime
import logging
import re
from typing import Any, Callable

import ckan.plugins.toolkit as tk
from ckan.lib.search import SearchError

log = logging.getLogger(__name__)

DEFAULT_PRIMARY_COLOR = "#0a5cc2"
_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


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


# Look and feel


def dwr_theme_primary_color() -> str:
    """Configured brand colour, or the default if it is not a valid hex colour.

    The value is injected into a <style> tag, so it must be validated.
    """
    color = (tk.config.get("ckanext.dwr_theme.primary_color") or "").strip()
    if _HEX_COLOR.match(color):
        return color.lower()
    if color:
        log.warning("Invalid ckanext.dwr_theme.primary_color %r, using default", color)
    return DEFAULT_PRIMARY_COLOR


def _hex_to_rgb(color: str) -> list[int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return [int(value[i:i + 2], 16) for i in (0, 2, 4)]


def _mix(color: str, other: str, weight: float) -> str:
    """Blend ``weight`` (0..1) of ``other`` into ``color``."""
    return "#" + "".join(
        f"{round(a + (b - a) * weight):02x}"
        for a, b in zip(_hex_to_rgb(color), _hex_to_rgb(other))
    )


def dwr_theme_palette() -> dict[str, str]:
    primary = dwr_theme_primary_color()
    return {
        "primary": primary,
        "dark": _mix(primary, "#000000", 0.25),
        "soft": _mix(primary, "#ffffff", 0.9),
    }


def dwr_theme_web_fonts() -> bool:
    return tk.asbool(tk.config.get("ckanext.dwr_theme.web_fonts"))


def dwr_theme_hero() -> dict[str, str]:
    """Hero texts from config; empty values fall back to site settings in the template."""
    return {
        "title": tk.config.get("ckanext.dwr_theme.hero_title") or "",
        "subtitle": tk.config.get("ckanext.dwr_theme.hero_subtitle") or "",
        "image": tk.config.get("ckanext.dwr_theme.hero_image") or "",
    }


def dwr_theme_current_year() -> int:
    return datetime.date.today().year


# Homepage content


def dwr_theme_recent_datasets(limit: int | None = None) -> list[dict[str, Any]]:
    if limit is None:
        limit = tk.config.get("ckanext.dwr_theme.home_datasets")
    try:
        result = tk.get_action("package_search")(
            {}, {"rows": limit, "sort": "metadata_modified desc"}
        )
    except SearchError:
        log.warning("Search index unavailable, cannot list recent datasets")
        return []
    return result["results"]


def dwr_theme_popular_tags(limit: int = 6) -> list[dict[str, Any]]:
    try:
        result = tk.get_action("package_search")(
            {}, {"rows": 0, "facet.field": ["tags"], "facet.limit": limit}
        )
    except SearchError:
        log.warning("Search index unavailable, cannot list popular tags")
        return []
    items = result["search_facets"].get("tags", {}).get("items", [])
    return sorted(items, key=lambda item: item["count"], reverse=True)[:limit]


def dwr_theme_featured_organizations(limit: int | None = None) -> list[dict[str, Any]]:
    if limit is None:
        limit = tk.config.get("ckanext.dwr_theme.home_organizations")
    try:
        return tk.get_action("organization_list")(
            {}, {"all_fields": True, "sort": "package_count desc", "limit": limit}
        )
    except SearchError:
        log.warning("Search index unavailable, cannot list organizations")
        return []


def dwr_theme_initials(name: str) -> str:
    """Up to two initials for an avatar placeholder, e.g. "Water Resources" -> "WR"."""
    words = [word for word in (name or "").split() if word]
    return "".join(word[0] for word in words[:2]).upper() or "?"


def get_helpers() -> dict[str, Callable[..., Any]]:
    return {
        "dwr_theme_greeting": dwr_theme_greeting,
        "dwr_theme_show_dataset_count": dwr_theme_show_dataset_count,
        "dwr_theme_dataset_count": dwr_theme_dataset_count,
        "dwr_theme_primary_color": dwr_theme_primary_color,
        "dwr_theme_palette": dwr_theme_palette,
        "dwr_theme_web_fonts": dwr_theme_web_fonts,
        "dwr_theme_hero": dwr_theme_hero,
        "dwr_theme_current_year": dwr_theme_current_year,
        "dwr_theme_recent_datasets": dwr_theme_recent_datasets,
        "dwr_theme_popular_tags": dwr_theme_popular_tags,
        "dwr_theme_featured_organizations": dwr_theme_featured_organizations,
        "dwr_theme_initials": dwr_theme_initials,
    }
