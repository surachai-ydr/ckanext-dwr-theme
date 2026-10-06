import pytest

import ckan.plugins.toolkit as tk
from ckan.tests.helpers import call_action


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
class TestThemeHello:
    def test_greets_name(self):
        result = call_action("dwr_theme_hello", name="CKAN")
        assert result == {"message": "Hello, CKAN!"}

    def test_name_required(self):
        with pytest.raises(tk.ValidationError) as e:
            call_action("dwr_theme_hello")
        assert "name" in e.value.error_dict

    def test_name_with_digits_rejected(self):
        with pytest.raises(tk.ValidationError) as e:
            call_action("dwr_theme_hello", name="R2D2")
        assert e.value.error_dict["name"] == ["Must not contain digits"]
