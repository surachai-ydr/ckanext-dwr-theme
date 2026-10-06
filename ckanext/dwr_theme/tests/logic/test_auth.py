import pytest

from ckan import model
from ckan.tests.helpers import call_auth


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
def test_theme_hello_anonymous_allowed():
    context = {"user": "", "model": model}
    assert call_auth("dwr_theme_hello", context=context)
