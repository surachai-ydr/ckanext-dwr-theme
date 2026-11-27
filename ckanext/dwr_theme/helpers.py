from __future__ import annotations

import datetime
import hashlib
import logging
import re
from importlib import metadata
from typing import Any, Callable

import ckan.plugins as plugins
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


CKAN_DEFAULT_FAVICON = "/base/images/ckan.ico"
DEFAULT_FAVICON = "/favicon.ico"


def dwr_theme_favicon() -> str:
    """``ckan.favicon`` if a sysadmin set one, else the theme's public/favicon.ico."""
    favicon = (tk.config.get("ckan.favicon") or "").strip()
    if favicon and favicon != CKAN_DEFAULT_FAVICON:
        return favicon
    return DEFAULT_FAVICON


def dwr_theme_web_fonts() -> bool:
    return tk.asbool(tk.config.get("ckanext.dwr_theme.web_fonts"))


# Languages whose texts can be edited on /ckan-admin/config
LANGUAGES = ("th", "en")


def _localized(option: str) -> str:
    """``<option>_<lang>`` for the current language, else ``<option>``.

    The per-language options are set by sysadmins on /ckan-admin/config.
    """
    lang = (tk.h.lang() or "").split("_")[0]
    for key in (f"ckanext.dwr_theme.{option}_{lang}", f"ckanext.dwr_theme.{option}"):
        value = (tk.config.get(key) or "").strip()
        if value:
            return value
    return ""


def dwr_theme_hero() -> dict[str, str]:
    """Hero texts from config; empty values fall back to translated defaults in the template."""
    return {
        "title": _localized("hero_title"),
        "subtitle": _localized("hero_subtitle"),
        "image": (tk.config.get("ckanext.dwr_theme.hero_image") or "").strip(),
        "logo": (tk.config.get("ckanext.dwr_theme.hero_logo") or "").strip(),
    }


def dwr_theme_footer() -> dict[str, str]:
    """Footer name and logo from config; the name falls back to the site title."""
    return {
        "name": _localized("footer_name") or tk.config.get("ckan.site_title") or "",
        "logo": (tk.config.get("ckanext.dwr_theme.footer_logo") or "").strip(),
    }


# Thai readers expect years in the Buddhist Era (B.E. = C.E. + 543)
BUDDHIST_ERA_OFFSET = 543
_YEAR = re.compile(r"(?<!\d)\d{4}(?!\d)")


def _is_thai() -> bool:
    return (tk.h.lang() or "").split("_")[0] == "th"


def to_buddhist_era(text: str) -> str:
    """Convert the C.E. years in a formatted date to B.E., e.g.
    "20 พฤศจิกายน ค.ศ. 2026" -> "20 พฤศจิกายน พ.ศ. 2569"."""
    text = text.replace("ค.ศ.", "พ.ศ.")
    return _YEAR.sub(lambda match: str(int(match.group()) + BUDDHIST_ERA_OFFSET), text)


@tk.chained_helper
def render_datetime(next_helper: Callable[..., str], *args: Any, **kwargs: Any) -> str:
    """Core ``render_datetime``, with Buddhist Era years when the language is Thai.

    An explicit ``date_format`` asks for a fixed (often machine) format, so it is left alone.
    """
    rendered = next_helper(*args, **kwargs)
    has_format = len(args) > 1 and args[1] or kwargs.get("date_format")
    if rendered and not has_format and _is_thai():
        return to_buddhist_era(rendered)
    return rendered


def dwr_theme_current_year() -> int:
    year = datetime.date.today().year
    return year + BUDDHIST_ERA_OFFSET if _is_thai() else year


def dwr_theme_privacy_policy_url() -> str:
    """Configured external privacy policy, or the built-in page."""
    return (tk.config.get("ckanext.dwr_theme.privacy_policy_url") or "").strip() or tk.url_for(
        "dwr_theme.privacy_policy"
    )


# Homepage content


def _gdc_event_popup() -> dict[str, str] | None:
    """thai_gdc's popup (Sysadmin settings -> ป็อปอัพ), when published with an image.

    thai_gdc renders it from its own home/index.html, which this theme's
    homepage replaces, so it is shown through the dwr dialog instead.
    """
    if not dwr_theme_gdc_enabled():
        return None
    conf = tk.h.thai_gdc_get_conf_group("EVENT") or {}
    image = (conf.get("EVENT_IMAGE") or "").strip()
    if conf.get("EVENT_PUBLIC") != "True" or not image:
        return None
    return {
        "image": image,
        "link_url": (conf.get("EVENT_URL") or "").strip(),
        "link_text": (conf.get("EVENT_TEXT") or "").strip(),
        "no_text": "true",
    }


def dwr_theme_home_modal_images() -> list[str]:
    """Extra slideshow images (``ckanext.dwr_theme.home_modal_images``), one URL per line."""
    return (tk.config.get("ckanext.dwr_theme.home_modal_images") or "").split()


def dwr_theme_home_modal_image_only() -> bool:
    """``ckanext.dwr_theme.home_modal_image_only``; empty (never saved) counts as off."""
    return tk.asbool(tk.config.get("ckanext.dwr_theme.home_modal_image_only") or False)


def dwr_theme_home_modal() -> dict[str, Any] | None:
    """Homepage dialog settings, or None when there is nothing to show.

    thai_gdc's popup (edited on /ckan-admin/popup-edit) wins when published;
    otherwise ``ckanext.dwr_theme.home_modal`` and its options are used.
    ``images`` is the main image followed by
    ``ckanext.dwr_theme.home_modal_images``, shown as a slideshow when there
    are several. ``image_only`` (``ckanext.dwr_theme.home_modal_image_only``,
    needs an image) shows just the images, near full screen. Empty title/text
    fall back to translated defaults in the template. ``key`` changes whenever the
    content does, so a visitor's "Don't show this again" only applies to the
    content they dismissed.
    """
    modal = _gdc_event_popup()
    if modal is None:
        if not tk.asbool(tk.config.get("ckanext.dwr_theme.home_modal")):
            return None
        modal = {
            field: (tk.config.get(f"ckanext.dwr_theme.home_modal_{field}") or "").strip()
            for field in ("title", "text", "image", "link_url", "link_text")
        }
    images = [modal.pop("image")] + dwr_theme_home_modal_images()
    modal["images"] = list(dict.fromkeys(image for image in images if image))
    if modal["images"] and dwr_theme_home_modal_image_only():
        modal["image_only"] = "true"
    content = "\n".join(
        "\n".join(value) if isinstance(value, list) else value
        for _field, value in sorted(modal.items())
    )
    modal["key"] = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return modal


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


HOME_GROUP_KINDS = ("organization", "group")


def dwr_theme_home_groups(kind: str, offset: int = 0) -> dict[str, Any]:
    """One page of the homepage organization or group cards, most datasets first.

    kind is "organization" or "group". Returns {"results": [...], "total": n,
    "next_offset": offset of the next page, or None on the last page}.

    Sorted here rather than with sort="package_count desc", which leaves out
    groups that have no datasets yet and can't page past
    ckan.group_and_organization_list_all_fields_max.
    """
    is_org = kind == "organization"
    list_action = tk.get_action(f"{kind}_list")
    limit = tk.config.get(
        "ckanext.dwr_theme.home_organizations" if is_org else "ckanext.dwr_theme.home_groups"
    )
    facet = "organization" if is_org else "groups"
    empty = {"results": [], "total": 0, "next_offset": None}
    try:
        names = list_action({}, {})
        facets = tk.get_action("package_search")(
            {}, {"rows": 0, "facet.field": [facet], "facet.limit": -1}
        )["search_facets"]
    except SearchError:
        log.warning("Search index unavailable, cannot list %ss", kind)
        return empty
    counts = {item["name"]: item["count"] for item in facets.get(facet, {}).get("items", [])}
    # names come in title order, which the stable sort keeps for equal counts.
    names.sort(key=lambda name: counts.get(name, 0), reverse=True)

    page = names[offset:offset + limit]
    if not page:
        return {**empty, "total": len(names)}
    results = list_action(
        {}, {"all_fields": True, "organizations" if is_org else "groups": page}
    )
    results.sort(key=lambda group: page.index(group["name"]))
    end = offset + len(page)
    return {
        "results": results,
        "total": len(names),
        "next_offset": end if end < len(names) else None,
    }


def dwr_theme_version() -> str:
    """Installed version of this extension (setup.cfg's version), e.g. "0.0.1"."""
    try:
        return metadata.version("ckanext-dwr-theme")
    except metadata.PackageNotFoundError:
        return ""


def dwr_theme_gdc_enabled() -> bool:
    """True when ckanext-thai_gdc is loaded, so templates can use its helpers."""
    return plugins.plugin_loaded("thai_gdc")


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
        "dwr_theme_favicon": dwr_theme_favicon,
        "dwr_theme_web_fonts": dwr_theme_web_fonts,
        "dwr_theme_hero": dwr_theme_hero,
        "dwr_theme_footer": dwr_theme_footer,
        "dwr_theme_current_year": dwr_theme_current_year,
        "dwr_theme_privacy_policy_url": dwr_theme_privacy_policy_url,
        "dwr_theme_home_modal": dwr_theme_home_modal,
        "dwr_theme_home_modal_image_only": dwr_theme_home_modal_image_only,
        "dwr_theme_home_modal_images": dwr_theme_home_modal_images,
        "dwr_theme_recent_datasets": dwr_theme_recent_datasets,
        "dwr_theme_popular_tags": dwr_theme_popular_tags,
        "dwr_theme_home_groups": dwr_theme_home_groups,
        "dwr_theme_initials": dwr_theme_initials,
        "dwr_theme_gdc_enabled": dwr_theme_gdc_enabled,
        "dwr_theme_version": dwr_theme_version,
        "render_datetime": render_datetime,
    }
