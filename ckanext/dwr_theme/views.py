from __future__ import annotations

from flask import Blueprint

import ckan.plugins.toolkit as tk

from ckanext.dwr_theme.helpers import HOME_GROUP_KINDS, dwr_theme_home_groups
from ckanext.dwr_theme.user_admin import user_admin

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


def home_cards(kind: str):
    """Next page of homepage organization/group cards, for the "Load more" button."""
    if kind not in HOME_GROUP_KINDS:
        return tk.abort(404)
    try:
        offset = max(int(tk.request.args.get("offset", 0)), 0)
    except ValueError:
        return tk.abort(400, tk._("Invalid offset"))
    page = dwr_theme_home_groups(kind, offset)
    html = tk.render(
        "dwr_theme/snippets/group_cards.html", extra_vars={"groups": page["results"]}
    )
    return {"html": html, "next_offset": page["next_offset"], "total": page["total"]}


dwr_theme.add_url_rule("/dwr-theme", view_func=index, methods=["GET", "POST"])
dwr_theme.add_url_rule("/privacy-policy", view_func=privacy_policy)
dwr_theme.add_url_rule("/dwr-theme/home/<kind>", view_func=home_cards)


def get_blueprints():
    return [dwr_theme, user_admin]
