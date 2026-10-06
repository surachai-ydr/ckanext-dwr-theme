from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan.types import AuthResult, Context, DataDict


@tk.auth_allow_anonymous_access
def dwr_theme_hello(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": True}


def get_auth_functions():
    return {
        "dwr_theme_hello": dwr_theme_hello,
    }
