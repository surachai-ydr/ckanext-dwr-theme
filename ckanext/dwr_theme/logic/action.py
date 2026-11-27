from __future__ import annotations

from typing import Any

import ckan.lib.uploader as uploader
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.types import Context, DataDict
from flask import has_request_context

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
            url = _save_image(file, upload_field)
            if url:
                data_dict[option] = url

    return next_action(context, data_dict)


def _save_image(file: Any, upload_field: str) -> str:
    """Save an uploaded image like core does for the site logo; returns its URL or ''.

    The file goes to <ckan.storage_path>/storage/uploads/admin/ (the name gets
    a timestamp prefix, so uploads never overwrite each other). Errors such as
    a file that is not an image are raised keyed by ``upload_field``.
    """
    upload = uploader.get_uploader("admin")
    upload.update_data_dict({upload_field: file}, "url", upload_field, "clear")
    upload.upload(uploader.get_max_image_size())
    return tk.h.url_for_static(f"uploads/admin/{upload.filename}") if upload.filename else ""


# Fields this theme adds to thai_gdc's popup form (templates/admin/popup.html)
IMAGE_ONLY_FIELD = "DWR_IMAGE_ONLY"
IMAGES_FIELD = "DWR_IMAGES"
IMAGES_UPLOAD_FIELD = "DWR_IMAGES_UPLOAD"


@tk.chained_action
def popup_update_conf_group(
    next_action: Any, context: Context, data_dict: DataDict
) -> Any:
    """Also save this theme's fields from thai_gdc's popup page.

    thai_gdc's view only passes its own EVENT_* fields on, so the "image only"
    choice and the extra slideshow images are read from the submitted form
    and stored as CKAN config options. Uploaded images are appended to the
    listed ones.

    EVENT_TEXT (the link's label) is optional here, but thai_gdc's schema
    requires it, so an empty one is stored as a space; readers strip it.
    """
    fields = data_dict.get("fields")
    if isinstance(fields, dict) and not (fields.get("EVENT_TEXT") or "").strip():
        fields["EVENT_TEXT"] = " "
    result = next_action(context, data_dict)
    if data_dict.get("conf_group") != "EVENT" or not has_request_context():
        return result
    form, files = tk.request.form, tk.request.files
    if IMAGE_ONLY_FIELD not in form:
        # Not submitted from this theme's version of the form
        return result

    images = form.get(IMAGES_FIELD, "").split()
    for file in files.getlist(IMAGES_UPLOAD_FIELD):
        if getattr(file, "filename", None):
            url = _save_image(file, IMAGES_UPLOAD_FIELD)
            if url:
                images.append(url)
    tk.get_action("config_option_update")(
        {"user": context.get("user")},
        {
            "ckanext.dwr_theme.home_modal_image_only": "true" if tk.asbool(form[IMAGE_ONLY_FIELD]) else "false",
            "ckanext.dwr_theme.home_modal_images": "\n".join(images),
        },
    )
    return result


def get_actions():
    actions = {
        "dwr_theme_hello": dwr_theme_hello,
        "config_option_update": config_option_update,
    }
    # Chaining an action that does not exist fails, so only with thai_gdc
    if plugins.plugin_loaded("thai_gdc"):
        actions["popup_update_conf_group"] = popup_update_conf_group
    return actions
