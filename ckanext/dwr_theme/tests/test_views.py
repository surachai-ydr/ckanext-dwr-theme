import pytest


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestThemeView:
    def test_get(self, app):
        resp = app.get("/dwr-theme")
        assert resp.status_code == 200
        assert "ckanext-dwr-theme demo" in resp.body

    @pytest.mark.ckan_config("WTF_CSRF_ENABLED", False)
    def test_post_greets(self, app):
        resp = app.post("/dwr-theme", data={"name": "CKAN"})
        assert resp.status_code == 200
        assert "Hello, CKAN!" in resp.body

    @pytest.mark.ckan_config("WTF_CSRF_ENABLED", False)
    def test_post_invalid_shows_error(self, app):
        resp = app.post("/dwr-theme", data={"name": "R2D2"})
        assert "Must not contain digits" in resp.body


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.usefixtures("with_plugins")
class TestPrivacyPolicy:
    def test_english(self, app):
        resp = app.get("/en/privacy-policy")
        assert resp.status_code == 200
        assert "Personal Data Protection Act" in resp.body

    def test_thai(self, app):
        resp = app.get("/th/privacy-policy")
        assert resp.status_code == 200
        assert "พระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล" in resp.body

    @pytest.mark.ckan_config("ckan.locale_default", "fr")
    def test_falls_back_to_english(self, app):
        resp = app.get("/privacy-policy")
        assert "Personal Data Protection Act" in resp.body


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.ckan_config("ckanext.dwr_theme.home_groups", "2")
@pytest.mark.ckan_config("ckanext.dwr_theme.home_organizations", "2")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestHomeCards:
    def test_groups_most_datasets_first_including_empty(self, app):
        from ckan.tests import factories

        empty = factories.Group(title="Alpha")
        busy = factories.Group(title="Zulu")
        factories.Dataset(groups=[{"id": busy["id"]}])
        factories.Group(title="Mike")

        first = app.get("/dwr-theme/home/group").json
        assert first["next_offset"] == 2
        assert first["total"] == 3
        assert first["html"].index("Zulu") < first["html"].index("Alpha")
        assert "Mike" not in first["html"]

        last = app.get("/dwr-theme/home/group?offset=2").json
        assert "Mike" in last["html"]
        assert empty["title"] not in last["html"]
        assert last["next_offset"] is None

    def test_organizations(self, app):
        from ckan.tests import factories

        factories.Organization(title="Water Resources")

        page = app.get("/dwr-theme/home/organization").json
        assert "Water Resources" in page["html"]
        assert "/organization/" in page["html"]
        assert page["next_offset"] is None

    def test_unknown_kind(self, app):
        app.get("/dwr-theme/home/dataset", status=404)

    def test_invalid_offset(self, app):
        app.get("/dwr-theme/home/group?offset=abc", status=400)
