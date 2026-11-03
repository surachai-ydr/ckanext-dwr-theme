from __future__ import annotations

from typing import Any

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as tk
from ckan.types import Context, DataDict

from ckanext.dwr_theme.logic import schema


@tk.side_effect_free
def dwr_theme_hello(context: Context, data_dict: DataDict) -> dict[str, Any]:
    """Return a greeting for ``name``.

    :param name: who to greet (no digits allowed)
    :type name: string
    :rtype: dictionary with a ``message`` key
    """
    tk.check_access("dwr_theme_hello", context, data_dict)

    data, errors = tk.navl_validate(data_dict, schema.dwr_theme_hello(), context)
    if errors:
        raise tk.ValidationError(errors)

    greeting = tk.config.get("ckanext.dwr_theme.greeting")
    return {"message": f"{greeting}, {data['name']}!"}


HERO_LOGO = "ckanext.dwr_theme.hero_logo"
HERO_LOGO_UPLOAD = "hero_logo_upload"
HERO_LOGO_CLEAR = "clear_hero_logo_upload"


@tk.chained_action
def config_option_update(
    next_action: Any, context: Context, data_dict: DataDict
) -> dict[str, Any]:
    """Store an uploaded homepage hero logo, like core does for the site logo.

    Core only handles the ``ckan.site_logo`` upload, so the file is saved here
    and the option is set to its public ``/uploads/admin/...`` URL (built the
    same way as core's, so it honours ``ckan.root_path``).
    """
    if HERO_LOGO in data_dict or HERO_LOGO_UPLOAD in data_dict:
        tk.check_access("config_option_update", context, data_dict)
        upload = uploader.get_uploader("admin")
        upload.update_data_dict(data_dict, HERO_LOGO, HERO_LOGO_UPLOAD, HERO_LOGO_CLEAR)
        upload.upload(uploader.get_max_image_size())

        value = data_dict.get(HERO_LOGO) or ""
        if value and not value.startswith(("http", "/")):
            data_dict[HERO_LOGO] = tk.h.url_for_static(f"uploads/admin/{value}")

    data_dict.pop(HERO_LOGO_UPLOAD, None)
    data_dict.pop(HERO_LOGO_CLEAR, None)
    return next_action(context, data_dict)


def get_actions():
    return {
        "dwr_theme_hello": dwr_theme_hello,
        "config_option_update": config_option_update,
    }
