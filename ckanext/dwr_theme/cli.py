from __future__ import annotations

import click

import ckan.plugins.toolkit as tk


@click.group(name="dwr-theme", short_help="ckanext-dwr-theme CLI commands.")
def dwr_theme():
    pass


@dwr_theme.command()
@click.argument("name", default="World")
def hello(name: str):
    """Print a greeting using the dwr_theme_hello action."""
    try:
        result = tk.get_action("dwr_theme_hello")({"ignore_auth": True}, {"name": name})
    except tk.ValidationError as e:
        tk.error_shout(e.error_dict)
        raise click.Abort()
    click.secho(result["message"], fg="green")


def get_commands():
    return [dwr_theme]
