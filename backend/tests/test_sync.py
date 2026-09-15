from tests.conftest import register_and_login


def _create_and_publish_survey(client, headers):
    payload = {
        "title": "Population Survey 2026",
        "questions": [
            {"code": "full_name", "label": "Full Name", "type": "SHORT_TEXT", "order_index": 1, "is_required": True},
        ],
    }
    survey = client.post("/api/surveys", json=payload, headers=headers).json()
    return client.post(f"/api/surveys/{survey['id']}/publish", headers=headers).json()


def test_sync_download_returns_only_published_surveys(client):
    headers = register_and_login(client, email="admin@synctest.local", role="ADMINISTRATOR")

    draft_payload = {
        "title": "Draft Survey",
        "questions": [{"code": "q1", "label": "Q1", "type": "SHORT_TEXT", "order_index": 1}],
    }
    client.post("/api/surveys", json=draft_payload, headers=headers)
    published = _create_and_publish_survey(client, headers)

    resp = client.get("/api/sync/download", headers=headers)
    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()["surveys"]]
    assert "Population Survey 2026" in titles
    assert "Draft Survey" not in titles
    assert published["title"] in titles


def test_sync_upload_batch_is_partially_resilient(client):
    headers = register_and_login(client, email="admin2@synctest.local", role="ADMINISTRATOR")
    survey = _create_and_publish_survey(client, headers)
    question_id = survey["questions"][0]["id"]

    batch = {
        "device_id": "device-123",
        "submissions": [
            {
                "client_submission_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "survey_id": survey["id"],
                "survey_version_id": survey["current_version_id"],
                "answers": [{"question_id": question_id, "value_text": "Valid Name"}],
            },
            {
                "client_submission_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "survey_id": survey["id"],
                "survey_version_id": "not-a-real-version-id",
                "answers": [],
            },
        ],
    }
    resp = client.post("/api/sync/upload", json=batch, headers=headers)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 2
    assert results[0]["accepted"] is True
    assert results[1]["accepted"] is False
