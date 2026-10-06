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
