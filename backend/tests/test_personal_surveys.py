from tests.conftest import register_and_login
from tests.test_surveys import _sample_survey_payload


def _create(client, headers, **extra):
    return client.post("/api/surveys", json={**_sample_survey_payload(), **extra}, headers=headers)


def test_enumerator_creates_personal_survey_by_default(client):
    headers = register_and_login(client, email="e1@test.local", role="ENUMERATOR", full_name="E One")
    resp = _create(client, headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["scope"] == "PERSONAL"
    assert body["created_by_id"]


def test_admin_creates_global_by_default_and_can_choose_personal(client):
    headers = register_and_login(client, email="a@test.local", role="ADMINISTRATOR")
    assert _create(client, headers).json()["scope"] == "GLOBAL"
    assert _create(client, headers, scope="PERSONAL").json()["scope"] == "PERSONAL"


def test_supervisor_cannot_create_global(client):
    headers = register_and_login(client, email="s@test.local", role="SUPERVISOR")
    assert _create(client, headers, scope="GLOBAL").status_code == 403
    assert _create(client, headers).json()["scope"] == "PERSONAL"


def test_personal_survey_is_private_to_owner(client):
    owner = register_and_login(client, email="owner@test.local", role="ENUMERATOR", full_name="Owner")
    other = register_and_login(client, email="other@test.local", role="ENUMERATOR", full_name="Other")
    admin = register_and_login(client, email="adm@test.local", role="ADMINISTRATOR")

    survey = _create(client, owner).json()

    assert [s["id"] for s in client.get("/api/surveys", headers=owner).json()] == [survey["id"]]
    assert client.get("/api/surveys", headers=other).json() == []
    assert client.get("/api/surveys", headers=admin).json() == []  # admin list hides others' personal surveys

    assert client.get(f"/api/surveys/{survey['id']}", headers=owner).status_code == 200
    assert client.get(f"/api/surveys/{survey['id']}", headers=other).status_code == 404


def test_only_owner_can_edit_publish_personal_survey(client):
    owner = register_and_login(client, email="owner2@test.local", role="ENUMERATOR", full_name="Owner")
    other = register_and_login(client, email="other2@test.local", role="ENUMERATOR", full_name="Other")
    survey = _create(client, owner).json()
    sid = survey["id"]

    assert client.put(f"/api/surveys/{sid}", json={"title": "Hacked"}, headers=other).status_code in (403, 404)
    assert client.post(f"/api/surveys/{sid}/publish", headers=other).status_code in (403, 404)

    assert client.put(f"/api/surveys/{sid}", json={"title": "Mine"}, headers=owner).json()["title"] == "Mine"
    assert client.post(f"/api/surveys/{sid}/publish", headers=owner).json()["status"] == "PUBLISHED"


def test_enumerator_cannot_edit_global_survey(client):
    admin = register_and_login(client, email="adm2@test.local", role="ADMINISTRATOR")
    enum = register_and_login(client, email="e2@test.local", role="ENUMERATOR", full_name="E Two")
    survey = _create(client, admin).json()
    assert client.put(f"/api/surveys/{survey['id']}", json={"title": "x"}, headers=enum).status_code == 403
    assert client.post(f"/api/surveys/{survey['id']}/publish", headers=enum).status_code == 403


def test_personal_survey_syncs_only_to_owner(client):
    owner = register_and_login(client, email="owner3@test.local", role="ENUMERATOR", full_name="Owner")
    other = register_and_login(client, email="other3@test.local", role="ENUMERATOR", full_name="Other")
    survey = _create(client, owner).json()
    client.post(f"/api/surveys/{survey['id']}/publish", headers=owner)

    mine = client.get("/api/sync/download", headers=owner).json()["surveys"]
    theirs = client.get("/api/sync/download", headers=other).json()["surveys"]
    assert [s["id"] for s in mine] == [survey["id"]]
    assert theirs == []


def test_global_survey_still_visible_to_enumerators(client):
    admin = register_and_login(client, email="adm3@test.local", role="ADMINISTRATOR")
    enum = register_and_login(client, email="e3@test.local", role="ENUMERATOR", full_name="E Three")
    survey = _create(client, admin).json()
    client.post(f"/api/surveys/{survey['id']}/publish", headers=admin)
    assert [s["id"] for s in client.get("/api/surveys", headers=enum).json()] == [survey["id"]]
    assert [s["id"] for s in client.get("/api/sync/download", headers=enum).json()["surveys"]] == [survey["id"]]
