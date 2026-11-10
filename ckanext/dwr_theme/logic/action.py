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


# Image options editable on /ckan-admin/config, as
# {option: (file upload field, "remove" checkbox field)}
LOGO_FIELDS = {
    f"ckanext.dwr_theme.{name}": (f"{name}_upload", f"clear_{name}_upload")
    for name in ("hero_logo", "hero_image", "footer_logo")
}


@tk.chained_action
def config_option_update(
    next_action: Any, context: Context, data_dict: DataDict
) -> dict[str, Any]:
    """Store uploaded theme images (logos, hero background), like core does for the site logo.

    Core only handles the ``ckan.site_logo`` upload, so the files are saved
    here and each option is set to its public ``/uploads/admin/...`` URL (built
    the same way as core's, so it honours ``ckan.root_path``).
    """
    for option, (upload_field, clear_field) in LOGO_FIELDS.items():
        file = data_dict.pop(upload_field, None)
        clear = tk.asbool(data_dict.pop(clear_field, False))

        if clear:
            data_dict[option] = ""
        elif getattr(file, "filename", None):
            tk.check_access("config_option_update", context, data_dict)
            upload = uploader.get_uploader("admin")
            # Saves to <ckan.storage_path>/storage/uploads/admin/; errors are
            # keyed by upload_field (e.g. a file that is not an image)
            upload.update_data_dict({upload_field: file}, option, upload_field, clear_field)
            upload.upload(uploader.get_max_image_size())
            if upload.filename:
                data_dict[option] = tk.h.url_for_static(f"uploads/admin/{upload.filename}")

    return next_action(context, data_dict)


def get_actions():
    return {
        "dwr_theme_hello": dwr_theme_hello,
        "config_option_update": config_option_update,
    }
