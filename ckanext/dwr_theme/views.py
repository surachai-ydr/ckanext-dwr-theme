from __future__ import annotations

from flask import Blueprint

import ckan.plugins.toolkit as tk

dwr_theme = Blueprint("dwr_theme", __name__)


def index():
    data = {}
    errors = {}
    message = None

    if tk.request.method == "POST":
        data = {"name": tk.request.form.get("name", "")}
        try:
            result = tk.get_action("dwr_theme_hello")({}, data)
            message = result["message"]
        except tk.ValidationError as e:
            errors = e.error_dict

    return tk.render(
        "dwr_theme/index.html",
        extra_vars={"data": data, "errors": errors, "message": message},
    )


def privacy_policy():
    return tk.render("dwr_theme/privacy_policy.html")


dwr_theme.add_url_rule("/dwr-theme", view_func=index, methods=["GET", "POST"])
dwr_theme.add_url_rule("/privacy-policy", view_func=privacy_policy)


def get_blueprints():
    return [dwr_theme]
