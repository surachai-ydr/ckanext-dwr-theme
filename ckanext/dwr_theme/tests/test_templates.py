import pytest

from ckan.tests import factories


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestTheme:
    def test_homepage(self, app):
        organization = factories.Organization(title="Water Resources")
        factories.Dataset(title="Reservoir levels", owner_org=organization["id"])

        body = app.get("/").body

        assert 'class="dwr-hero"' in body
        assert "Reservoir levels" in body
        assert "Water Resources" in body

    def test_header_and_footer_on_inner_pages(self, app):
        body = app.get("/dataset/").body

        assert 'class="dwr-header"' in body
        assert 'class="dwr-footer"' in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.primary_color", "#00796b")
    def test_primary_color_injected(self, app):
        body = app.get("/").body

        assert "--dwr-primary:#00796b" in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_title", "DWR Open Data")
    def test_hero_title_configurable(self, app):
        body = app.get("/").body

        assert "DWR Open Data" in body
