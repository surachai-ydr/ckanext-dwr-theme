import pytest

from ckanext.dwr_theme.cli import dwr_theme


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
def test_hello(cli):
    result = cli.invoke(dwr_theme, ["hello", "CKAN"])
    assert result.exit_code == 0, result.output
    assert "Hello, CKAN!" in result.output
