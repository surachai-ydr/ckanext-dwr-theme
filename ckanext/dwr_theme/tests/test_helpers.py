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
