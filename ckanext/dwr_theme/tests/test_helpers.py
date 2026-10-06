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
