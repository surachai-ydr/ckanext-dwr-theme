from __future__ import annotations

from typing import Any

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.lib.plugins import DefaultTranslation

from ckanext.dwr_theme import cli, helpers, views
from ckanext.dwr_theme.logic import action, auth, validators


# Loads the options declared in config_declaration.yaml (CKAN 2.10+)
@tk.blanket.config_declarations
class DwrThemePlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config_: Any):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "dwr-theme")

    def update_config_schema(self, schema: dict[str, Any]):
        # Lets sysadmins edit the homepage hero texts on /ckan-admin/config
        ignore_missing = tk.get_validator("ignore_missing")
        unicode_safe = tk.get_validator("unicode_safe")
        for field in ("title", "subtitle"):
            for lang in helpers.HERO_LANGUAGES:
                schema[f"ckanext.dwr_theme.hero_{field}_{lang}"] = [ignore_missing, unicode_safe]
        # The upload/clear fields are consumed by the chained config_option_update
        for key in (action.HERO_LOGO, action.HERO_LOGO_UPLOAD, action.HERO_LOGO_CLEAR):
            schema[key] = [ignore_missing, unicode_safe]
        return schema

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IBlueprint

    def get_blueprint(self):
        return views.get_blueprints()

    # IActions

    def get_actions(self):
        return action.get_actions()

    # IAuthFunctions

    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IValidators

    def get_validators(self):
        return validators.get_validators()

    # IClick

    def get_commands(self):
        return cli.get_commands()
