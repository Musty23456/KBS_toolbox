from tests.conftest import register_and_login
from tests.test_surveys import _sample_survey_payload


def _targets(client, headers):
    return {t["email"]: t["id"] for t in client.get("/api/surveys/share-targets", headers=headers).json()}


def _setup(client):
    """Owner publishes a personal survey, shares it with friend, friend submits once."""
    owner = register_and_login(client, email="own@test.local", role="ENUMERATOR", full_name="Owner")
    friend = register_and_login(client, email="friend@test.local", role="ENUMERATOR", full_name="Friend Fatima")
    stranger = register_and_login(client, email="stranger@test.local", role="ENUMERATOR", full_name="Stranger")
    admin = register_and_login(client, email="adm@test.local", role="ADMINISTRATOR", full_name="Admin")

    survey = client.post("/api/surveys", json=_sample_survey_payload(), headers=owner).json()
    sid = survey["id"]
    client.put(f"/api/surveys/{sid}/shares", json={"user_ids": [_targets(client, owner)["friend@test.local"]]}, headers=owner)
    published = client.post(f"/api/surveys/{sid}/publish", headers=owner).json()
    qs = {q["code"]: q["id"] for q in published["questions"]}

    payload = {
        "survey_id": sid,
        "survey_version_id": published["current_version_id"],
        "client_submission_uuid": "11111111-1111-4111-8111-111111111111",
        "collected_at": "2026-09-29T10:00:00Z",
        "answers": [
            {"question_id": qs["full_name"], "value_text": "Ada Lovelace"},
            {"question_id": qs["age_years"], "value_text": "30"},
            {"question_id": qs["gender"], "value_text": "FEMALE"},
        ],
    }
    resp = client.post("/api/submissions", json=payload, headers=friend)
    assert resp.status_code == 201
    return owner, friend, stranger, admin, sid, resp.json()["id"]


def test_owner_sees_submissions_from_people_it_was_shared_with(client):
    owner, friend, stranger, admin, sid, sub_id = _setup(client)

    rows = client.get("/api/submissions", params={"survey_id": sid}, headers=owner)
    assert rows.status_code == 200
    body = rows.json()
    assert [r["id"] for r in body] == [sub_id]
    assert body[0]["submitted_by_name"] == "Friend Fatima"

    # The recipient and an outsider do not get the owner's results list
    assert client.get("/api/submissions", headers=friend).json() == []
    assert client.get("/api/submissions", headers=stranger).json() == []
    # Staff behaviour is unchanged
    assert [r["id"] for r in client.get("/api/submissions", headers=admin).json()] == [sub_id]


def test_owner_can_open_single_submission_but_outsider_cannot(client):
    owner, friend, stranger, _admin, _sid, sub_id = _setup(client)
    assert client.get(f"/api/submissions/{sub_id}", headers=owner).status_code == 200
    assert client.get(f"/api/submissions/{sub_id}", headers=friend).status_code == 200  # their own
    assert client.get(f"/api/submissions/{sub_id}", headers=stranger).status_code == 403


def test_owner_analytics_overview_and_questions(client):
    owner, _friend, stranger, admin, sid, _sub = _setup(client)

    overview = client.get("/api/analytics/overview", params={"survey_id": sid}, headers=owner)
    assert overview.status_code == 200
    data = overview.json()
    assert data["total_submissions"] == 1
    assert data["unique_enumerators"] == 1
    assert [e["name"] for e in data["enumerator_performance"]] == ["Friend Fatima"]
    assert [s["survey_id"] for s in data["survey_comparison"]] == [sid]  # only their own survey

    questions = client.get("/api/analytics/questions", params={"survey_id": sid}, headers=owner)
    assert questions.status_code == 200
    assert any(q["code"] == "gender" and q["response_count"] == 1 for q in questions.json())

    assert client.get("/api/analytics/overview", params={"survey_id": sid}, headers=admin).status_code == 200
    # Not the owner, or no survey chosen -> refused
    assert client.get("/api/analytics/overview", params={"survey_id": sid}, headers=stranger).status_code == 403
    assert client.get("/api/analytics/overview", headers=owner).status_code == 403


def test_enumerator_cannot_analyse_global_survey(client):
    admin = register_and_login(client, email="adm2@test.local", role="ADMINISTRATOR", full_name="Admin")
    enum = register_and_login(client, email="e@test.local", role="ENUMERATOR", full_name="Enum")
    global_survey = client.post("/api/surveys", json=_sample_survey_payload(), headers=admin).json()
    assert client.get("/api/analytics/overview", params={"survey_id": global_survey["id"]}, headers=enum).status_code == 403
    assert client.get("/api/analytics/questions", params={"survey_id": global_survey["id"]}, headers=enum).status_code == 403


def test_owner_can_export_own_survey_only(client):
    owner, _friend, stranger, _admin, sid, _sub = _setup(client)
    ok = client.get("/api/exports/csv", params={"survey_id": sid}, headers=owner)
    assert ok.status_code == 200
    assert "Ada Lovelace" in ok.text
    assert client.get("/api/exports/csv", headers=owner).status_code == 403
    assert client.get("/api/exports/csv", params={"survey_id": sid}, headers=stranger).status_code == 403
