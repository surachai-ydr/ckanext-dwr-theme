from __future__ import annotations

from typing import Any

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


def get_actions():
    return {
        "dwr_theme_hello": dwr_theme_hello,
    }
