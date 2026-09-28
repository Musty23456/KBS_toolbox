from tests.conftest import register_and_login
from tests.test_surveys import _sample_survey_payload


def _user_id(client, headers):
    return client.get("/api/auth/me", headers=headers).json()["id"]


def _setup(client):
    owner = register_and_login(client, email="own@test.local", role="ENUMERATOR", full_name="Owner")
    friend = register_and_login(client, email="friend@test.local", role="ENUMERATOR", full_name="Friend")
    stranger = register_and_login(client, email="stranger@test.local", role="ENUMERATOR", full_name="Stranger")
    survey = client.post("/api/surveys", json=_sample_survey_payload(), headers=owner).json()
    return owner, friend, stranger, survey


def _targets(client, headers):
    return {t["email"]: t["id"] for t in client.get("/api/surveys/share-targets", headers=headers).json()}


def test_share_targets_exclude_self_and_non_enumerators(client):
    owner, friend, _stranger, _s = _setup(client)
    register_and_login(client, email="adm@test.local", role="ADMINISTRATOR", full_name="Admin")
    targets = _targets(client, owner)
    assert "own@test.local" not in targets
    assert "adm@test.local" not in targets
    assert {"friend@test.local", "stranger@test.local"} <= set(targets)


def test_owner_shares_published_survey_and_friend_can_see_it(client):
    owner, friend, stranger, survey = _setup(client)
    sid = survey["id"]
    fid = _targets(client, owner)["friend@test.local"]

    r = client.put(f"/api/surveys/{sid}/shares", json={"user_ids": [fid]}, headers=owner)
    assert r.status_code == 200 and r.json()["user_ids"] == [fid]

    # Not published yet -> recipient sees nothing
    assert client.get("/api/surveys", headers=friend).json() == []
    assert client.get(f"/api/surveys/{sid}", headers=friend).status_code == 404

    client.post(f"/api/surveys/{sid}/publish", headers=owner)
    assert [s["id"] for s in client.get("/api/surveys", headers=friend).json()] == [sid]
    assert client.get(f"/api/surveys/{sid}", headers=friend).status_code == 200
    assert [s["id"] for s in client.get("/api/sync/download", headers=friend).json()["surveys"]] == [sid]

    # Someone it was not shared with still cannot see it
    assert client.get("/api/surveys", headers=stranger).json() == []
    assert client.get(f"/api/surveys/{sid}", headers=stranger).status_code == 404


def test_recipient_is_fill_only(client):
    owner, friend, _stranger, survey = _setup(client)
    sid = survey["id"]
    fid = _targets(client, owner)["friend@test.local"]
    client.put(f"/api/surveys/{sid}/shares", json={"user_ids": [fid]}, headers=owner)
    client.post(f"/api/surveys/{sid}/publish", headers=owner)

    assert client.put(f"/api/surveys/{sid}", json={"title": "x"}, headers=friend).status_code == 403
    assert client.post(f"/api/surveys/{sid}/unpublish", headers=friend).status_code == 403
    assert client.delete(f"/api/surveys/{sid}", headers=friend).status_code == 403
    assert client.get(f"/api/surveys/{sid}/shares", headers=friend).status_code == 403
    assert client.put(f"/api/surveys/{sid}/shares", json={"user_ids": []}, headers=friend).status_code == 403


def test_recipient_can_submit_and_stranger_cannot(client):
    owner, friend, stranger, survey = _setup(client)
    sid = survey["id"]
    fid = _targets(client, owner)["friend@test.local"]
    client.put(f"/api/surveys/{sid}/shares", json={"user_ids": [fid]}, headers=owner)
    published = client.post(f"/api/surveys/{sid}/publish", headers=owner).json()
    qs = {q["code"]: q["id"] for q in published["questions"]}

    def payload(uuid):
        return {
            "survey_id": sid,
            "survey_version_id": published["current_version_id"],
            "client_submission_uuid": uuid,
            "collected_at": "2026-09-29T10:00:00Z",
            "answers": [
                {"question_id": qs["full_name"], "value_text": "Ada Lovelace"},
                {"question_id": qs["age_years"], "value_text": "30"},
                {"question_id": qs["gender"], "value_text": "FEMALE"},
            ],
        }

    assert client.post("/api/submissions", json=payload("11111111-1111-4111-8111-111111111111"), headers=friend).status_code == 201
    assert client.post("/api/submissions", json=payload("22222222-2222-4222-8222-222222222222"), headers=stranger).status_code == 403


def test_unshare_removes_access(client):
    owner, friend, _stranger, survey = _setup(client)
    sid = survey["id"]
    fid = _targets(client, owner)["friend@test.local"]
    client.put(f"/api/surveys/{sid}/shares", json={"user_ids": [fid]}, headers=owner)
    client.post(f"/api/surveys/{sid}/publish", headers=owner)
    assert len(client.get("/api/surveys", headers=friend).json()) == 1

    client.put(f"/api/surveys/{sid}/shares", json={"user_ids": []}, headers=owner)
    assert client.get("/api/surveys", headers=friend).json() == []
    assert client.get("/api/sync/download", headers=friend).json()["surveys"] == []


def test_cannot_share_global_survey_or_with_non_enumerator(client):
    admin = register_and_login(client, email="adm2@test.local", role="ADMINISTRATOR", full_name="Admin")
    owner, _friend, _stranger, survey = _setup(client)
    global_survey = client.post("/api/surveys", json=_sample_survey_payload(), headers=admin).json()
    assert client.put(f"/api/surveys/{global_survey['id']}/shares", json={"user_ids": []}, headers=admin).status_code == 403

    admin_id = client.get("/api/auth/me", headers=admin).json()["id"]
    r = client.put(f"/api/surveys/{survey['id']}/shares", json={"user_ids": [admin_id]}, headers=owner)
    assert r.status_code == 400
