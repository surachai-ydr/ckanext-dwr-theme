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


@pytest.mark.ckan_config("ckan.plugins", "dwr-theme")
@pytest.mark.ckan_config("WTF_CSRF_ENABLED", False)
@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestUserAdmin:
    url = "/ckan-admin/users/"

    def _as(self, user):
        return {"Authorization": user["token"]}

    def test_needs_sysadmin(self, app):
        from ckan.tests import factories

        user = factories.UserWithToken()
        assert app.get(self.url, headers=self._as(user), status=403)
        assert app.get(self.url, status=403)

    def test_lists_users(self, app):
        from ckan.tests import factories

        sysadmin = factories.SysadminWithToken()
        user = factories.User(fullname="Somchai Test")
        resp = app.get(self.url, headers=self._as(sysadmin))
        assert "Somchai Test" in resp.body
        assert user["email"] in resp.body

    def test_create_with_organization_role(self, app):
        from ckan import model
        from ckan.tests import factories

        sysadmin = factories.SysadminWithToken()
        org = factories.Organization()
        app.post(self.url + "new", headers=self._as(sysadmin), data={
            "name": "newuser", "email": "new@example.com", "password": "pass12345678",
            "organization": org["id"], "role": "editor",
        })
        from ckan.tests.helpers import call_action

        assert model.User.get("newuser") is not None
        orgs = call_action("organization_list_for_user", id="newuser", permission="manage_group")
        assert [o["id"] for o in orgs] == []  # editor, not admin
        orgs = call_action("organization_list_for_user", id="newuser", permission="create_dataset")
        assert [o["id"] for o in orgs] == [org["id"]]

    def test_toggle_sysadmin(self, app):
        from ckan import model
        from ckan.tests import factories

        sysadmin = factories.SysadminWithToken()
        user = factories.User()
        app.post(f"{self.url}{user['id']}/sysadmin", headers=self._as(sysadmin), data={"sysadmin": "true"})
        assert model.User.get(user["id"]).sysadmin
        app.post(f"{self.url}{user['id']}/sysadmin", headers=self._as(sysadmin), data={"sysadmin": "false"})
        assert not model.User.get(user["id"]).sysadmin

    def test_cannot_demote_or_delete_self(self, app):
        from ckan import model
        from ckan.tests import factories

        sysadmin = factories.SysadminWithToken()
        app.post(f"{self.url}{sysadmin['id']}/sysadmin", headers=self._as(sysadmin), data={"sysadmin": "false"})
        app.post(f"{self.url}{sysadmin['id']}/delete", headers=self._as(sysadmin))
        user = model.User.get(sysadmin["id"])
        assert user.sysadmin and user.state == "active"

    def test_delete_and_reactivate(self, app):
        from ckan import model
        from ckan.tests import factories

        sysadmin = factories.SysadminWithToken()
        user = factories.User()
        app.post(f"{self.url}{user['id']}/delete", headers=self._as(sysadmin))
        assert model.User.get(user["id"]).state == "deleted"
        app.post(f"{self.url}{user['id']}/reactivate", headers=self._as(sysadmin))
        assert model.User.get(user["id"]).state == "active"

    def test_change_and_remove_role(self, app):
        from ckan.tests import factories
        from ckan.tests.helpers import call_action

        sysadmin = factories.SysadminWithToken()
        user = factories.User()
        org = factories.Organization()
        post = lambda role: app.post(f"{self.url}{user['id']}/membership", headers=self._as(sysadmin),
                                     data={"organization": org["id"], "role": role})

        def roles():
            members = call_action("member_list", id=org["id"], object_type="user")
            return [role.lower() for member_id, _type, role in members if member_id == user["id"]]

        post("admin")
        assert roles() == ["admin"]
        post("")
        assert roles() == []
