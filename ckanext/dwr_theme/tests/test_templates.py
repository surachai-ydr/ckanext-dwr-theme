import base64
import datetime
import io
import re

import pytest

import ckan.lib.uploader as uploader
from ckan.tests import factories

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


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

    def test_favicon(self, app):
        assert '<link rel="shortcut icon" href="/favicon.ico">' in app.get("/").body
        assert app.get("/favicon.ico").status_code == 200

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

        assert "<h1>DWR Open Data</h1>" in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_title", "Generic title")
    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_title_en", "English title")
    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_subtitle_en", "English subtitle")
    def test_hero_texts_per_language(self, app):
        body = app.get("/").body

        assert "<h1>English title</h1>" in body
        assert "English subtitle" in body

    # Saving updates the in-memory config; these marks restore it afterwards
    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_title_en", "")
    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_subtitle_en", "")
    def test_hero_texts_editable_on_admin_config(self, app):
        sysadmin = factories.SysadminWithToken()
        headers = {"Authorization": sysadmin["token"]}

        body = app.get("/ckan-admin/config", headers=headers).body
        assert 'name="ckanext.dwr_theme.hero_title_th"' in body
        assert 'name="ckanext.dwr_theme.hero_subtitle_en"' in body

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={
                "save": "",
                "ckanext.dwr_theme.hero_title_en": "Water Data Hub",
                "ckanext.dwr_theme.hero_subtitle_en": "Open water data",
            },
        )

        body = app.get("/").body
        assert "<h1>Water Data Hub</h1>" in body
        assert "Open water data" in body

    def test_hero_logo_hidden_by_default(self, app):
        body = app.get("/").body

        assert 'class="dwr-hero__logo"' not in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_logo", "/images/dwr-logo.png")
    def test_hero_logo_configured(self, app):
        body = app.get("/").body

        assert '<img class="dwr-hero__logo" src="/images/dwr-logo.png"' in body

    def test_hero_logo_field_on_admin_config(self, app):
        sysadmin = factories.SysadminWithToken()

        body = app.get("/ckan-admin/config", headers={"Authorization": sysadmin["token"]}).body

        assert 'name="ckanext.dwr_theme.hero_logo"' in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_logo", "")
    def test_hero_logo_url_saved_on_admin_config(self, app):
        sysadmin = factories.SysadminWithToken()

        app.post(
            "/ckan-admin/config",
            headers={"Authorization": sysadmin["token"]},
            data={"save": "", "ckanext.dwr_theme.hero_logo": "https://example.com/logo.png"},
        )

        assert 'src="https://example.com/logo.png"' in app.get("/").body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_logo", "")
    def test_hero_logo_uploaded_on_admin_config(self, app, ckan_config, monkeypatch, tmpdir):
        monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmpdir))
        monkeypatch.setattr(uploader, "_storage_path", str(tmpdir))
        sysadmin = factories.SysadminWithToken()
        headers = {"Authorization": sysadmin["token"]}

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={"save": "", "hero_logo_upload": (io.BytesIO(PNG_1X1), "dwr-logo.png")},
        )

        logo = ckan_config["ckanext.dwr_theme.hero_logo"]
        assert re.match(r"^/uploads/admin/.*dwr-logo\.png$", logo)
        assert f'<img class="dwr-hero__logo" src="{logo}"' in app.get("/").body
        assert app.get(logo).status_code == 200

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={"save": "", "ckanext.dwr_theme.hero_logo": logo, "clear_hero_logo_upload": "true"},
        )
        assert 'class="dwr-hero__logo"' not in app.get("/").body

    @pytest.mark.ckan_config("ckanext.dwr_theme.hero_image", "")
    def test_hero_image_uploaded_on_admin_config(self, app, ckan_config, monkeypatch, tmpdir):
        monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmpdir))
        monkeypatch.setattr(uploader, "_storage_path", str(tmpdir))
        sysadmin = factories.SysadminWithToken()
        headers = {"Authorization": sysadmin["token"]}

        assert "--dwr-hero-image" not in app.get("/").body
        assert 'name="hero_image_upload"' in app.get("/ckan-admin/config", headers=headers).body

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={"save": "", "hero_image_upload": (io.BytesIO(PNG_1X1), "hero.png")},
        )

        image = ckan_config["ckanext.dwr_theme.hero_image"]
        assert re.match(r"^/uploads/admin/.*hero\.png$", image)
        assert f"--dwr-hero-image: url('{image}')" in app.get("/").body

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={"save": "", "ckanext.dwr_theme.hero_image": image, "clear_hero_image_upload": "true"},
        )
        assert "--dwr-hero-image" not in app.get("/").body

    @pytest.mark.ckan_config("ckan.site_title", "My Portal")
    def test_footer_defaults_to_site_title(self, app):
        body = app.get("/").body

        assert '<span class="dwr-brand__title">My Portal</span>' in body
        assert 'class="dwr-footer__logo"' not in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.footer_name_en", "Department of Water Resources")
    @pytest.mark.ckan_config("ckanext.dwr_theme.footer_logo", "/images/dwr-white.png")
    def test_footer_name_and_logo_configured(self, app):
        body = app.get("/").body

        assert '<span class="dwr-brand__title">Department of Water Resources</span>' in body
        assert f"&copy; {datetime.date.today().year} Department of Water Resources" in body
        assert '<img class="dwr-footer__logo" src="/images/dwr-white.png"' in body

    @pytest.mark.ckan_config("ckanext.dwr_theme.footer_logo", "")
    @pytest.mark.ckan_config("ckanext.dwr_theme.footer_name_en", "")
    def test_footer_editable_on_admin_config(self, app, ckan_config, monkeypatch, tmpdir):
        monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmpdir))
        monkeypatch.setattr(uploader, "_storage_path", str(tmpdir))
        sysadmin = factories.SysadminWithToken()
        headers = {"Authorization": sysadmin["token"]}

        body = app.get("/ckan-admin/config", headers=headers).body
        assert 'name="ckanext.dwr_theme.footer_name_th"' in body
        assert 'name="footer_logo_upload"' in body

        app.post(
            "/ckan-admin/config",
            headers=headers,
            data={
                "save": "",
                "ckanext.dwr_theme.footer_name_en": "DWR Footer",
                "footer_logo_upload": (io.BytesIO(PNG_1X1), "footer.png"),
            },
        )

        logo = ckan_config["ckanext.dwr_theme.footer_logo"]
        assert re.match(r"^/uploads/admin/.*footer\.png$", logo)
        body = app.get("/").body
        assert '<span class="dwr-brand__title">DWR Footer</span>' in body
        assert f'<img class="dwr-footer__logo" src="{logo}"' in body

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
