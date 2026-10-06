import pytest

import ckan.plugins.toolkit as tk

from ckanext.dwr_theme.logic import validators


def test_no_digits_accepts_text():
    assert validators.dwr_theme_no_digits("CKAN") == "CKAN"


def test_no_digits_rejects_digits():
    with pytest.raises(tk.Invalid):
        validators.dwr_theme_no_digits("abc123")
