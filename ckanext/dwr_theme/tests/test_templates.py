import re

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

    def test_font_size_control(self, app):
        body = app.get("/").body

        assert 'data-module="dwr-theme-font-size"' in body
        assert 'data-dwr-font-size' in body

    def test_footer_links_privacy_policy(self, app):
        body = app.get("/").body

        assert 'href="/privacy-policy"' in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.privacy_policy_url", "https://example.com/privacy")
    def test_footer_privacy_policy_url_configurable(self, app):
        body = app.get("/").body

        assert 'href="https://example.com/privacy"' in body

    def test_home_modal_off_by_default(self, app):
        body = app.get("/").body

        assert "dwr-theme-home-modal" not in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal", "true")
    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_title", "Maintenance notice")
    @pytest.mark.ckan_config("ckanext.dwr_theme.home_modal_text", "Down **Sunday**")
    def test_home_modal_enabled(self, app):
        body = app.get("/").body

        assert 'data-module="dwr-theme-home-modal"' in body
        assert "Maintenance notice" in body
        assert "<strong>Sunday</strong>" in body

    def test_search_sidebar_facets(self, app):
        factories.Dataset(resources=[
            {"url": "http://example.com/a.csv", "format": "CSV"},
            {"url": "http://example.com/b.json", "format": "JSON"},
        ])

        body = app.get("/dataset/", query_string={"res_format": "CSV"}).body

        assert body.count('<details class="dwr-facet" open>') == 1  # only Formats, which has a selection
        assert 'class="dwr-facet__active" title="Selected">1<' in body
        assert re.search(r'class="dwr-facet__link is-active"[^>]*title="CSV"', body)
        assert 'title="JSON"' in body

    @pytest.mark.ckan_config("ckan.datasets_per_page", 2)
    def test_search_pagination(self, app):
        for _ in range(3):
            factories.Dataset()

        body = app.get("/dataset/").body

        assert 'class="pagination-wrapper"' in body
        assert 'href="/dataset/?page=2"' in body
