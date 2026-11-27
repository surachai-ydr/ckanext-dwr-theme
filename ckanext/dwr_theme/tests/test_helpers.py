import pytest

from ckanext.dwr_theme import helpers


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
def test_greeting_default():
    assert helpers.dwr_theme_greeting() == "Hello"


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.ckan_config("ckanext.dwr_theme.greeting", "Sawasdee")
@pytest.mark.usefixtures("with_plugins")
def test_greeting_configured():
    assert helpers.dwr_theme_greeting() == "Sawasdee"


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
class TestPrimaryColor:
    def test_default(self):
        assert helpers.dwr_theme_primary_color() == helpers.DEFAULT_PRIMARY_COLOR

    @pytest.mark.ckan_config("ckanext.dwr_theme.primary_color", "#00796B")
    def test_configured(self):
        assert helpers.dwr_theme_primary_color() == "#00796b"

    @pytest.mark.ckan_config("ckanext.dwr_theme.primary_color", "red;}</style><script>")
    def test_invalid_value_falls_back_to_default(self):
        assert helpers.dwr_theme_primary_color() == helpers.DEFAULT_PRIMARY_COLOR


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
class TestFavicon:
    def test_default_replaces_ckan_icon(self):
        assert helpers.dwr_theme_favicon() == helpers.DEFAULT_FAVICON

    @pytest.mark.ckan_config("ckan.favicon", "/images/custom.ico")
    def test_configured(self):
        assert helpers.dwr_theme_favicon() == "/images/custom.ico"


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.ckan_config("ckanext.dwr_theme.primary_color", "#fff")
@pytest.mark.usefixtures("with_plugins")
def test_palette_derives_shades():
    palette = helpers.dwr_theme_palette()
    assert palette == {"primary": "#fff", "dark": "#bfbfbf", "soft": "#ffffff"}


@pytest.mark.parametrize("name, initials", [
    ("Water Resources", "WR"),
    ("dwr", "D"),
    ("Department of Water Resources", "DO"),
    ("", "?"),
])
def test_initials(name, initials):
    assert helpers.dwr_theme_initials(name) == initials


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
class TestHomeModal:
    def test_disabled_by_default(self):
        assert helpers.dwr_theme_home_modal() is None

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal", "true")
    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_title", "Notice")
    def test_enabled(self):
        modal = helpers.dwr_theme_home_modal()
        assert modal["title"] == "Notice"
        assert modal["text"] == ""
        assert len(modal["key"]) == 12

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal", "true")
    def test_key_changes_with_content(self, ckan_config, monkeypatch):
        before = helpers.dwr_theme_home_modal()["key"]
        monkeypatch.setitem(ckan_config, "ckanext.dwr_theme.home_modal_text", "New")
        assert helpers.dwr_theme_home_modal()["key"] != before

    def _gdc_popup(self, monkeypatch, conf):
        import ckan.plugins.toolkit as tk

        monkeypatch.setattr(helpers, "dwr_theme_gdc_enabled", lambda: True)
        monkeypatch.setitem(tk.h, "thai_gdc_get_conf_group", lambda group: conf)

    def test_gdc_popup(self, monkeypatch):
        self._gdc_popup(monkeypatch, {
            "EVENT_PUBLIC": "True",
            "EVENT_IMAGE": "/uploads/admin/event.png",
            "EVENT_URL": "https://example.com",
            "EVENT_TEXT": "More",
        })
        modal = helpers.dwr_theme_home_modal()
        assert modal["images"] == ["/uploads/admin/event.png"]
        assert modal["link_url"] == "https://example.com"
        assert modal["link_text"] == "More"
        assert modal["no_text"]
        assert "image_only" not in modal

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_image_only", "true")
    def test_gdc_popup_image_only(self, monkeypatch):
        self._gdc_popup(monkeypatch, {"EVENT_PUBLIC": "True", "EVENT_IMAGE": "/x.png"})
        assert helpers.dwr_theme_home_modal()["image_only"]

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal", "true")
    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_image_only", "true")
    def test_image_only_needs_an_image(self):
        assert "image_only" not in helpers.dwr_theme_home_modal()

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal", "true")
    def test_unpublished_gdc_popup_falls_back_to_config(self, monkeypatch):
        self._gdc_popup(monkeypatch, {"EVENT_PUBLIC": "False", "EVENT_IMAGE": "/x.png"})
        modal = helpers.dwr_theme_home_modal()
        assert modal["images"] == []
        assert "image_only" not in modal

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_images", "/b.png\n/a.png\n/b.png")
    def test_extra_images_follow_the_main_one(self, monkeypatch):
        self._gdc_popup(monkeypatch, {"EVENT_PUBLIC": "True", "EVENT_IMAGE": "/a.png"})
        assert helpers.dwr_theme_home_modal()["images"] == ["/a.png", "/b.png"]

    def test_key_changes_with_images(self, ckan_config, monkeypatch):
        self._gdc_popup(monkeypatch, {"EVENT_PUBLIC": "True", "EVENT_IMAGE": "/a.png"})
        before = helpers.dwr_theme_home_modal()["key"]
        monkeypatch.setitem(ckan_config, "ckanext.dwr_theme.home_modal_images", "/b.png")
        assert helpers.dwr_theme_home_modal()["key"] != before


def test_version_matches_installed_package():
    from importlib import metadata

    assert helpers.dwr_theme_version() == metadata.version("ckanext-dwr-theme")


@pytest.mark.parametrize("text, expected", [
    ("20 พฤศจิกายน ค.ศ. 2026", "20 พฤศจิกายน พ.ศ. 2569"),
    ("พฤศจิกายน 20, 2026, 14:05 (UTC)", "พฤศจิกายน 20, 2569, 14:05 (UTC)"),
])
def test_to_buddhist_era(text, expected):
    assert helpers.to_buddhist_era(text) == expected



@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins", "with_request_context")
class TestAdminNav:
    def _nav(self, ckan_config, monkeypatch):
        monkeypatch.setitem(ckan_config, "ckan.admin_tabs", {
            "admin.trash": {"label": "Trash", "icon": "trash"},
            "admin.config": {"label": "Config", "icon": None},
        })
        return helpers.build_extra_admin_nav()

    def test_shows_tabs(self, ckan_config, monkeypatch):
        nav = self._nav(ckan_config, monkeypatch)
        assert "/ckan-admin/trash" in nav
        assert "/ckan-admin/config" in nav

    @pytest.mark.ckan_config("ckanext.dwr_theme.hidden_admin_tabs", "admin.trash")
    def test_hides_listed_tabs(self, ckan_config, monkeypatch):
        nav = self._nav(ckan_config, monkeypatch)
        assert "/ckan-admin/trash" not in nav
        assert "/ckan-admin/config" in nav
