"""Sysadmin user management: the "Users" tab on /ckan-admin.

CKAN 2.10 spreads user management over /user, /user/edit/<id> and each
organization's members page, and can only grant sysadmin from the CLI. This
page lists every user with their organization roles and lets sysadmins
create, delete/reactivate, (un)make sysadmin and set organization roles.

Writes go through CKAN actions (user_create, user_delete,
organization_member_create/delete) so their validation and activity stream
apply; sysadmin and reactivation have no action in 2.10, so they change the
model directly, as ``ckan sysadmin add`` does.
"""
from __future__ import annotations

from typing import Any

from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.lib.pagination import Page

user_admin = Blueprint("dwr_user_admin", __name__, url_prefix="/ckan-admin/users")

PER_PAGE = 25
STATES = ("active", "pending", "deleted")
ROLES = ("admin", "editor", "member")


@user_admin.before_request
def _check_sysadmin():
    try:
        tk.check_access("sysadmin", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Need to be system administrator to administer"))


def _context() -> dict[str, Any]:
    return {"user": tk.current_user.name}


def _redirect_back(reopen: model.User | None = None):
    """Back to the list, keeping its search, filter and page; ``reopen``
    opens that user's Manage dialog again so the sysadmin can carry on."""
    args = {
        key: tk.request.form.get(key)
        for key in ("q", "state", "page")
        if tk.request.form.get(key)
    }
    if reopen is not None:
        args["open"] = reopen.id
    return tk.redirect_to("dwr_user_admin.index", **args)


def _get_user(user_id: str) -> model.User:
    user = model.User.get(user_id)
    if user is None:
        tk.abort(404, tk._("User not found"))
    return user


def _is_protected(user: model.User) -> str | None:
    """Why this user must not be deleted or demoted, or None."""
    if user.id == tk.current_user.id:
        return tk._("You cannot do this to your own account.")
    if user.name == tk.config.get("ckan.site_id"):
        return tk._("The site user is used by CKAN itself and cannot be changed.")
    return None


def _memberships(user_ids: list[str]) -> dict[str, list[dict[str, str]]]:
    """Active organization memberships per user id, as {id, name, title, role}."""
    rows = (
        model.Session.query(model.Member.table_id, model.Member.capacity, model.Group)
        .join(model.Group, model.Group.id == model.Member.group_id)
        .filter(model.Member.table_name == "user")
        .filter(model.Member.table_id.in_(user_ids))
        .filter(model.Member.state == "active")
        .filter(model.Group.is_organization.is_(True))
        .filter(model.Group.state == "active")
        .order_by(model.Group.title)
    )
    result: dict[str, list[dict[str, str]]] = {}
    for user_id, role, org in rows:
        result.setdefault(user_id, []).append(
            {"id": org.id, "name": org.name, "title": org.title or org.name, "role": role}
        )
    return result


def _organizations() -> list[model.Group]:
    return (
        model.Session.query(model.Group)
        .filter(model.Group.is_organization.is_(True))
        .filter(model.Group.state == "active")
        .order_by(model.Group.title)
        .all()
    )


def index(create_data: dict[str, Any] | None = None, create_errors: dict[str, Any] | None = None):
    """The user list; a POST creates a user (same URL, so the Users tab stays
    highlighted). ``create_data``/``create_errors`` re-open the "Create user"
    dialog with what was typed when user_create rejected it."""
    if tk.request.method == "POST" and create_errors is None:
        return create()
    # values: the list state comes as query args, or as hidden fields on a POST
    params = tk.request.values
    q = params.get("q", "").strip()
    state = params.get("state", "")
    try:
        page_number = max(int(params.get("page", 1)), 1)
    except ValueError:
        page_number = 1

    query = model.Session.query(model.User).filter(
        model.User.name != tk.config.get("ckan.site_id")
    )
    if state in STATES:
        query = query.filter(model.User.state == state)
    if q:
        like = f"%{q}%"
        query = query.filter(
            model.User.name.ilike(like)
            | model.User.fullname.ilike(like)
            | model.User.email.ilike(like)
        )
    count = query.count()
    users = (
        query.order_by(model.User.sysadmin.desc(), model.User.name)
        .offset((page_number - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    def pager_url(q=q, state=state, page=None):
        return tk.h.url_for("dwr_user_admin.index", q=q or None, state=state or None, page=page)

    page = Page(
        collection=users,
        page=page_number,
        url=pager_url,
        item_count=count,
        items_per_page=PER_PAGE,
        presliced_list=True,
    )
    return tk.render(
        "admin/dwr_users.html",
        extra_vars={
            "page": page,
            "users": users,
            "memberships": _memberships([user.id for user in users]),
            "organizations": _organizations(),
            "q": q,
            "state": state,
            "states": STATES,
            "roles": ROLES,
            "count": count,
            "current_user_id": tk.current_user.id,
            "create_data": create_data or {},
            "create_errors": create_errors or {},
            "open_id": params.get("open"),
        },
    )


def create():
    form = tk.request.form
    data = {
        "name": form.get("name", "").strip(),
        "fullname": form.get("fullname", "").strip(),
        "email": form.get("email", "").strip(),
        "password": form.get("password", ""),
    }
    org = form.get("organization")
    role = form.get("role")
    try:
        user = tk.get_action("user_create")(_context(), data)
    except tk.ValidationError as e:
        data.pop("password")
        return index(create_data={**data, "organization": org, "role": role},
                     create_errors=e.error_dict)

    if org and role in ROLES:
        try:
            tk.get_action("organization_member_create")(
                _context(), {"id": org, "username": user["name"], "role": role}
            )
        except (tk.ValidationError, tk.ObjectNotFound) as e:
            tk.h.flash_error(_error_text(e))
            return _redirect_back()
    tk.h.flash_success(tk._("User {name} created.").format(name=user["name"]))
    return _redirect_back()


def sysadmin(user_id: str):
    user = _get_user(user_id)
    reason = _is_protected(user)
    if reason:
        tk.h.flash_error(reason)
        return _redirect_back(user)
    user.sysadmin = tk.asbool(tk.request.form.get("sysadmin"))
    model.repo.commit()
    if user.sysadmin:
        tk.h.flash_success(tk._("{name} is now a sysadmin.").format(name=user.name))
    else:
        tk.h.flash_success(tk._("{name} is no longer a sysadmin.").format(name=user.name))
    return _redirect_back(user)


def delete(user_id: str):
    user = _get_user(user_id)
    reason = _is_protected(user)
    if reason:
        tk.h.flash_error(reason)
        return _redirect_back()
    tk.get_action("user_delete")(_context(), {"id": user.id})
    tk.h.flash_success(tk._("User {name} deleted.").format(name=user.name))
    return _redirect_back()


def reactivate(user_id: str):
    user = _get_user(user_id)
    user.state = model.State.ACTIVE
    model.repo.commit()
    # user_delete also removed their memberships; those are not restored
    tk.h.flash_success(
        tk._(
            "User {name} is active again. Add them back to their organizations if needed."
        ).format(name=user.name)
    )
    return _redirect_back()


def membership(user_id: str):
    """Add or change (role) one organization membership, or remove it ("remove")."""
    user = _get_user(user_id)
    org = tk.request.form.get("organization")
    role = None if tk.request.form.get("remove") else tk.request.form.get("role")
    if not org:
        tk.h.flash_error(tk._("Choose an organization."))
        return _redirect_back(user)
    try:
        if role in ROLES:
            tk.get_action("organization_member_create")(
                _context(), {"id": org, "username": user.name, "role": role}
            )
            tk.h.flash_success(tk._("Role saved for {name}.").format(name=user.name))
        else:
            tk.get_action("organization_member_delete")(
                _context(), {"id": org, "username": user.name}
            )
            tk.h.flash_success(
                tk._("{name} removed from the organization.").format(name=user.name)
            )
    except (tk.ValidationError, tk.ObjectNotFound) as e:
        tk.h.flash_error(_error_text(e))
    return _redirect_back(user)


def _error_text(error: Exception) -> str:
    if isinstance(error, tk.ValidationError):
        return "; ".join(
            f"{field}: {', '.join(map(str, messages)) if isinstance(messages, list) else messages}"
            for field, messages in error.error_dict.items()
        )
    return str(error) or tk._("Not found")


user_admin.add_url_rule("/", view_func=index, endpoint="index", methods=["GET", "POST"])
user_admin.add_url_rule("/<user_id>/sysadmin", view_func=sysadmin, methods=["POST"])
user_admin.add_url_rule("/<user_id>/delete", view_func=delete, methods=["POST"])
user_admin.add_url_rule("/<user_id>/reactivate", view_func=reactivate, methods=["POST"])
user_admin.add_url_rule("/<user_id>/membership", view_func=membership, methods=["POST"])
